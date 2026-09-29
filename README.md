# Basel-Stadt environmental audit · Umweltbilanz Basel-Stadt

**Live:** [English](https://jonashertner.github.io/basel-environmental-audit/) · [Deutsch](https://jonashertner.github.io/basel-environmental-audit/de/)

A graded assessment of the environment in the canton of Basel-Stadt (climate, heat, chemical legacy, air, water, and noise and traffic) built only on official data: values that an official body measured, counted or calculated, and sums that this audit derived from them. Every figure states which, and carries a numbered citation that opens its source.

Eine benotete Bilanz der Umwelt im Kanton Basel-Stadt (Klima, Hitze, Chemie-Altlasten, Luft, Wasser, Lärm und Verkehr), gestützt nur auf amtliche Daten: Werte, die eine amtliche Stelle gemessen, gezählt oder berechnet hat, und Summen, die diese Bilanz daraus abgeleitet hat. Jede Zahl nennt ihre Grundlage und trägt eine nummerierte Quellenangabe, die ihre Quelle öffnet.

Last reviewed: 29 September 2026.

## The rule

Every figure comes from an official source (authorities, courts, public utilities and international bodies) and states its basis:

- **Measured**: measured by an official body, or a statistic it forms directly from its measurements (an annual mean, a count of hot days, a 30-year normal).
- **Counted**: counted by an official body (registers, permits, site inventories, trees, passengers, votes).
- **Official calculation**: calculated by an official body by its own published method (the canton's greenhouse gas inventory, a canopy cover, a share of the road network).
- **Derived from official data**: calculated by this audit from official figures alone, by adding or subtracting them; the chart or note says how.
- **Assessed evidence**: a finding or range from an official review of many studies (IPCC, WHO, EEA, BAFU and similar). It says what a measure achieves in general, not what it achieved in Basel, and is used only in «What works».

Estimates, projections, costs, averages carried over from elsewhere (such as the Swiss average per-capita footprint applied to Basel) and press or advocacy figures are excluded. Legal limits, guidelines and targets appear only as labelled reference values. The build enforces this: it fails if a figure, chart, the hero or the vote results cite a source that is not typed `official`, or lack a `basis`.

## What is on the page

- **Thesis and summer strip.** The 92 days of June to August 2026 at Basel-Binningen: 52 hot days (30 °C or more), against MeteoSwiss's normal of 14.3 for a whole year.
- **Grades.** An overall grade, three facets (governance, outcomes, legacy) and one grade per area, each with a one-line verdict.
- **Areas.** Key figures, charts, "The uncomfortable part" and "What would raise the grade" for each of the six areas.
- **What works.** Fifteen measures against summer heat on a path from protecting people to regenerating living systems. For each: what official evidence reviews say, an official record from another city, and Basel's status (among the leaders, in place with gaps, behind, missing). The status is the audit's judgment.
- **Voters.** Ballot results that explain the gap between targets and measures.
- **Deadlines.** Past events and upcoming deadlines, with countdowns computed from the reader's date.
- **Open obligations.** Binding duties with a deadline (federal or cantonal law, or a Grand Council decision) and whether Basel-Stadt has met them: not met, at risk, or met late.
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

- Every metric needs at least one source id in `sources` and a `basis`: `measured`, `counted`, `official` or `derived` (a list where a chart mixes them). Charts, the hero and the vote results carry a `basis` too. The labels and their definitions live in `method.basis`.
- A metric has a short `label` and an optional `context` line for comparisons and reference values.
- Source `type` is one of `official`, `press`, `advocacy`, `reference`. Only `official` sources may carry a figure; the others may appear in context only, and are flagged. The current edition cites official sources only. Source titles stay in their original language.
- `measures.items` have a `stage`, a `status` and three parts (`evidence`, `exemplar`, `basel`), each with official `sources`. A part carries a `basis` (here `assessed` is allowed) when it states a figure; a part that states only a rule, target or date carries none.
- `obligations.items` have a `status`, an ISO `due` date (optional `dueDisplay` for recurring or year-only deadlines), an optional ISO `done` date for duties met late, and official `sources`.
- Timeline items take an ISO `date`. For approximate dates, add `precision` (`year`, `month`, `season`) and optionally `display`; the countdown uses the ISO date.
- Grades use A–D or F with an optional `+` or `–`.
- The template computes no figures of its own. Where this audit adds up or subtracts official figures (hot days over a summer, the waste segment "Other", the years between two official dates), the figure is labelled `derived` and the note says how.
- German text follows Swiss conventions: "ss" for "ß", «guillemets», an apostrophe as thousands separator (28’000) and a decimal comma in running text.

## Deployment

GitHub Pages, built by GitHub Actions on every push to `main` (Settings → Pages → Source: GitHub Actions). Pull requests run the validation and fail if the built files were not regenerated after a data change.

## Design notes

- **Typography.** A single family, Archivo, using its width axis from condensed (grades, figures, headlines) to normal (text), in the Swiss typographic tradition of which Basel's School of Design is a centre. The font is self-hosted, so the page makes no third-party requests.
- **Colour.** Black and white, as in Basel's colours, plus three signals: Rhine teal for good grades, sulfur yellow for middling ones, and a magenta close to fuchsine, one of the synthetic dyes Basel's chemical industry grew out of, for poor grades and for the hot days of 2026.
- **Basis marks.** A filled square, a half-filled square, a dot, a ring or an outlined diamond before each figure's citations marks it as measured, counted, officially calculated, derived or assessed evidence. Citations are quiet numbered tabs that open the source.
- **Motion.** One moment: the hot-day segment of the summer strip extends on load. It is skipped when the reader prefers reduced motion.

## Before relying on it

- Grades are an analytical judgment, not an official rating. Recommendations are the audit's analysis, not the canton's plans.
- Data years differ (heating counts September 2026, weather 2026, air 2025, groundwater 2024 and 2025, greenhouse gas inventory 2022). Figures show their source and year.
- Not legal advice.

## Licence

Text and data: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Code: MIT. Font: SIL OFL 1.1. See [LICENSE](LICENSE). Third-party sources remain under their own terms; the page links to them and does not reproduce them. To cite, see [CITATION.cff](CITATION.cff).
