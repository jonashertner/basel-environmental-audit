# Basel-Stadt environmental audit · Umweltbilanz Basel-Stadt

**Live:** [English](https://jonashertner.github.io/basel-environmental-audit/) · [Deutsch](https://jonashertner.github.io/basel-environmental-audit/de/)

A graded assessment of the environment in the canton of Basel-Stadt (climate, heat, chemical legacy, air, water, and noise and traffic) built only on values that an official body measured or counted. Every figure on the page carries a numbered citation that opens its source.

Eine benotete Bilanz der Umwelt im Kanton Basel-Stadt (Klima, Hitze, Chemie-Altlasten, Luft, Wasser, Lärm und Verkehr), gestützt nur auf Werte, die eine amtliche Stelle gemessen oder gezählt hat. Jede Zahl trägt eine nummerierte Quellenangabe, die ihre Quelle öffnet.

Last reviewed: 29 September 2026.

## The rule

Only measured or counted values from official sources: authorities, courts, public utilities and international bodies. Estimates, projections, modelled values, costs and press or advocacy figures are excluded, including the canton's greenhouse gas inventory, which is calculated. Legal limits, guidelines and targets appear only as labelled reference values. The build enforces this: it fails if a figure, chart, the hero or the vote results cite a source that is not typed `official`.

## What is on the page

- **Thesis and summer strip.** The 92 days of June to August 2026 at Basel-Binningen: 52 hot days (30 °C or more) against a normal of 13.6.
- **Grades.** An overall grade, three facets (governance, outcomes, legacy) and one grade per area, each with a one-line verdict.
- **Areas.** Key figures, charts, "The uncomfortable part" and "What would raise the grade" for each of the six areas.
- **Voters.** Ballot results that explain the gap between targets and measures.
- **Deadlines.** Past events and upcoming deadlines, with countdowns computed from the reader's date.
- **Legal questions.** Where the findings turn into legal questions, with statutory and case-law references.
- **Method, revision history and a citation line.**
- **Sources.** Filterable by type and searchable, each showing where it is cited.

Other functions: English and German editions from one data file; light, dark and automatic themes; a print stylesheet that expands all data tables; downloads of the full dataset (JSON) and the source list (CSV); a "review due" flag once the data is older than the review interval; "Show the numbers" tables under every chart; a static summary for readers without JavaScript.

## Repository layout

```
data/assessment.json          The only file you edit for content (both languages)
src/template.html             Markup, styles and rendering code
scripts/build.py              Validates the data and writes the built files
index.html, de/index.html     Built pages, English and German (committed)
sitemap.xml, robots.txt       Built
assets/                       Self-hosted font (SIL OFL) and social preview images
.github/workflows/pages.yml   Validation on pull requests, deployment from main
```

No framework and no build dependencies beyond Python's standard library.

## Updating the content

1. Edit `data/assessment.json`.
2. Run `python scripts/build.py`.
3. Open `index.html` and `de/index.html` through a local server (`python -m http.server`) to check, then commit.

Every piece of reader-facing text is stored in both languages:

```json
"label": { "en": "Trees on public ground in the city", "de": "Bäume auf öffentlichem Grund in der Stadt" }
```

The build fails if a text field lacks either language or contains an em-dash, a figure cites a source that does not exist, a source lacks a field or an https URL, a grade is malformed, a chart is missing, or a date is not ISO formatted. It warns about sources that are listed but never cited, and about a review older than `meta.reviewIntervalDays` (90 by default). Add a line to `changelog` for each substantive revision.

Conventions in the data file:

- Every metric needs at least one source id in `sources`.
- Source `type` is one of `official`, `press`, `advocacy`, `reference`. Only `official` sources may carry a figure; the others may appear in context only, and are flagged. The current edition cites official sources only. Source titles stay in their original language.
- Timeline items take an ISO `date`. For approximate dates, add `precision` (`year`, `month`, `season`) and optionally `display`; the countdown uses the ISO date.
- Grades use A–D or F with an optional `+` or `–`.
- The template computes no figures of its own. Where official counts are added up (hot days per summer, the June to August normal, the waste segment "Other"), the method notes say so.
- German text follows Swiss conventions: "ss" for "ß", «guillemets», an apostrophe as thousands separator (28’000) and a decimal comma in running text.

## Deployment

GitHub Pages, built by GitHub Actions on every push to `main` (Settings → Pages → Source: GitHub Actions). Pull requests run the validation and fail if the built files were not regenerated after a data change.

## Design notes

- **Typography.** A single family, Archivo, using its width axis from condensed (grades, figures, headlines) to normal (text), in the Swiss typographic tradition of which Basel's School of Design is a centre. The font is self-hosted, so the page makes no third-party requests.
- **Colour.** Black and white, as in Basel's colours, plus three signals: Rhine teal for good grades, sulfur yellow for middling ones, and a magenta close to fuchsine, one of the synthetic dyes Basel's chemical industry grew out of, for poor grades and for the hot days of 2026.
- **Motion.** One moment: the hot-day segment of the summer strip extends on load. It is skipped when the reader prefers reduced motion.

## Before relying on it

- Grades are an analytical judgment, not an official rating. Recommendations are the audit's analysis, not the canton's plans.
- Data years differ (heating counts September 2026, weather 2026, air 2025, groundwater 2024 and 2025). Figures show their source and year.
- Not legal advice.

## Licence

Text and data: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Code: MIT. Font: SIL OFL 1.1. See [LICENSE](LICENSE). Third-party sources remain under their own terms; the page links to them and does not reproduce them. To cite, see [CITATION.cff](CITATION.cff).
