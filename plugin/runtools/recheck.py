import json
import os
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

from runtools.pagetext import page_date, recheck_quote
from runtools.runcheck import _findings
from runtools.support import build_windows

PRIMARY = {"regulator", "registry"}


def _domain(url):
    host = urlparse(url or "").netloc.lower()
    return host[4:] if host.startswith("www.") else host


def _languages_searched(run_dir):
    langs = set()
    for name in sorted(os.listdir(run_dir)):
        if not (name.startswith("q") and name.endswith(".json")) and name not in ("dossier.json", "law.json"):
            continue
        try:
            with open(os.path.join(run_dir, name)) as f:
                card = json.load(f)
        except (OSError, ValueError):
            continue
        for row in (card.get("search_matrix") or []) if isinstance(card, dict) else []:
            if isinstance(row, dict) and row.get("results") is not None and row.get("lang"):
                langs.add(str(row["lang"]).lower())
    return langs


NOTES = {
    "found": "live page contains the quote",
    "gone": "the cached copy had the quote; the live page no longer does",
    "not_found": "quote not on the page",
    "fetch_failed": "page could not be fetched",
}


def recheck(run_dir, claims, check=recheck_quote, workers=8, windows=True):
    findings = _findings(run_dir)
    ids = sorted({fid for c in claims for fid in c.get("finding_ids") or []})
    pages = {}

    def one(fid):
        row = findings.get(fid)
        if row is None:
            return fid, {"finding_id": fid, "quote_check": "fetch_failed", "independent_sources": 0, "note": "finding not in store"}
        res = check(row.get("url", ""), row.get("quote_original") or row.get("quote") or "")
        result = res.get("result", "fetch_failed")
        note = NOTES.get(result, result)
        if res.get("live") == "fetch_failed":
            note = "live refetch failed; result from the cached copy" + (f" fetched {res.get('fetched_at')}" if res.get("fetched_at") else "")
        if res.get("text") is not None:
            pages[fid] = (res["text"], res)
        entry = {"finding_id": fid, "quote_check": result, "independent_sources": 1,
                 "live": res.get("live"), "fetched_at": res.get("fetched_at"),
                 "note": f"{note}; source_kind {row.get('source_kind')}"}
        entry.update(page_date(res, row))
        return fid, entry

    with ThreadPoolExecutor(max_workers=workers) as pool:
        checked = dict(pool.map(one, ids))
    decisive = []
    for c in claims:
        good = [fid for fid in c.get("finding_ids") or [] if checked.get(fid, {}).get("quote_check") == "found"]
        domains = {_domain(findings[f].get("url")) for f in good}
        primary = any(findings[f].get("source_kind") in PRIMARY for f in good)
        verdict = "holds" if len(domains) >= 2 or primary else "weak" if good else "fails"
        decisive.append({"claim": c.get("claim", ""), "code": c.get("code"), "finding_ids": c.get("finding_ids") or [],
                         "independent_sources": len(domains), "verdict": verdict})
    try:
        with open(os.path.join(run_dir, "card.json")) as f:
            plan = {str(p.get("language", "")).lower() for p in json.load(f).get("language_plan") or []}
    except (OSError, ValueError):
        plan = set()
    missing = sorted(plan - _languages_searched(run_dir) - {""})
    fails = sum(1 for d in decisive if d["verdict"] == "fails")
    status = "fail" if decisive and fails * 2 > len(decisive) else "partial" if fails or missing or any(d["verdict"] == "weak" for d in decisive) else "pass"
    audit = {"mode": "recheck", "checked": list(checked.values()), "decisive_claims": decisive,
             "language_plan_met": not missing, "missing_languages": missing, "returns": [], "status": status}
    with open(os.path.join(run_dir, "audit.json"), "w") as f:
        json.dump(audit, f, indent=1)
    if windows:
        build_windows(run_dir, findings, claims, pages=pages, page=lambda url: (None, None))
    return audit
