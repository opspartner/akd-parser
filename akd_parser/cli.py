from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
import time
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Annotated, Any, Literal

import typer

from akd_parser.extractor import StreamEvent, VisionExtractor, build_system_prompt
from akd_parser.pdf import load_images
from akd_parser.schema import AkdStructuredOutput, akd_json_schema

OutputFormat = Literal["json", "csv"]

logger = logging.getLogger(__name__)

_IS_TTY = sys.stderr.isatty()
_DIM = "\033[2m" if _IS_TTY else ""
_RESET = "\033[0m" if _IS_TTY else ""
_BOLD = "\033[1m" if _IS_TTY else ""
_GREEN = "\033[32m" if _IS_TTY else ""
_YELLOW = "\033[33m" if _IS_TTY else ""
_RED = "\033[31m" if _IS_TTY else ""
_CLEAR_LINE = "\r\033[K" if _IS_TTY else "\n"

_RECORD_SHORT = {
    "recordart_10_police": "R10",
    "recordart_20_kreis": "R20",
    "recordart_30_lohnsummen": "R30",
    "recordart_40_schaden": "R40",
    "recordart_50_langzeit_schaeden": "R50",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _find_project_root() -> Path:
    current = Path.cwd().resolve()
    for path in (current, *current.parents):
        if (path / "pyproject.toml").is_file():
            return path
    return current


def _load_dotenv() -> None:
    env_path = _find_project_root() / ".env"
    if not env_path.is_file():
        return
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())


def _configure_logging(*, verbose: bool) -> None:
    for name in ("openai", "httpx", "httpcore"):
        logging.getLogger(name).setLevel(logging.DEBUG if verbose else logging.WARNING)
    pkg = logging.getLogger("akd_parser")
    pkg.handlers.clear()
    pkg.propagate = False
    pkg.setLevel(logging.DEBUG if verbose else logging.WARNING)
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("%(message)s"))
    pkg.addHandler(handler)


def _format_duration(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes, remainder = divmod(seconds, 60)
    return f"{int(minutes)}m {remainder:.0f}s"


def _fmt_chars(n: int) -> str:
    if n >= 1000:
        return f"{n / 1000:.1f}k"
    return str(n)


def _format_size(n_bytes: int) -> str:
    if n_bytes < 1024:
        return f"{n_bytes} B"
    if n_bytes < 1024 * 1024:
        return f"{n_bytes / 1024:.0f} KB"
    return f"{n_bytes / (1024 * 1024):.1f} MB"


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2))


def _discover_pdfs(input_dir: Path) -> list[Path]:
    return sorted({p.resolve() for p in input_dir.iterdir() if p.suffix.lower() == ".pdf"})


def _format_record_counts(raw: dict[str, object]) -> str:
    parts: list[str] = []
    for key, short in _RECORD_SHORT.items():
        val = raw.get(key)
        if isinstance(val, list) and len(val) > 0:
            parts.append(f"{len(val)}x{short}")
    return " ".join(parts) if parts else "no records"


def _stderr(msg: str = "", end: str = "\n") -> None:
    sys.stderr.write(msg + end)
    sys.stderr.flush()


# ---------------------------------------------------------------------------
# Live progress display
# ---------------------------------------------------------------------------


class _StreamProgress:
    def __init__(self, *, verbose: bool):
        self.verbose = verbose
        self._started = time.perf_counter()
        self._reasoning_chars = 0
        self._content_chars = 0
        self._last_render = 0.0
        self._in_reasoning = False

    def on_token(self, event: StreamEvent) -> None:
        if event.kind == "reasoning":
            self._reasoning_chars += len(event.text)
            if self.verbose:
                if not self._in_reasoning:
                    self._in_reasoning = True
                    _stderr(f"\n{_DIM}", end="")
                sys.stderr.write(event.text)
                sys.stderr.flush()
        else:
            self._content_chars += len(event.text)
            if self.verbose:
                if self._in_reasoning:
                    self._in_reasoning = False
                    _stderr(f"{_RESET}\n")
                sys.stderr.write(event.text)
                sys.stderr.flush()

        if not self.verbose:
            now = time.perf_counter()
            if now - self._last_render >= 0.25:
                self._last_render = now
                self._render_status()

    def _render_status(self) -> None:
        elapsed = _format_duration(time.perf_counter() - self._started)
        parts = [elapsed]
        if self._reasoning_chars:
            parts.append(f"thinking {_fmt_chars(self._reasoning_chars)} chars")
        if self._content_chars:
            parts.append(f"output {_fmt_chars(self._content_chars)} chars")
        sys.stderr.write(f"{_CLEAR_LINE}  {_DIM}{'  ·  '.join(parts)}{_RESET}")
        sys.stderr.flush()

    def finish(self) -> None:
        if self.verbose:
            if self._in_reasoning:
                _stderr(_RESET)
            _stderr()
        elif _IS_TTY:
            sys.stderr.write(_CLEAR_LINE)
            sys.stderr.flush()


# ---------------------------------------------------------------------------
# Processing
# ---------------------------------------------------------------------------


@dataclass
class _Result:
    source: str
    output: Path | None = None
    pages: int | None = None
    img_size: int | None = None
    duration: float | None = None
    error: str | None = None
    skipped: bool = False
    record_counts: str = ""


async def _process_pdf(
    source_path: Path,
    output_dir: Path,
    *,
    extractor: VisionExtractor,
    dpi: int,
    max_pages: int | None,
    max_long_edge: int,
    overwrite: bool,
    output_format: OutputFormat = "csv",
    verbose: bool = False,
) -> _Result:
    source_path = source_path.resolve()
    stem = source_path.stem
    ext = "csv" if output_format == "csv" else "json"
    output_path = output_dir / f"{stem}.{ext}"

    if output_path.exists() and not overwrite:
        return _Result(source=source_path.name, output=output_path, skipped=True)

    started = time.perf_counter()

    try:
        images = load_images(source_path, dpi=dpi, max_pages=max_pages, max_long_edge=max_long_edge)
        img_size = sum(len(img) for img in images)
        _stderr(
            f"{_BOLD}●{_RESET} {source_path.name}"
            f"  {_DIM}{len(images)} pages · {_format_size(img_size)}{_RESET}"
        )

        progress = _StreamProgress(verbose=verbose)
        raw_json = await extractor.extract(images, on_token=progress.on_token)
        progress.finish()

        counts_str = _format_record_counts(raw_json)
        validated = AkdStructuredOutput.model_validate(raw_json)

        if output_format == "csv":
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(validated.to_akd_csv())
        else:
            _write_json(output_path, validated.model_dump(by_alias=True))

        elapsed = time.perf_counter() - started
        _stderr(f"  {_GREEN}✓{_RESET} {_format_duration(elapsed)}  ·  {counts_str}")
        _stderr(f"  → {output_path}")

        return _Result(
            source=source_path.name,
            output=output_path,
            pages=len(images),
            img_size=img_size,
            duration=elapsed,
            record_counts=counts_str,
        )

    except Exception as exc:
        elapsed = time.perf_counter() - started
        _stderr(f"  {_RED}✗{_RESET} {_format_duration(elapsed)}  ·  {exc}")
        logger.debug("%s: %s", source_path.name, traceback.format_exc())
        _write_json(
            output_dir / f"{stem}.error.json",
            {
                "source_file": source_path.name,
                "error": str(exc),
                "traceback": traceback.format_exc(),
            },
        )
        return _Result(
            source=source_path.name,
            error=str(exc),
            duration=elapsed,
        )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

app = typer.Typer(invoke_without_command=True, no_args_is_help=True, add_completion=False)


@app.command()
def main(
    input_path: Annotated[
        Path | None,
        typer.Argument(help="PDF file or folder with PDFs (default: current directory)"),
    ] = None,
    output_dir: Annotated[
        Path | None,
        typer.Option("--output-dir", "-o", help="Output folder (default: cwd)"),
    ] = None,
    base_url: Annotated[
        str | None,
        typer.Option("--base-url", help="OpenAI-compatible chat completions base URL"),
    ] = None,
    model: Annotated[
        str | None,
        typer.Option("--model", "-m", help="Model name"),
    ] = None,
    api_key: Annotated[
        str | None,
        typer.Option("--api-key", help="API key"),
    ] = None,
    temperature: Annotated[
        float | None,
        typer.Option("--temperature", "-t", help="Sampling temperature (default: 0.7)"),
    ] = None,
    dpi: Annotated[
        int,
        typer.Option("--dpi", help="DPI for PDF-to-image conversion"),
    ] = 200,
    max_pages: Annotated[
        int | None,
        typer.Option("--max-pages", help="Limit pages per PDF"),
    ] = None,
    max_image_size: Annotated[
        int,
        typer.Option("--max-image-size", help="Max pixel on long edge"),
    ] = 3072,
    max_tokens: Annotated[
        int,
        typer.Option("--max-tokens", help="Max output tokens for LLM response"),
    ] = 16384,
    thinking: Annotated[
        bool,
        typer.Option("--thinking/--no-thinking", help="Enable extended thinking (Qwen 3)"),
    ] = False,
    format: Annotated[
        OutputFormat,
        typer.Option("--format", "-f", help="Output format: csv (AKD) or json"),
    ] = "csv",
    overwrite: Annotated[
        bool,
        typer.Option("--overwrite", help="Reprocess even if output exists"),
    ] = False,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Stream LLM reasoning and output"),
    ] = False,
) -> None:
    """Extract AKD data from PDF(s) using a vision LLM."""
    _load_dotenv()
    _configure_logging(verbose=verbose)

    resolved_input = (input_path or Path.cwd()).resolve()
    resolved_output = (output_dir or Path.cwd()).resolve()
    resolved_output.mkdir(parents=True, exist_ok=True)

    if resolved_input.is_file():
        pdf_files = [resolved_input]
    elif resolved_input.is_dir():
        pdf_files = _discover_pdfs(resolved_input)
    else:
        _stderr(f"{_RED}Error:{_RESET} {resolved_input} is not a file or directory")
        raise typer.Exit(code=1)

    if not pdf_files:
        _stderr(f"{_RED}Error:{_RESET} No PDFs found in {resolved_input}")
        raise typer.Exit(code=1)

    resolved_base_url = base_url or os.environ.get("OPENAI_BASE_URL")
    resolved_model = model or os.environ.get("OPENAI_MODEL")
    resolved_api_key = api_key or os.environ.get("OPENAI_API_KEY", "local")

    if not resolved_base_url:
        _stderr(f"{_RED}Error:{_RESET} --base-url or OPENAI_BASE_URL is required")
        raise typer.Exit(code=1)
    if not resolved_model:
        _stderr(f"{_RED}Error:{_RESET} --model or OPENAI_MODEL is required")
        raise typer.Exit(code=1)

    resolved_temperature = temperature
    if resolved_temperature is None:
        env_temp = os.environ.get("OPENAI_TEMPERATURE")
        resolved_temperature = float(env_temp) if env_temp else 0.7

    schema = akd_json_schema()
    extractor = VisionExtractor(
        base_url=resolved_base_url,
        model=resolved_model,
        system_prompt=build_system_prompt(schema),
        json_schema=schema,
        api_key=resolved_api_key,
        temperature=resolved_temperature,
        max_tokens=max_tokens,
        enable_thinking=thinking,
    )

    _stderr(f"{_BOLD}akd-parser{_RESET}  ·  {resolved_model} @ {resolved_base_url}")
    _stderr(
        f"{_DIM}{len(pdf_files)} PDF(s) from {resolved_input}"
        f"  →  {resolved_output}  [{format}]{_RESET}"
    )
    _stderr()

    async def run() -> list[_Result]:
        results: list[_Result] = []
        for i, pdf_path in enumerate(pdf_files):
            if i > 0:
                _stderr()
            results.append(
                await _process_pdf(
                    pdf_path,
                    resolved_output,
                    extractor=extractor,
                    dpi=dpi,
                    max_pages=max_pages,
                    max_long_edge=max_image_size,
                    overwrite=overwrite,
                    output_format=format,
                    verbose=verbose,
                )
            )
        return results

    started = time.perf_counter()
    results = asyncio.run(run())
    elapsed = time.perf_counter() - started

    processed = sum(1 for r in results if r.error is None and not r.skipped)
    skipped = sum(1 for r in results if r.skipped)
    failed = sum(1 for r in results if r.error is not None)

    _stderr()
    parts = []
    if processed:
        parts.append(f"{_GREEN}{processed} processed{_RESET}")
    if skipped:
        parts.append(f"{skipped} skipped")
    if failed:
        parts.append(f"{_RED}{failed} failed{_RESET}")
    _stderr(f"{_BOLD}Done{_RESET}  ·  {'  ·  '.join(parts)}  ·  {_format_duration(elapsed)}")

    if failed:
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
