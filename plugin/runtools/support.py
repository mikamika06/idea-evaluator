import json
import os

from runtools.pagetext import cut_qualifier, fetch, page_date, quote_window

LABELS = ("supports", "partial", "does_not_support", "truncated_qualifier")
DROP = {"does_not_support", "truncated_qualifier"}
WINDOWS = "support-windows.json"
CHECKS = "support.json"
RADIUS = 2


def _load(path):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def _read(path):
    try:
        with open(path, errors="ignore") as f:
            return f.read()
    except OSError:
        return None


def _page(url):
    meta = fetch(url)
    if not meta.get("ok") or not meta.get("path"):
        return None, meta
    return _read(meta["path"]), meta


def claim_pairs(claims):
    pairs = {}
    for i, c in enumerate(claims or []):
        if not isinstance(c, dict):
            continue
        code = str(c.get("code") or f"claim{i + 1}")
        for fid in c.get("finding_ids") or []:
            pairs.setdefault((code, fid), c.get("claim") or "")
    return pairs


def build_windows(run_dir, findings, claims=None, pages=None, page=_page):
    if claims is None:
        audit = _load(os.path.join(run_dir, "audit.json")) or {}
        claims = audit.get("decisive_claims") or []
    pages = pages or {}
    out = []
    for (code, fid), claim in sorted(claim_pairs(claims).items()):
        row = findings.get(fid) or {}
        quote = row.get("quote_original") or row.get("quote") or ""
        url = row.get("url")
        text, meta = pages.get(fid, (None, None))
        if text is None and url:
            text, meta = page(url)
        window = quote_window(quote, text, RADIUS) if text else None
        entry = {"code": code, "finding_id": fid, "claim": claim, "url": url, "quote": quote,
                 "window": window["text"] if window else None,
                 "before": window["before"] if window else [],
                 "after": window["after"] if window else [],
                 "window_status": "ok" if window else ("quote_not_on_page" if text else "page_unavailable"),
                 "qualifier_hint": cut_qualifier(quote, text) if text else None}
        entry.update(page_date(meta or {}, row))
        out.append(entry)
    doc = {"generated_by": "support-windows", "radius_sentences": RADIUS, "pairs": out}
    with open(os.path.join(run_dir, WINDOWS), "w") as f:
        json.dump(doc, f, indent=1, ensure_ascii=False)
    return doc


def load_windows(run_dir):
    doc = _load(os.path.join(run_dir, WINDOWS))
    if not isinstance(doc, dict):
        return None
    return {(p.get("code"), p.get("finding_id")): p for p in doc.get("pairs") or [] if isinstance(p, dict)}


def load_checks(run_dir):
    doc = _load(os.path.join(run_dir, CHECKS))
    if not isinstance(doc, dict):
        return None
    out = {}
    for c in doc.get("checks") or []:
        if isinstance(c, dict) and c.get("code") and c.get("finding_id"):
            out[(str(c["code"]), c["finding_id"])] = {"label": c.get("label"), "reason": str(c.get("reason") or "").strip()}
    return out


def label_of(support, code, fid):
    entry = (support or {}).get((code, fid))
    return entry.get("label") if isinstance(entry, dict) else None


def cited_pairs(verdict):
    pairs = []
    for p in verdict.get("patterns") or []:
        if isinstance(p, dict) and p.get("fired") and p.get("basis") != "card":
            pairs += [(p.get("code"), fid) for fid in p.get("finding_ids") or []]
    for s in verdict.get("alive_signals") or []:
        if isinstance(s, dict):
            pairs += [(s.get("code"), fid) for fid in s.get("finding_ids") or []]
    return list(dict.fromkeys(pairs))


def check_support(verdict, run_dir):
    pairs = cited_pairs(verdict)
    if not pairs:
        return []
    windows = load_windows(run_dir)
    checks = load_checks(run_dir)
    if windows is None:
        return [f"{WINDOWS} missing: run bin/support-windows <RUN> after the audit"]
    if checks is None:
        return [f"{CHECKS} missing: dispatch the support-checker on {WINDOWS}"]
    errors = []
    for code, fid in pairs:
        if (code, fid) not in windows:
            errors.append(f"{WINDOWS}: no window for {code} {fid}; add {fid} to the {code} claim and rerun the audit and bin/support-windows")
            continue
        entry = checks.get((code, fid))
        if not entry:
            errors.append(f"{CHECKS}: {code} {fid} has no support label")
        elif entry.get("label") not in LABELS:
            errors.append(f"{CHECKS}: {code} {fid} label {entry.get('label')!r} not in {list(LABELS)}")
        elif not entry.get("reason"):
            errors.append(f"{CHECKS}: {code} {fid} needs a short reason")
    return errors
