# ruff: noqa: E501
from __future__ import annotations

import json
from typing import Annotated, ClassVar, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Bool01 = Literal[0, 1]
DateCH = Annotated[
    str,
    Field(
        pattern=r"^\d{2}\.\d{2}\.\d{4}$",
        description="Datum im AKD-Format 'dd.mm.yyyy'.",
        examples=["22.10.2024"],
    ),
]

UnterbrancheCode = Literal[420, 360, 380]
SpracheCode = Literal["D", "F", "I"]
UnfallartCode = Literal[1, 2, 3]
LangzeitStatus = Literal[0, 1, 2, 3]
ProgressionCode = Literal[100, 225, 350]
InvaliditaetsLeistungsart = Literal[1, 2]
SpitalklasseCode = Literal[1, 2]


class AkdBaseModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )


class AkdPoliceRecord10(AkdBaseModel):
    recordart: Literal[10] = Field(10, alias="RECORDART", description="Recordart 10, Konstante.")
    ges_nr: int = Field(
        alias="GES_NR",
        description="Gesellschaftsnummer des Vorversicherers gemäss Mitversicherungs-Austausch.",
    )
    unterbranche_cd: UnterbrancheCode = Field(
        alias="UNTERBRANCHE_CD", description="Unterbranche: 420=KTG, 360=UVG-Z, 380=UVG/OUFL."
    )
    police_nr: str = Field(
        alias="POLICE_NR", description="Policennummer; zentrale ID zur Verknüpfung der Records."
    )
    vnbez: str = Field(alias="VNBEZ", description="Versicherungsnehmer-Bezeichnung / Kundenname.")
    strasse: str = Field(alias="STRASSE", description="Adresse Versicherungsnehmer: Strasse.")
    hausnr: str = Field(alias="HAUSNR", description="Adresse Versicherungsnehmer: Hausnummer.")
    plz: int = Field(alias="PLZ", description="Adresse Versicherungsnehmer: Postleitzahl.")
    ort: str = Field(alias="ORT", description="Adresse Versicherungsnehmer: Ort.")
    beginn: DateCH = Field(
        alias="BEGINN", description="Ursprünglicher Beginn der Versicherung / früheste Police."
    )
    ende: DateCH = Field(alias="ENDE", description="Nächstmöglicher Kündigungstermin der Police.")
    risikonr: str | None = Field(
        default=None,
        alias="RISIKONR",
        description="Risikonummer gemäss Risikoklassifizierung UVG, Format etwa 'iiii.jj'. Bei KTG optional.",
    )
    betrart_text: str | None = Field(
        default=None,
        alias="BETRART_TEXT",
        description="Betriebsart in Textform gemäss Risikoklassifizierung UVG; bei KTG optional.",
    )
    sprach_cd: SpracheCode = Field(
        alias="SPRACH_CD", description="Korrespondenzsprache / Sprache der Auskunft: D, F oder I."
    )
    sicht_dt: DateCH = Field(
        alias="SICHT_DT", description="Sichtdatum / Daten- und Abwicklungsstand der Auskunft."
    )
    kz_ereig_finanz: Bool01 = Field(
        alias="KZ_EREIG_FINANZ", description="1=Ereignissicht, 0=Finanzsicht."
    )
    kz_obl: Bool01 | None = Field(
        default=None,
        alias="KZ_OBL",
        description="Nur UVG: 1=obligatorische Versicherung vorhanden, 0=nein; sonst leer/null.",
    )
    kz_frw: Bool01 | None = Field(
        default=None,
        alias="KZ_FRW",
        description="Nur UVG: 1=freiwillige Versicherung vorhanden, 0=nein; sonst leer/null.",
    )
    ls_frw: int | None = Field(
        default=None,
        alias="LS_FRW",
        description="Nur UVG: versicherte Lohnsumme bei freiwilliger Versicherung; sonst leer/null.",
    )
    gekuendigt: Bool01 = Field(
        alias="GEKUENDIGT", description="1=Vertrag gekündigt, 0=nicht gekündigt."
    )
    gekuendigt_dt: DateCH | None = Field(
        default=None,
        alias="GEKUENDIGT_DT",
        description="Falls gekündigt: Wirkungsdatum der Kündigung; sonst leer/null.",
    )
    gekuendigt_durchwen: Bool01 | None = Field(
        default=None,
        alias="GEKUENDIGT_DURCHWEN",
        description="Falls gekündigt: 1=Kunde, 0=Versicherer; sonst leer/null.",
    )
    verstoss_as: Bool01 | None = Field(
        default=None,
        alias="VERSTOSS_AS",
        description="Nur UVG: 1=Höherstufung wegen Arbeitssicherheitsverstössen, 0=nein; sonst leer/null.",
    )
    organ: str | None = Field(
        default=None,
        alias="ORGAN",
        description="Nur UVG bei VERSTOSS_AS=1: zuständiges Durchführungsorgan; sonst leer/null.",
    )
    version: str = Field(
        default="1.0",
        alias="VERSION",
        description="Versions-ID des verwendeten Auskunftsformats, z. B. '1.0'.",
    )

    @field_validator("version", mode="before")
    @classmethod
    def _coerce_version(cls, v: object) -> str:
        if v is None:
            return "1.0"
        return str(v)

    csv_columns: ClassVar[list[str]] = [
        "RECORDART",
        "GES_NR",
        "UNTERBRANCHE_CD",
        "POLICE_NR",
        "VNBEZ",
        "STRASSE",
        "HAUSNR",
        "PLZ",
        "ORT",
        "BEGINN",
        "ENDE",
        "RISIKONR",
        "BETRART_TEXT",
        "SPRACH_CD",
        "SICHT_DT",
        "KZ_EREIG_FINANZ",
        "KZ_OBL",
        "KZ_FRW",
        "LS_FRW",
        "GEKUENDIGT",
        "GEKUENDIGT_DT",
        "GEKUENDIGT_DURCHWEN",
        "VERSTOSS_AS",
        "ORGAN",
        "VERSION",
    ]



class AkdKreisRecord20(AkdBaseModel):
    recordart: Literal[20] = Field(20, alias="RECORDART", description="Recordart 20, Konstante.")
    police_nr: str = Field(
        alias="POLICE_NR", description="Policennummer zur Verknüpfung mit Recordart 10."
    )
    krs_lfnr: int = Field(
        alias="KRS_LFNR",
        ge=1,
        description="Laufnummer des Deckungskreises; innerhalb der Auskunft eindeutig.",
    )
    kreisart_cd: Bool01 = Field(
        alias="KREISART_CD", description="1=Einzelperson, 0=Personengruppe."
    )
    kreis_txt: str = Field(
        alias="KREIS_TXT", description="Bezeichnung des Personenkreises, ohne Personendaten."
    )
    jahr_max: int = Field(
        alias="JAHR_MAX",
        description="Letztes Jahr, in dem der Deckungskreis unter der Police versichert war.",
    )
    sum_sch: Bool01 | None = Field(
        default=None,
        alias="SUM_SCH",
        description="KTG: 1=Schadenversicherung, 0=Summenversicherung.",
    )
    frw_obl: Bool01 | None = Field(
        default=None, alias="FRW_OBL", description="UVG: 1=freiwillig, 0=obligatorisch."
    )
    ktg_deckungsart: Bool01 | None = Field(
        default=None,
        alias="KTG_DECKUNGSART",
        description="KTG: 1=Volldeckung, 0=Koordinationsdeckung.",
    )
    tg_fl: Bool01 | None = Field(
        default=None,
        alias="TG_FL",
        description="KTG / UVG-Z-bis Taggeld: 1=versichert, 0=nicht versichert.",
    )
    tg_ld: int | None = Field(
        default=None,
        alias="TG_LD",
        description="KTG: maximale Leistungsdauer in Anzahl Taggeldern, typischerweise 720 oder 730.",
    )
    tg1_lh: int | None = Field(
        default=None,
        alias="TG1_LH",
        description="KTG / UVG-Z-bis Taggeld: Leistungshöhe 1. Taggeld in Prozent, ganzzahlig.",
    )
    tg1_wfr: int | None = Field(
        default=None,
        alias="TG1_WFR",
        description="KTG / UVG-Z-bis Taggeld: Wartefrist 1. Taggeld in Tagen.",
    )
    tg2_lh: int | None = Field(
        default=None,
        alias="TG2_LH",
        description="Leistungshöhe 2. Taggeld in Prozent; leer/null falls nicht versichert.",
    )
    tg2_wfr: int | None = Field(
        default=None,
        alias="TG2_WFR",
        description="Wartefrist 2. Taggeld in Tagen; leer/null falls nicht versichert.",
    )
    tg3_lh: int | None = Field(
        default=None,
        alias="TG3_LH",
        description="Leistungshöhe 3. Taggeld in Prozent; leer/null falls nicht versichert.",
    )
    tg3_wfr: int | None = Field(
        default=None,
        alias="TG3_WFR",
        description="Wartefrist 3. Taggeld in Tagen; leer/null falls nicht versichert.",
    )
    tg_12tag_fl: Bool01 | None = Field(
        default=None,
        alias="TG_12TAG_FL",
        description="UVG-Z: Taggeld 1+2 Tag, 1=versichert, 0=nicht versichert.",
    )
    tg_12tag_lh: int | None = Field(
        default=None,
        alias="TG_12TAG_LH",
        description="UVG-Z: Leistungshöhe Taggeld 1+2 Tag in Prozent.",
    )
    tgu_fl: Bool01 | None = Field(
        default=None,
        alias="TGU_FL",
        description="UVG-Z-über Taggeld: 1=versichert, 0=nicht versichert.",
    )
    tgu1_lh: int | None = Field(
        default=None, alias="TGU1_LH", description="UVG-Z-über Taggeld: Leistungshöhe 1 in Prozent."
    )
    tgu1_wfr: int | None = Field(
        default=None, alias="TGU1_WFR", description="UVG-Z-über Taggeld: Wartefrist 1 in Tagen."
    )
    tgu2_lh: int | None = Field(
        default=None, alias="TGU2_LH", description="UVG-Z-über Taggeld: Leistungshöhe 2 in Prozent."
    )
    tgu2_wfr: int | None = Field(
        default=None, alias="TGU2_WFR", description="UVG-Z-über Taggeld: Wartefrist 2 in Tagen."
    )
    tgu3_lh: int | None = Field(
        default=None, alias="TGU3_LH", description="UVG-Z-über Taggeld: Leistungshöhe 3 in Prozent."
    )
    tgu3_wfr: int | None = Field(
        default=None, alias="TGU3_WFR", description="UVG-Z-über Taggeld: Wartefrist 3 in Tagen."
    )
    iru_fl: Bool01 | None = Field(
        default=None,
        alias="IRU_FL",
        description="UVG-Z-über Invaliditätsrente: 1=versichert, 0=nicht versichert.",
    )
    inv_fl: Bool01 | None = Field(
        default=None,
        alias="INV_FL",
        description="UVG-Z-bis Invaliditätskapital: 1=versichert, 0=nicht versichert.",
    )
    inv_la: InvaliditaetsLeistungsart | None = Field(
        default=None,
        alias="INV_LA",
        description="UVG-Z-bis Invaliditätskapital Leistungsart: 1=als Faktor, 2=in CHF.",
    )
    inv_lh: float | None = Field(
        default=None,
        alias="INV_LH",
        description="UVG-Z-bis Invaliditätskapital Leistungshöhe: Faktor oder CHF-Betrag.",
    )
    inv_pv: ProgressionCode | None = Field(
        default=None,
        alias="INV_PV",
        description="UVG-Z-bis Invaliditätskapital Progression: 100, 225 oder 350.",
    )
    ivu_fl: Bool01 | None = Field(
        default=None,
        alias="IVU_FL",
        description="UVG-Z-über Invaliditätskapital: 1=versichert, 0=nicht versichert.",
    )
    ivu_lh: float | None = Field(
        default=None,
        alias="IVU_LH",
        description="UVG-Z-über Invaliditätskapital Leistungshöhe als Faktor.",
    )
    ivu_pv: ProgressionCode | None = Field(
        default=None,
        alias="IVU_PV",
        description="UVG-Z-über Invaliditätskapital Progression: 100, 225 oder 350.",
    )
    hru_fl: Bool01 | None = Field(
        default=None,
        alias="HRU_FL",
        description="UVG-Z-über Hinterlassenenrente: 1=versichert, 0=nicht versichert.",
    )
    tod_fl: Bool01 | None = Field(
        default=None,
        alias="TOD_FL",
        description="UVG-Z-bis Todesfallkapital: 1=versichert, 0=nicht versichert.",
    )
    tod_lh: float | None = Field(
        default=None,
        alias="TOD_LH",
        description="UVG-Z-bis Todesfallkapital Leistungshöhe als Faktor des Jahreslohns.",
    )
    tdu_fl: Bool01 | None = Field(
        default=None,
        alias="TDU_FL",
        description="UVG-Z-über Todesfallkapital: 1=versichert, 0=nicht versichert.",
    )
    tdu_lh: float | None = Field(
        default=None,
        alias="TDU_LH",
        description="UVG-Z-über Todesfallkapital Leistungshöhe als Faktor des Jahreslohns.",
    )
    hk_fl: Bool01 | None = Field(
        default=None,
        alias="HK_FL",
        description="UVG-Z Heilungskosten: 1=versichert, 0=nicht versichert.",
    )
    hk_kl: SpitalklasseCode | None = Field(
        default=None,
        alias="HK_KL",
        description="UVG-Z Heilungskosten Spitalklasse: 1=privat/1. Klasse, 2=halbprivat/2. Klasse.",
    )
    diff_fl: Bool01 | None = Field(
        default=None,
        alias="DIFF_FL",
        description="UVG-Z Differenzdeckung: 1=versichert, 0=nicht versichert.",
    )

    csv_columns: ClassVar[list[str]] = [
        "RECORDART",
        "POLICE_NR",
        "KRS_LFNR",
        "KREISART_CD",
        "KREIS_TXT",
        "JAHR_MAX",
        "SUM_SCH",
        "FRW_OBL",
        "KTG_DECKUNGSART",
        "TG_FL",
        "TG_LD",
        "TG1_LH",
        "TG1_WFR",
        "TG2_LH",
        "TG2_WFR",
        "TG3_LH",
        "TG3_WFR",
        "TG_12TAG_FL",
        "TG_12TAG_LH",
        "TGU_FL",
        "TGU1_LH",
        "TGU1_WFR",
        "TGU2_LH",
        "TGU2_WFR",
        "TGU3_LH",
        "TGU3_WFR",
        "IRU_FL",
        "INV_FL",
        "INV_LA",
        "INV_LH",
        "INV_PV",
        "IVU_FL",
        "IVU_LH",
        "IVU_PV",
        "HRU_FL",
        "TOD_FL",
        "TOD_LH",
        "TDU_FL",
        "TDU_LH",
        "HK_FL",
        "HK_KL",
        "DIFF_FL",
    ]


class AkdLohnsummenRecord30(AkdBaseModel):
    recordart: Literal[30] = Field(30, alias="RECORDART", description="Recordart 30, Konstante.")
    police_nr: str = Field(
        alias="POLICE_NR", description="Policennummer zur Verknüpfung mit Recordart 10."
    )
    krs_lfnr: int = Field(
        alias="KRS_LFNR",
        ge=1,
        description="Laufnummer des Deckungskreises zur Verknüpfung mit Recordart 20.",
    )
    jahr: int = Field(alias="JAHR", description="Kalenderjahr der Deckungs-Gültigkeit.")
    ls_m: int | None = Field(
        default=None, alias="LS_M", description="KTG: Lohnsumme Männer, ganze CHF."
    )
    ls_f: int | None = Field(
        default=None, alias="LS_F", description="KTG: Lohnsumme Frauen, ganze CHF."
    )
    ls_tot: int | None = Field(
        default=None,
        alias="LS_TOT",
        description="KTG optional: Gesamtlohnsumme, falls keine Geschlechteraufteilung vorliegt.",
    )
    ls_bis: int | None = Field(
        default=None, alias="LS_BIS", description="UVG-Z: Lohnsumme bis UVG-Maximum, ganze CHF."
    )
    ls_ueb: int | None = Field(
        default=None, alias="LS_UEB", description="UVG-Z: Lohnsumme über UVG-Maximum, ganze CHF."
    )
    ls_bu_m: int | None = Field(
        default=None, alias="LS_BU_M", description="UVG: BU-Lohnsumme Männer, ganze CHF."
    )
    ls_bu_f: int | None = Field(
        default=None, alias="LS_BU_F", description="UVG: BU-Lohnsumme Frauen, ganze CHF."
    )
    ls_bu: int | None = Field(
        default=None, alias="LS_BU", description="UVG: Gesamtlohnsumme BU, ganze CHF."
    )
    ls_nbu_m: int | None = Field(
        default=None, alias="LS_NBU_M", description="UVG: NBU-Lohnsumme Männer, ganze CHF."
    )
    ls_nbu_f: int | None = Field(
        default=None, alias="LS_NBU_F", description="UVG: NBU-Lohnsumme Frauen, ganze CHF."
    )
    ls_nbu: int | None = Field(
        default=None, alias="LS_NBU", description="UVG: Gesamtlohnsumme NBU, ganze CHF."
    )

    csv_columns: ClassVar[list[str]] = [
        "RECORDART",
        "POLICE_NR",
        "KRS_LFNR",
        "JAHR",
        "LS_M",
        "LS_F",
        "LS_TOT",
        "LS_BIS",
        "LS_UEB",
        "LS_BU_M",
        "LS_BU_F",
        "LS_BU",
        "LS_NBU_M",
        "LS_NBU_F",
        "LS_NBU",
    ]


class AkdSchadenRecord40(AkdBaseModel):
    recordart: Literal[40] = Field(40, alias="RECORDART", description="Recordart 40, Konstante.")
    police_nr: str = Field(
        alias="POLICE_NR", description="Policennummer zur Verknüpfung mit Recordart 10."
    )
    jahr: int = Field(
        alias="JAHR", description="Bei Ereignissicht Ereignisjahr, bei Finanzsicht Zahlungsjahr."
    )
    unfallart: UnfallartCode | None = Field(
        default=None,
        alias="UNFALLART",
        description="Nur UVG: 1=BU, 2=NBU, 3=Freiwillig; sonst leer/null.",
    )
    anz_alle: int = Field(
        alias="ANZ_ALLE", description="Anzahl Schäden total im betreffenden Jahr zum Sichtdatum."
    )
    anz_pendent: int = Field(
        alias="ANZ_PENDENT",
        description="Anzahl offener Schäden im betreffenden Jahr zum Sichtdatum.",
    )
    zahlung_hk: int | None = Field(
        default=None,
        alias="ZAHLUNG_HK",
        description="Nur UVG: Zahlungen Heilungskosten, ganze CHF.",
    )
    zahlung_tg: int | None = Field(
        default=None, alias="ZAHLUNG_TG", description="Nur UVG: Zahlungen Taggeld, ganze CHF."
    )
    zahlung_tot: int | None = Field(
        default=None,
        alias="ZAHLUNG_TOT",
        description="KTG/UVG-Z: Zahlung total inkl. fallbezogener Kosten, ganze CHF.",
    )
    rueckstellung: int | None = Field(
        default=None,
        alias="RUECKSTELLUNG",
        description="KTG/UVG-Z: kumulierte Fallreserven, ganze CHF.",
    )

    csv_columns: ClassVar[list[str]] = [
        "RECORDART",
        "POLICE_NR",
        "JAHR",
        "UNFALLART",
        "ANZ_ALLE",
        "ANZ_PENDENT",
        "ZAHLUNG_HK",
        "ZAHLUNG_TG",
        "ZAHLUNG_TOT",
        "RUECKSTELLUNG",
    ]


class AkdLangzeitSchadenRecord50(AkdBaseModel):
    recordart: Literal[50] = Field(50, alias="RECORDART", description="Recordart 50, Konstante.")
    police_nr: str = Field(
        alias="POLICE_NR", description="Policennummer zur Verknüpfung mit Recordart 10."
    )
    id: int | None = Field(
        default=None,
        alias="ID",
        ge=1,
        description="Laufnummer des Schadens, chronologisch nach Ereignisdatum; bei STATUS=0 leer/null.",
    )
    ereignis_dt: DateCH | None = Field(
        default=None,
        alias="EREIGNIS_DT",
        description="Ereignisdatum des Schadens; bei STATUS=0 leer/null.",
    )
    status: LangzeitStatus = Field(
        alias="STATUS",
        description="1=pendent/offen, 2=erledigt, 3=max. Leistungsdauer erreicht, 0=keine Langzeit-Schäden vorhanden.",
    )
    zahlung_tot: int | None = Field(
        default=None,
        alias="ZAHLUNG_TOT",
        description="Summe geleisteter Taggelder und fallbezogener Kosten, ganze CHF; bei STATUS=0 leer/null.",
    )
    rueck_total_betr: int | None = Field(
        default=None,
        alias="RUECK_TOTAL_BETR",
        description="Offene Fallreserven, ganze CHF; bei geschlossenen Fällen 0; bei STATUS=0 leer/null.",
    )

    csv_columns: ClassVar[list[str]] = [
        "RECORDART",
        "POLICE_NR",
        "ID",
        "EREIGNIS_DT",
        "STATUS",
        "ZAHLUNG_TOT",
        "RUECK_TOTAL_BETR",
    ]



class AkdStructuredOutput(AkdBaseModel):
    recordart_10_police: list[AkdPoliceRecord10] = Field(
        default_factory=list, description="Alle Recordart-10-Police-Records."
    )
    recordart_20_kreis: list[AkdKreisRecord20] = Field(
        default_factory=list, description="Alle Recordart-20-Kreis-Records."
    )
    recordart_30_lohnsummen: list[AkdLohnsummenRecord30] = Field(
        default_factory=list, description="Alle Recordart-30-Lohnsummen-Records."
    )
    recordart_40_schaden: list[AkdSchadenRecord40] = Field(
        default_factory=list, description="Alle Recordart-40-Schaden-Records."
    )
    recordart_50_langzeit_schaeden: list[AkdLangzeitSchadenRecord50] = Field(
        default_factory=list, description="Alle Recordart-50-Langzeit-Schaden-Records; nur KTG."
    )

    _MAX_CSV_COLUMNS: ClassVar[int] = max(
        len(AkdPoliceRecord10.csv_columns),
        len(AkdKreisRecord20.csv_columns),
        len(AkdLohnsummenRecord30.csv_columns),
        len(AkdSchadenRecord40.csv_columns),
        len(AkdLangzeitSchadenRecord50.csv_columns),
    )

    def to_akd_csv(self, *, encoding: str = "iso-8859-1") -> bytes:
        lines: list[str] = []
        record_lists: list[
            list[AkdPoliceRecord10]
            | list[AkdKreisRecord20]
            | list[AkdLohnsummenRecord30]
            | list[AkdSchadenRecord40]
            | list[AkdLangzeitSchadenRecord50]
        ] = [
            self.recordart_10_police,
            self.recordart_20_kreis,
            self.recordart_30_lohnsummen,
            self.recordart_40_schaden,
            self.recordart_50_langzeit_schaeden,
        ]
        for record_list in record_lists:
            for record in record_list:
                cols = record.csv_columns
                data = record.model_dump(by_alias=True)
                values = [_csv_value(data.get(col)) for col in cols]
                values.extend("" for _ in range(self._MAX_CSV_COLUMNS - len(values)))
                lines.append(";".join(values))
        if lines:
            lines.append("")
        return "\n".join(lines).encode(encoding)


def _csv_value(v: object) -> str:
    if v is None:
        return ""
    if isinstance(v, float):
        if v == int(v):
            return str(int(v))
        return str(v)
    return str(v)


_PROGRAMMATIC_FIELDS = {"VERSION"}


def _make_strict(schema: dict[str, object]) -> None:
    """Make a JSON Schema strict-compatible: all properties required, no defaults."""
    props = schema.get("properties", {})
    if props:
        schema["required"] = [k for k in props if k not in _PROGRAMMATIC_FIELDS]
        schema.setdefault("additionalProperties", False)
        for prop_def in props.values():
            prop_def.pop("default", None)  # type: ignore[union-attr]


def akd_json_schema() -> dict[str, object]:
    schema = AkdStructuredOutput.model_json_schema(by_alias=True)
    for def_schema in schema.get("$defs", {}).values():  # type: ignore[union-attr]
        props = def_schema.get("properties", {})
        for field_name in _PROGRAMMATIC_FIELDS:
            props.pop(field_name, None)
        _make_strict(def_schema)
    _make_strict(schema)
    return schema


def write_json_schema(path: str = "akd_structured_output.schema.json") -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(akd_json_schema(), f, ensure_ascii=False, indent=2)
        f.write("\n")


if __name__ == "__main__":
    write_json_schema()
