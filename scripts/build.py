#!/usr/bin/env python3
"""Validate data/assessment.json and build the English and German pages.

Usage:
    python scripts/build.py          # validate and write index.html, de/index.html, sitemap.xml
    python scripts/build.py --check  # validate and fail if any built file is out of date

No third-party dependencies. Exit code 1 on any validation error.
"""
from __future__ import annotations

import html
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "assessment.json"
TEMPLATE = ROOT / "src" / "template.html"
PLACEHOLDER = "/*__ASSESSMENT_DATA__*/"

LANGS = ("en", "de")
PAGES = {
    "en": {"out": ROOT / "index.html", "base": "", "path": "", "locale": "en_GB"},
    "de": {"out": ROOT / "de" / "index.html", "base": "../", "path": "de/", "locale": "de_CH"},
}
CHROME = {
    "en": {"skip": "Skip to content", "nav": "Sections", "theme": "Theme: Auto", "switch": "Deutsch", "switchShort": "DE",
           "short": "Basel-Stadt audit", "noscript": "This page draws its charts with JavaScript. The full data is in",
           "grades": "Grades by area", "overall": "Overall grade"},
    "de": {"skip": "Zum Inhalt springen", "nav": "Abschnitte", "theme": "Darstellung: Auto", "switch": "English", "switchShort": "EN",
           "short": "Umweltbilanz BS", "noscript": "Diese Seite zeichnet ihre Grafiken mit JavaScript. Die vollständigen Daten stehen in",
           "grades": "Noten nach Bereich", "overall": "Gesamtnote"},
}

GRADE = re.compile(r"^[A-DF][+–-]?$")
DATE = re.compile(r"^\d{4}(-\d{2}(-\d{2})?)?$")
SOURCE_TYPES = {"official", "press", "advocacy", "reference"}
BASES = {"measured", "counted", "official", "derived", "assessed"}
REQUIRED_SOURCE_FIELDS = ("id", "type", "publisher", "date", "title", "url")
# Fields that carry reader-facing prose and must exist in every language.
TEXT_KEYS = {
    "title", "scope", "thesis", "standfirst", "disclaimer", "description", "kicker", "author",
    "label", "short", "note", "summary", "verdict", "text", "name", "place", "k", "v", "lead",
    "trajCaption", "statusNote", "benefitsLabel",
    "kind", "law", "body", "work", "meaning", "valueLabel", "deadlineLabel", "display",
    "dueDisplay", "doneDisplay", "measure",
}
# Lists whose items are reader-facing prose.
TEXT_LIST_KEYS = {"notes"}


def is_loc(x) -> bool:
    return isinstance(x, dict) and set(x) == set(LANGS)


def loc(x, lang: str) -> str:
    return x[lang] if is_loc(x) else ("" if x is None else str(x))


def collect_refs(node, path="$", out=None):
    """Return every (path, source_id) referenced anywhere under a 'sources' key,
    excluding the top-level source registry itself."""
    if out is None:
        out = []
    if isinstance(node, dict):
        for key, value in node.items():
            child = f"{path}.{key}"
            if (key == "sources" or key.endswith("Sources")) and path != "$" and isinstance(value, list):
                out.extend((child, ref) for ref in value)
            else:
                collect_refs(value, child, out)
    elif isinstance(node, list):
        for i, item in enumerate(node):
            collect_refs(item, f"{path}[{i}]", out)
    return out


def check_languages(node, path, errors):
    """Every localised field has non-empty text in each language; prose fields are never left monolingual."""
    if is_loc(node):
        for lang in LANGS:
            if not isinstance(node[lang], str) or not node[lang].strip():
                errors.append(f"{path} is missing its '{lang}' text.")
        if "—" in node.get("en", "") + node.get("de", ""):
            errors.append(f"{path} contains an em-dash; use an en-dash or comma.")
        return
    if isinstance(node, dict):
        for key, value in node.items():
            child = f"{path}.{key}"
            if key in TEXT_KEYS and isinstance(value, str) and not (key == "kind" and value == "point"):
                errors.append(f"{child} is a plain string; give it as {{\"en\": ..., \"de\": ...}}.")
            elif key in TEXT_LIST_KEYS and isinstance(value, list) and any(isinstance(x, str) for x in value):
                errors.append(f"{child} contains plain strings; give each item as {{\"en\": ..., \"de\": ...}}.")
            elif isinstance(value, dict) and not is_loc(value) and set(value) & set(LANGS):
                errors.append(f"{child} has only some languages: {sorted(value)}.")
            else:
                check_languages(value, child, errors)
    elif isinstance(node, list):
        for i, item in enumerate(node):
            check_languages(item, f"{path}[{i}]", errors)


def validate(d: dict) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    # Meta
    meta = d.get("meta", {})
    try:
        reviewed = date.fromisoformat(meta.get("reviewed", ""))
        age = (date.today() - reviewed).days
        if age > meta.get("reviewIntervalDays", 90):
            warnings.append(f"Review is {age} days old; interval is {meta.get('reviewIntervalDays')} days.")
    except ValueError:
        errors.append("meta.reviewed must be an ISO date (YYYY-MM-DD).")
    if not str(meta.get("siteUrl", "")).startswith("https://") or not meta["siteUrl"].endswith("/"):
        errors.append("meta.siteUrl must be an https URL ending in '/'.")

    # Languages (the source registry keeps original titles and is exempt)
    check_languages({k: v for k, v in d.items() if k != "sources"}, "$", errors)

    # Sources registry
    sources = d.get("sources", [])
    ids = [s.get("id") for s in sources]
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        errors.append(f"Duplicate source ids: {sorted(dupes)}")
    for s in sources:
        for field in REQUIRED_SOURCE_FIELDS:
            if not s.get(field):
                errors.append(f"Source {s.get('id', '?')} is missing '{field}'.")
        if s.get("type") not in SOURCE_TYPES:
            errors.append(f"Source {s.get('id')} has unknown type '{s.get('type')}'.")
        if s.get("url") and not s["url"].startswith("https://"):
            errors.append(f"Source {s.get('id')} URL must use https.")
        if s.get("date") not in (None, "n.d.") and not DATE.match(str(s.get("date"))):
            errors.append(f"Source {s.get('id')} date '{s.get('date')}' must be YYYY, YYYY-MM, YYYY-MM-DD or n.d.")

    # References resolve
    known = set(ids)
    refs = collect_refs(d)
    for where, ref in refs:
        if ref not in known:
            errors.append(f"{where} cites unknown source '{ref}'.")
    used = {ref for _, ref in refs}
    for unused in sorted(known - used):
        warnings.append(f"Source '{unused}' is listed but never cited.")

    # Values: every figure, chart value and vote result rests on official sources only
    types = {s.get("id"): s.get("type") for s in sources}
    value_nodes = [("hero", d.get("hero", {})), ("politics", d.get("politics", {}))]
    value_nodes += [(f"chart '{cid}'", c) for cid, c in d.get("charts", {}).items()]
    value_nodes += [(f"metrics of '{dom.get('id')}'", dom.get("metrics", [])) for dom in d.get("domains", [])]
    for where, node in value_nodes:
        for path, ref in collect_refs(node, where):
            if types.get(ref) and types[ref] != "official":
                errors.append(f"{path} cites '{ref}' ({types[ref]}); values may cite official sources only.")

    # Basis: every figure says whether it was measured, counted, calculated officially or derived here
    basis_ids = {b.get("id") for b in d.get("method", {}).get("basis", [])}
    if basis_ids != BASES:
        errors.append(f"method.basis must define exactly {sorted(BASES)}.")
    def check_basis(node, where):
        b = node.get("basis") if isinstance(node, dict) else None
        vals = b if isinstance(b, list) else [b]
        if not b or any(v not in BASES for v in vals):
            errors.append(f"{where} needs a basis from {sorted(BASES)}.")
    check_basis(d.get("hero", {}), "hero")
    check_basis(d.get("politics", {}), "politics")
    for cid, c in d.get("charts", {}).items():
        check_basis(c, f"chart '{cid}'")
    for dom in d.get("domains", []):
        for m in dom.get("metrics", []):
            check_basis(m, f"metric '{loc(m.get('value'), 'en')}' in '{dom.get('id')}'")

    # Measures: proven measures, each with its evidence, an exemplar and Basel's status
    ms = d.get("measures")
    if ms:
        stages = {s.get("id") for s in ms.get("stages", [])}
        statuses = {s.get("id") for s in ms.get("status", [])}
        benefits = {b.get("id") for b in ms.get("benefits", [])}
        seen = set()
        for it in ms.get("items", []):
            mid = it.get("id")
            if not mid or mid in seen:
                errors.append(f"Measure id '{mid}' is missing or duplicated.")
            seen.add(mid)
            if it.get("stage") not in stages:
                errors.append(f"Measure '{mid}' has unknown stage '{it.get('stage')}'.")
            if it.get("status") not in statuses:
                errors.append(f"Measure '{mid}' has unknown status '{it.get('status')}'.")
            for b in it.get("benefits", []):
                if b not in benefits:
                    errors.append(f"Measure '{mid}' has unknown benefit '{b}'.")
            for part in ("evidence", "exemplar", "basel"):
                node = it.get(part)
                if not node or not node.get("sources"):
                    errors.append(f"Measure '{mid}' needs '{part}' with sources.")
                    continue
                # A part that states only rules, targets or dates carries no basis mark.
                if "basis" in node:
                    check_basis(node, f"measure '{mid}' {part}")
                for path, ref in collect_refs(node, f"measure '{mid}' {part}"):
                    if types.get(ref) and types[ref] != "official":
                        errors.append(f"{path} cites '{ref}' ({types[ref]}); values may cite official sources only.")

    # Obligations: binding duties with a deadline, and whether they were met
    ob = d.get("obligations")
    if ob:
        ostat = {s.get("id") for s in ob.get("status", [])}
        for it in ob.get("items", []):
            oid = it.get("id")
            if it.get("status") not in ostat:
                errors.append(f"Obligation '{oid}' has unknown status '{it.get('status')}'.")
            for k in ("due", "done"):
                if k in it or k == "due":
                    try:
                        date.fromisoformat(it.get(k, ""))
                    except (TypeError, ValueError):
                        errors.append(f"Obligation '{oid}' needs an ISO '{k}' date.")
            if not it.get("sources"):
                errors.append(f"Obligation '{oid}' has no source.")
            for path, ref in collect_refs(it, f"obligation '{oid}'"):
                if types.get(ref) and types[ref] != "official":
                    errors.append(f"{path} cites '{ref}' ({types[ref]}); obligations may cite official sources only.")

    # Noncompliance: limits exceeded or met, and missed deadlines drawn from the obligations
    cp = d.get("compliance")
    if cp:
        cstat = {st.get("id") for st in cp.get("status", [])}
        obs = {o.get("id"): o for o in (ob or {}).get("items", [])}
        seen = set()
        for it in cp.get("items", []):
            cid = it.get("id")
            if not cid or cid in seen:
                errors.append(f"Compliance id '{cid}' is missing or duplicated.")
            seen.add(cid)
            if it.get("status") not in cstat:
                errors.append(f"Compliance item '{cid}' has unknown status '{it.get('status')}'.")
            if "ref" in it:
                o = obs.get(it["ref"])
                if not o:
                    errors.append(f"Compliance item '{cid}' refers to unknown obligation '{it['ref']}'.")
                elif o.get("status") != "open" or o.get("done"):
                    errors.append(f"Compliance item '{cid}' refers to obligation '{it['ref']}', which is not open.")
                continue
            for k in ("title", "law", "value", "measure", "body"):
                if not it.get(k):
                    errors.append(f"Compliance item '{cid}' needs '{k}'.")
            if not it.get("sources"):
                errors.append(f"Compliance item '{cid}' has no source.")
            check_basis(it, f"compliance item '{cid}'")
        for path, ref in collect_refs(cp, "compliance"):
            if types.get(ref) and types[ref] != "official":
                errors.append(f"{path} cites '{ref}' ({types[ref]}); compliance may cite official sources only.")

    # Grades
    def check_grade(value, where):
        if not isinstance(value, str) or not GRADE.match(value):
            errors.append(f"{where} has invalid grade '{value}'.")

    check_grade(d.get("overall", {}).get("grade"), "overall")
    for f in d.get("overall", {}).get("facets", []):
        check_grade(f.get("grade"), f"overall facet '{loc(f.get('label'), 'en')}'")
    charts = d.get("charts", {})
    for dom in d.get("domains", []):
        check_grade(dom.get("grade"), f"domain '{dom.get('id')}'")
        for sg in dom.get("subgrades", []):
            check_grade(sg.get("grade"), f"domain '{dom.get('id')}' subgrade")
        for cid in dom.get("charts", []):
            if cid not in charts:
                errors.append(f"Domain '{dom.get('id')}' references missing chart '{cid}'.")
        for m in dom.get("metrics", []):
            if not m.get("sources"):
                errors.append(f"Metric '{loc(m.get('value'), 'en')}' in '{dom.get('id')}' has no source.")

    # Timeline, votes, changelog
    for t in d.get("timeline", []):
        try:
            date.fromisoformat(t["date"])
        except (KeyError, ValueError):
            errors.append(f"Timeline item '{loc(t.get('label'), 'en')}' needs an ISO date.")
    for v in d.get("politics", {}).get("votes", []):
        if not 0 <= float(v.get("yes", -1)) <= 100:
            errors.append(f"Vote '{loc(v.get('label'), 'en')}' has an invalid yes share.")
    for c in d.get("changelog", []):
        try:
            date.fromisoformat(c["date"])
        except (KeyError, ValueError):
            errors.append("Every changelog entry needs an ISO date.")

    return errors, warnings


def attr(s: str) -> str:
    return html.escape(s, quote=True)


def head(d: dict, lang: str) -> str:
    m = d["meta"]
    site = m["siteUrl"]
    url = site + PAGES[lang]["path"]
    title = f"{loc(m['title'], lang)} {m['edition']}"
    desc = loc(m["description"], lang)
    other = "de" if lang == "en" else "en"
    ld = {
        "@context": "https://schema.org",
        "@type": "Dataset",
        "name": title,
        "description": desc,
        "url": url,
        "inLanguage": lang,
        "dateModified": m["reviewed"],
        "creator": {"@type": "Person", "name": loc(m["author"], lang)},
        "license": "https://creativecommons.org/licenses/by/4.0/",
        "spatialCoverage": {"@type": "Place", "name": "Kanton Basel-Stadt, Schweiz"},
        "isAccessibleForFree": True,
        "distribution": [{"@type": "DataDownload", "encodingFormat": "application/json", "contentUrl": site + "data/assessment.json"}],
    }
    ld_json = json.dumps(ld, ensure_ascii=False).replace("</", "<\\/")
    lines = [
        f"<title>{html.escape(title)}</title>",
        f'<meta name="description" content="{attr(desc)}">',
        f'<meta name="author" content="{attr(loc(m["author"], lang))}">',
        f'<link rel="canonical" href="{url}">',
        f'<link rel="alternate" hreflang="en" href="{site}">',
        f'<link rel="alternate" hreflang="de" href="{site}de/">',
        f'<link rel="alternate" hreflang="x-default" href="{site}">',
        '<meta property="og:type" content="website">',
        f'<meta property="og:title" content="{attr(title)}">',
        f'<meta property="og:description" content="{attr(desc)}">',
        f'<meta property="og:url" content="{url}">',
        f'<meta property="og:image" content="{site}assets/og-{lang}.png">',
        '<meta property="og:image:width" content="1200">',
        '<meta property="og:image:height" content="630">',
        f'<meta property="og:locale" content="{PAGES[lang]["locale"]}">',
        f'<meta property="og:locale:alternate" content="{PAGES[other]["locale"]}">',
        '<meta name="twitter:card" content="summary_large_image">',
        f'<script type="application/ld+json">{ld_json}</script>',
    ]
    if lang == "en":
        # First visit from a German-language browser goes to the German page; an explicit choice is remembered.
        lines.append("<script>try{if(!localStorage.getItem('basel-audit-lang')&&/^de\\b/i.test((navigator.languages&&navigator.languages[0])||navigator.language||''))location.replace('de/'+location.hash)}catch(e){}</script>")
    return "\n".join(lines)


def noscript(d: dict, lang: str) -> str:
    """A static summary for readers and crawlers without JavaScript."""
    m, o = d["meta"], d["overall"]
    items = "".join(
        f"<li><b>{html.escape(dom['grade'])}</b> {html.escape(loc(dom['name'], lang))}: {html.escape(loc(dom['verdict'], lang))}</li>"
        for dom in d["domains"]
    )
    data_href = PAGES[lang]["base"] + "data/assessment.json"
    c = CHROME[lang]
    return (
        f'<noscript><div class="wrap noscript"><h1>{html.escape(loc(m["thesis"], lang))}</h1>'
        f"<p>{html.escape(loc(m['standfirst'], lang))}</p>"
        f"<p><b>{c['overall']}: {html.escape(o['grade'])}.</b> {html.escape(loc(o['summary'], lang))}</p>"
        f"<h2>{c['grades']}</h2><ul>{items}</ul>"
        f'<p>{c["noscript"]} <a href="{data_href}">assessment.json</a>.</p></div></noscript>'
    )


def build(d: dict, lang: str) -> str:
    template = TEMPLATE.read_text(encoding="utf-8")
    if PLACEHOLDER not in template:
        raise SystemExit(f"Placeholder {PLACEHOLDER} not found in {TEMPLATE}.")
    m, c = d["meta"], CHROME[lang]
    other = "de" if lang == "en" else "en"
    switch_href = "de/" if lang == "en" else "../"
    switch = (f'<a class="lang-btn" id="lang-btn" href="{switch_href}" hreflang="{other}" lang="{other}" '
              f'aria-label="{c["switch"]}">{c["switchShort"]}</a>')
    payload = json.dumps(d, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    out = (template
           .replace("<!--__HEAD__-->", head(d, lang))
           .replace("<!--__NOSCRIPT__-->", noscript(d, lang))
           .replace("<!--__LANGSWITCH__-->", switch)
           .replace("__LANG__", lang)
           .replace("__BASE__", PAGES[lang]["base"])
           .replace("__SKIP__", c["skip"])
           .replace("__NAV_LABEL__", c["nav"])
           .replace("__THEME__", c["theme"])
           .replace("__BRAND_FULL__", html.escape(f"{loc(m['title'], lang)} {m['edition']}"))
           .replace("__BRAND_SHORT__", c["short"])
           .replace(PLACEHOLDER, payload))
    leftover = re.findall(r"__[A-Z_]+__", out.replace(payload, ""))
    if leftover:
        raise SystemExit(f"Unfilled placeholders in {lang} page: {sorted(set(leftover))}")
    return out


def sitemap(d: dict) -> str:
    site, day = d["meta"]["siteUrl"], d["meta"]["reviewed"]
    alt = f'<xhtml:link rel="alternate" hreflang="en" href="{site}"/><xhtml:link rel="alternate" hreflang="de" href="{site}de/"/>'
    urls = "".join(f"<url><loc>{site}{p}</loc><lastmod>{day}</lastmod>{alt}</url>" for p in ("", "de/"))
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">'
            f"{urls}</urlset>\n")


def outputs(d: dict) -> dict[Path, str]:
    files = {PAGES[lang]["out"]: build(d, lang) for lang in LANGS}
    files[ROOT / "sitemap.xml"] = sitemap(d)
    files[ROOT / "robots.txt"] = f"User-agent: *\nAllow: /\nSitemap: {d['meta']['siteUrl']}sitemap.xml\n"
    return files


def main() -> int:
    check_only = "--check" in sys.argv
    d = json.loads(DATA.read_text(encoding="utf-8"))
    errors, warnings = validate(d)
    for w in warnings:
        print(f"warning: {w}")
    for e in errors:
        print(f"error: {e}")
    if errors:
        print(f"{len(errors)} error(s). Nothing written.")
        return 1

    files = outputs(d)
    if check_only:
        stale = [p for p, text in files.items() if not p.exists() or p.read_text(encoding="utf-8") != text]
        if stale:
            print("Out of date: " + ", ".join(str(p.relative_to(ROOT)) for p in stale) + ". Run: python scripts/build.py")
            return 1
        print("Built files are up to date.")
        return 0

    for path, text in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    n_refs = len(collect_refs(d))
    print(f"Built index.html and de/index.html: {len(d['sources'])} sources, {n_refs} citations, {len(d['domains'])} areas.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
