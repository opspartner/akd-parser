# akd-parser

CLI-Tool zur automatischen Extraktion von AKD-Daten aus PDF-Formularen mittels Vision-LLM.

## Hintergrund

Wechselt ein Unternehmen den Krankentaggeld- oder Unfallversicherer, liefert der bisherige Versicherer eine **Vorversicherer-Auskunft** mit Vertrags-, Deckungs-, Lohnsummen- und Schadendaten. Der neue Versicherer benoetigt diese Daten fuer die Risikoeinschaetzung und Offertstellung.

Seit November 2024 gibt es dafuer ein einheitliches Format: den **Auskunftsdienst (AKD)**, definiert im [SVV-Handbuch V1.0](https://svv.ch/sites/default/files/media/documents/2024-11/241009_SVV_AKD_Handbuch_V1.0.pdf). Das Format wurde von einer Arbeitsgruppe des SVV unter Mitwirkung von Allianz Suisse, Baloise, Generali, Groupe Mutuel, Helsana, Helvetia, Mobiliar, SWICA, Zurich, AXA und Visana erarbeitet. Es deckt die drei Branchen **KTG**, **UVG** und **UVG-Z** ab und basiert auf dem [Freizuegigkeitsabkommen unter den Krankentaggeld-Versicherern](https://svv.ch/de/fachdokumente/regelwerk/freizuegigkeitsabkommen-der-kollektiv-krankentaggeldversicherung) (FZA KTG) vom 1. Januar 2006 bzw. Art. 68 UVG.

Die Umsetzung ist **freiwillig** -- die teilnehmenden Gesellschaften streben eine Einfuehrung **bis 1. Januar 2028** an. Ziel ist, dass empfangende Gesellschaften die **Daten maschinell in ihre Risikosysteme einlesen** koennen, um darauf basierend Offerten zu erstellen.

### Das Problem

In der Praxis liegen Vorversicherer-Auskuenfte haeufig als **PDF** vor -- jeder Versicherer mit eigenem Layout. Der manuelle Aufwand fuer die Uebertragung in die Risikosysteme ist hoch, die Fehleranfaelligkeit ebenfalls. Selbst mit dem neuen AKD-Standard muessen Versicherer weiterhin ein lesefreundliches PDF-Dokument mitliefern. Bei historischen Auskuenften oder Gesellschaften die das CSV-Format noch nicht liefern, bleibt das PDF die einzige Datenquelle.

## Was macht akd-parser?

`akd-parser` schliesst diese Luecke: **PDF rein, AKD-CSV raus.**

1. **PDF zu Bildern** -- Jede Seite wird in ein optimiertes JPEG konvertiert.
2. **Vision-LLM Extraktion** -- Die Bilder werden an ein lokales oder gehostetes Vision-LLM gesendet. Das Modell extrahiert alle AKD-relevanten Daten. Der Output wird ueber `response_format` mit JSON-Schema auf Token-Ebene erzwungen -- das LLM kann nur schema-konformes JSON generieren.
3. **AKD-CSV Ausgabe** -- Das JSON wird in eine spezifikationskonforme CSV-Datei serialisiert: Semikolon-getrennt, ISO 8859-1, alle Recordarten in einer Datei, auf 42 Spalten aufgefuellt.

### Die 5 AKD-Recordarten

| Record | Inhalt |
|--------|--------|
| **10 -- Police** | Vertrags- und Kundendaten (Policennr., Adresse, Kuendigung, ...) |
| **20 -- Kreis** | Personenkreise und Deckungen (Taggeld, Wartefristen, Kapitalleistungen, ...) |
| **30 -- Lohnsummen** | Versicherte Lohnsummen pro Kreis und Jahr |
| **40 -- Schaden** | Aggregierte Schadenanzahlen, Zahlungen und Rueckstellungen pro Jahr |
| **50 -- Langzeit-Schaeden** | Einzelne KTG-Langzeitfaelle (pendent, erledigt, ausgesteuert) |

## Voraussetzungen

- Python 3.12+
- Ein **Vision-LLM** mit OpenAI-kompatiblem Chat-Completions-Endpoint (`/v1/chat/completions`). Getestet mit:
  - [llama.cpp](https://github.com/ggml-org/llama.cpp) + Qwen 3.6 35B
  - Jeder Endpunkt der `response_format` mit `type: json_schema` und Vision (Bild-Input) unterstuetzt

## Installation

```bash
git clone https://github.com/opspartner/akd-parser.git
cd akd-parser
uv sync
```

## Konfiguration

Erstelle eine `.env`-Datei im Projektverzeichnis (oder uebergib die Werte als CLI-Flags):

```bash
cp .env.example .env
```

```env
# OpenAI-kompatibler Endpoint mit Vision-Support
OPENAI_BASE_URL=http://localhost:30001/v1
OPENAI_MODEL=qwen3.6-35b
OPENAI_API_KEY=local

# Optional: Sampling-Temperatur (Standard: 0.7)
# ACHTUNG: 0.0 verursacht bei Qwen 3 Endlosschleifen
# OPENAI_TEMPERATURE=0.7
```

## Verwendung

```bash
# Einzelne PDF-Datei verarbeiten
akd-parser auskunft.pdf

# Alle PDFs im aktuellen Verzeichnis
akd-parser

# Alle PDFs in einem Ordner, Ausgabe in anderes Verzeichnis
akd-parser /pfad/zu/pdfs -o /pfad/zu/output

# JSON statt CSV
akd-parser auskunft.pdf -f json

# Verbose: LLM-Output live streamen
akd-parser auskunft.pdf -v

# Bereits verarbeitete Dateien ueberschreiben
akd-parser auskunft.pdf --overwrite
```

### Ausgabe

```
akd-parser  ·  qwen3.6-35b @ http://localhost:30001/v1
1 PDF(s) from /home/user/auskuenfte  →  /home/user/auskuenfte  [csv]

● auskunft.pdf  3 pages · 2.9 MB
  ✓ 53.8s  ·  1xR10 2xR20 2xR30
  → /home/user/auskuenfte/auskunft.csv

Done  ·  1 processed  ·  53.8s
```

### CLI-Optionen

| Option | Beschreibung |
|--------|-------------|
| `--output-dir`, `-o` | Ausgabeordner (Standard: aktuelles Verzeichnis) |
| `--base-url` | OpenAI-kompatibler Endpoint (oder `OPENAI_BASE_URL`) |
| `--model`, `-m` | Modellname (oder `OPENAI_MODEL`) |
| `--api-key` | API-Key (oder `OPENAI_API_KEY`, Standard: `local`) |
| `--temperature`, `-t` | Sampling-Temperatur (oder `OPENAI_TEMPERATURE`, Standard: `0.7`) |
| `--format`, `-f` | Ausgabeformat: `csv` (Standard) oder `json` |
| `--dpi` | DPI fuer PDF-zu-Bild-Konvertierung (Standard: `200`) |
| `--max-pages` | Max. Seiten pro PDF |
| `--max-image-size` | Max. Pixel auf langer Kante (Standard: `3072`) |
| `--max-tokens` | Max. Output-Tokens des LLM (Standard: `16384`) |
| `--thinking` / `--no-thinking` | Extended Thinking ein/aus, fuer Qwen 3 (Standard: aus) |
| `--overwrite` | Bereits existierende Ausgaben ueberschreiben |
| `--verbose`, `-v` | LLM-Reasoning und -Output live auf stderr streamen |

## AKD-CSV Format

Die erzeugte CSV-Datei entspricht der Spezifikation aus dem SVV-Handbuch (Kap. 1.3):

- **Trennzeichen:** Semikolon (`;`)
- **Zeichensatz:** ISO 8859-1
- **Struktur:** Alle 5 Recordarten in einer Datei, jeder Record eine Zeile
- **Spaltenanzahl:** Jede Zeile auf 42 Spalten aufgefuellt (laengster Record = Recordart 20)
- **Keine Kopfzeile**
- **Leere Felder** erscheinen als `;;` (nicht ausgelassen)

## Architektur

```
PDF  ──►  pdf.py (PyMuPDF)  ──►  JPEG-Bilder
                                      │
                                      ▼
                               extractor.py (OpenAI API)
                               - Vision-LLM mit Bildern
                               - response_format: json_schema (strict)
                               - Streaming mit Token-Callback
                                      │
                                      ▼
                                schema.py (Pydantic v2)
                                - 5 Recordart-Modelle
                                - JSON-Schema-Generierung (strict-kompatibel)
                                - CSV-Serialisierung (to_akd_csv)
                                      │
                                      ▼
                                  cli.py (Typer)
                                  - .env laden
                                  - Fortschrittsanzeige
                                  - CSV/JSON schreiben
```

## Haftungsausschluss

Dieses Tool wird ohne jegliche Gewaehrleistung bereitgestellt. Die extrahierten Daten sind abhaengig von der Qualitaet des eingesetzten LLM und der Lesbarkeit der PDF-Vorlagen. **Die Ausgaben muessen vor der Weiterverwendung geprueft werden.** Die Autoren uebernehmen keinerlei Haftung fuer Schaeden, die aus der Nutzung dieses Tools oder der erzeugten Daten entstehen.

## Lizenz

[MIT](LICENSE)
