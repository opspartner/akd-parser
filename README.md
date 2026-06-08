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

## Datenfelder pro Recordart

Referenz aller extrahierten Felder gemaess [schema.py](akd_parser/schema.py). Konventionen:

- **0/1** = AKD-Boolean (nicht `true`/`false`).
- **Datum** = String im Format `dd.mm.yyyy`; gaengige Eingabeformate (ISO `yyyy-mm-dd`, `dd/mm/yyyy`) werden automatisch normalisiert.
- **Branche** in eckigen Klammern: `[KTG]`, `[UVG]`, `[UVG-Z]` markiert Felder, die nur fuer die jeweilige Branche befuellt werden; ohne Klammer gilt das Feld branchenuebergreifend.
- Bis auf `RECORDART` und `POLICE_NR` darf jedes Feld `null` sein, wenn der Wert im Formular nicht sichtbar oder nicht anwendbar ist (leeres CSV-Feld). `POLICE_NR` ist die zentrale Verknuepfungs-ID und immer gesetzt.

### Recordart 10 -- Police

Ein Record pro Police mit Vertrags- und Kundendaten.

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `RECORDART` | 10 | Konstante. |
| `GES_NR` | int | Gesellschaftsnummer des Vorversicherers gem. Mitversicherungs-Austausch. |
| `UNTERBRANCHE_CD` | 420 / 360 / 380 | Unterbranche: 420=KTG, 360=UVG-Z, 380=UVG/OUFL. |
| `POLICE_NR` | str | Policennummer; zentrale ID zur Verknuepfung aller Records. |
| `VNBEZ` | str | Versicherungsnehmer-Bezeichnung / Kundenname. |
| `STRASSE` | str | Adresse: Strasse. |
| `HAUSNR` | str | Adresse: Hausnummer. |
| `PLZ` | int | Adresse: Postleitzahl. |
| `ORT` | str | Adresse: Ort. |
| `BEGINN` | Datum | Urspruenglicher Beginn der Versicherung / frueheste Police. |
| `ENDE` | Datum | Naechstmoeglicher Kuendigungstermin der Police. |
| `RISIKONR` | str | [UVG] Risikonummer gem. Risikoklassifizierung, Format `iiii.jj`; bei KTG optional. |
| `BETRART_TEXT` | str | [UVG] Betriebsart in Textform; bei KTG optional. |
| `SPRACH_CD` | D / F / I | Korrespondenzsprache der Auskunft. |
| `SICHT_DT` | Datum | Sichtdatum / Daten- und Abwicklungsstand der Auskunft. |
| `KZ_EREIG_FINANZ` | 0/1 | 1=Ereignissicht, 0=Finanzsicht (steuert die Bedeutung von `JAHR` in R40). |
| `KZ_OBL` | 0/1 | [UVG] 1=obligatorische Versicherung vorhanden, 0=nein. |
| `KZ_FRW` | 0/1 | [UVG] 1=freiwillige Versicherung vorhanden, 0=nein. |
| `LS_FRW` | int | [UVG] Versicherte Lohnsumme bei freiwilliger Versicherung. |
| `GEKUENDIGT` | 0/1 | 1=Vertrag gekuendigt, 0=nicht gekuendigt. |
| `GEKUENDIGT_DT` | Datum | Wirkungsdatum der Kuendigung (falls gekuendigt). |
| `GEKUENDIGT_DURCHWEN` | 0/1 | Kuendigung durch: 1=Kunde, 0=Versicherer. |
| `VERSTOSS_AS` | 0/1 | [UVG] 1=Hoeherstufung wegen Arbeitssicherheitsverstoessen, 0=nein. |
| `ORGAN` | str | [UVG] Bei `VERSTOSS_AS`=1: zustaendiges Durchfuehrungsorgan. |
| `VERSION` | str | Versions-ID des Auskunftsformats (programmatisch gesetzt, z.B. `1.0`). |

### Recordart 20 -- Kreis

Ein Record pro Police und Deckungskreis (Personenkreis + Deckungen). Verknuepfung ueber `POLICE_NR` + `KRS_LFNR`.

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `RECORDART` | 20 | Konstante. |
| `POLICE_NR` | str | Verknuepfung zu Recordart 10. |
| `KRS_LFNR` | int | Laufnummer des Deckungskreises; innerhalb der Auskunft eindeutig. |
| `KREISART_CD` | 0/1 | 1=Einzelperson, 0=Personengruppe. |
| `KREIS_TXT` | str | Bezeichnung des Personenkreises, ohne Personendaten. |
| `JAHR_MAX` | int | Letztes Jahr, in dem der Deckungskreis versichert war. |
| `SUM_SCH` | 0/1 | [KTG] 1=Schadenversicherung, 0=Summenversicherung. |
| `FRW_OBL` | 0/1 | [UVG] 1=freiwillig, 0=obligatorisch. |
| `KTG_DECKUNGSART` | 0/1 | [KTG] 1=Volldeckung, 0=Koordinationsdeckung. |
| `TG_FL` | 0/1 | [KTG/UVG-Z] Taggeld: 1=versichert, 0=nicht versichert. |
| `TG_LD` | int | [KTG] Max. Leistungsdauer in Taggeldern (typ. 720 oder 730). |
| `TG1_LH` / `TG1_WFR` | int | 1. Taggeld: Leistungshoehe in % / Wartefrist in Tagen. |
| `TG2_LH` / `TG2_WFR` | int | 2. Taggeld: Leistungshoehe % / Wartefrist Tage. |
| `TG3_LH` / `TG3_WFR` | int | 3. Taggeld: Leistungshoehe % / Wartefrist Tage. |
| `TG_12TAG_FL` | 0/1 | [UVG-Z] Taggeld 1.+2. Tag: 1=versichert. |
| `TG_12TAG_LH` | int | [UVG-Z] Leistungshoehe Taggeld 1.+2. Tag in %. |
| `TGU_FL` | 0/1 | [UVG-Z] Taggeld-ueber: 1=versichert. |
| `TGU1_LH` / `TGU1_WFR` | int | [UVG-Z] Taggeld-ueber 1: Leistungshoehe % / Wartefrist Tage. |
| `TGU2_LH` / `TGU2_WFR` | int | [UVG-Z] Taggeld-ueber 2. |
| `TGU3_LH` / `TGU3_WFR` | int | [UVG-Z] Taggeld-ueber 3. |
| `IRU_FL` | 0/1 | [UVG-Z] Invaliditaetsrente-ueber: 1=versichert. |
| `INV_FL` | 0/1 | [UVG-Z] Invaliditaetskapital-bis: 1=versichert. |
| `INV_LA` | 1 / 2 | [UVG-Z] Leistungsart Invaliditaetskapital: 1=Faktor, 2=CHF. |
| `INV_LH` | float | [UVG-Z] Leistungshoehe Invaliditaetskapital (Faktor oder CHF-Betrag). |
| `INV_PV` | 100 / 225 / 350 | [UVG-Z] Progression Invaliditaetskapital-bis. |
| `IVU_FL` | 0/1 | [UVG-Z] Invaliditaetskapital-ueber: 1=versichert. |
| `IVU_LH` | float | [UVG-Z] Leistungshoehe Invaliditaetskapital-ueber als Faktor. |
| `IVU_PV` | 100 / 225 / 350 | [UVG-Z] Progression Invaliditaetskapital-ueber. |
| `HRU_FL` | 0/1 | [UVG-Z] Hinterlassenenrente-ueber: 1=versichert. |
| `TOD_FL` | 0/1 | [UVG-Z] Todesfallkapital-bis: 1=versichert. |
| `TOD_LH` | float | [UVG-Z] Leistungshoehe Todesfallkapital-bis als Faktor des Jahreslohns. |
| `TDU_FL` | 0/1 | [UVG-Z] Todesfallkapital-ueber: 1=versichert. |
| `TDU_LH` | float | [UVG-Z] Leistungshoehe Todesfallkapital-ueber als Faktor des Jahreslohns. |
| `HK_FL` | 0/1 | [UVG-Z] Heilungskosten: 1=versichert. |
| `HK_KL` | 1 / 2 | [UVG-Z] Spitalklasse: 1=privat/1. Klasse, 2=halbprivat/2. Klasse. |
| `DIFF_FL` | 0/1 | [UVG-Z] Differenzdeckung: 1=versichert. |

### Recordart 30 -- Lohnsummen

Ein Record pro Police, Deckungskreis und Jahr. Verknuepfung ueber `POLICE_NR` + `KRS_LFNR` + `JAHR`.

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `RECORDART` | 30 | Konstante. |
| `POLICE_NR` | str | Verknuepfung zu Recordart 10. |
| `KRS_LFNR` | int | Verknuepfung zu Recordart 20. |
| `JAHR` | int | Kalenderjahr der Deckungs-Gueltigkeit. |
| `LS_M` / `LS_F` | int | [KTG] Lohnsumme Maenner / Frauen, ganze CHF. |
| `LS_TOT` | int | [KTG] Gesamtlohnsumme, falls keine Geschlechteraufteilung vorliegt. |
| `LS_BIS` / `LS_UEB` | int | [UVG-Z] Lohnsumme bis / ueber UVG-Maximum, ganze CHF. |
| `LS_BU_M` / `LS_BU_F` / `LS_BU` | int | [UVG] BU-Lohnsumme Maenner / Frauen / Gesamt, ganze CHF. |
| `LS_NBU_M` / `LS_NBU_F` / `LS_NBU` | int | [UVG] NBU-Lohnsumme Maenner / Frauen / Gesamt, ganze CHF. |

### Recordart 40 -- Schaden

Ein Record pro Police, Jahr und (bei UVG) Unfallart -- aggregierte Schadenwerte.

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `RECORDART` | 40 | Konstante. |
| `POLICE_NR` | str | Verknuepfung zu Recordart 10. |
| `JAHR` | int | Bei Ereignissicht Ereignisjahr, bei Finanzsicht Zahlungsjahr (siehe `KZ_EREIG_FINANZ` in R10). |
| `UNFALLART` | 1 / 2 / 3 | [UVG] 1=BU, 2=NBU, 3=Freiwillig. |
| `ANZ_ALLE` | int | Anzahl Schaeden total im Jahr zum Sichtdatum. |
| `ANZ_PENDENT` | int | Anzahl offener Schaeden im Jahr zum Sichtdatum. |
| `ZAHLUNG_HK` | int | [UVG] Zahlungen Heilungskosten, ganze CHF. |
| `ZAHLUNG_TG` | int | [UVG] Zahlungen Taggeld, ganze CHF. |
| `ZAHLUNG_TOT` | int | [KTG/UVG-Z] Zahlung total inkl. fallbezogener Kosten, ganze CHF. |
| `RUECKSTELLUNG` | int | [KTG/UVG-Z] Kumulierte Fallreserven, ganze CHF. |

### Recordart 50 -- Langzeit-Schaeden

Ein Record pro KTG-Langzeitfall (nur KTG). Ist ausdruecklich sichtbar, dass keine Langzeitfaelle vorliegen, wird ein einzelner Record mit `STATUS`=0 erzeugt.

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `RECORDART` | 50 | Konstante. |
| `POLICE_NR` | str | Verknuepfung zu Recordart 10. |
| `ID` | int | Laufnummer des Schadens, chronologisch nach Ereignisdatum; bei `STATUS`=0 leer. |
| `EREIGNIS_DT` | Datum | Ereignisdatum des Schadens; bei `STATUS`=0 leer. |
| `STATUS` | 0 / 1 / 2 / 3 | 1=pendent/offen, 2=erledigt, 3=max. Leistungsdauer erreicht (ausgesteuert), 0=keine Langzeit-Schaeden vorhanden. |
| `ZAHLUNG_TOT` | int | Summe geleisteter Taggelder und fallbezogener Kosten, ganze CHF. |
| `RUECK_TOTAL_BETR` | int | Offene Fallreserven, ganze CHF; bei geschlossenen Faellen 0. |

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
