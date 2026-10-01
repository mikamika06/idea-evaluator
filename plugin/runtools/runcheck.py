import json
import os

from runtools.pagetext import cached_text, cut_qualifier
from runtools.rule import ALL_PATTERNS, audit_status, constraint_classes, decide
from runtools.runctx import load_context
from runtools.support import CHECKS, WINDOWS, check_support

VERDICTS = {"DEAD", "ALIVE", "INSUFFICIENT_DATA"}
SUBSTITUTES = {"tool", "service", "human"}
CAUSE_STATUS = {"supported", "refuted", "not_found"}
P_VALUES = {0.1, 0.3, 0.5, 0.7, 0.9}
INPUTS = {"findings", "assumption"}
NUMERIC_PATTERNS = ("KP4", "KP9", "KP15", "KP16")
SHEET_FIELDS = ("fired", "threshold_met", "finding_ids", "rebutted_by", "price_route", "unfixable", "clear_market",
                "basis", "inputs", "value_usd", "threshold_usd", "unknown", "constraint_ids", "airbnb")
SIGNAL_FIELDS = ("finding_ids", "price_checked", "number", "substitute", "pain_in_substitute")
CONSTRAINT_ENUMS = {
    "read": {"full", "headings", "none"},
    "binds": {"seller", "product", "buyer_channel", "data_handling", "marketing", "founders"},
    "on_whom": {"seller", "founders", "buyer", "donor", "nobody"},
    "sanction": {"criminal", "administrative", "payment_refused", "contract_void", "none_found"},
    "enforcement": {"seen", "none_found", "not_searched"},
    "gate": {"customs", "accreditation", "payment_system", "licence_register", "none"},
    "channel_scope": {"all", "one_channel"},
}
QUESTIONS = [f"q{i}.json" for i in range(1, 8)]
PASS1 = ["card.json", "dossier.json", "law.json"] + QUESTIONS
STAGES = [
    ("intake", ["run.json", "card.json"]),
    ("pass1", PASS1),
    ("merge", ["findings.jsonl"]),
    ("reconcile", ["reconcile.json"]),
    ("killcheck", ["killcheck.json"]),
    ("audit", ["audit.json"]),
    ("support", [WINDOWS, CHECKS]),
    ("verdict", ["verdict.json"]),
    ("judge", ["judge.json"]),
    ("report", ["report.md"]),
]


def _load_json(path):
    with open(path) as f:
        return json.load(f)


def _findings(run_dir):
    out = {}
    path = os.path.join(run_dir, "findings.jsonl")
    if not os.path.exists(path):
        return out
    with open(path, errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if isinstance(row, dict) and row.get("finding_id"):
                out[row["finding_id"]] = row
    return out


def _check_price(v, run_dir):
    try:
        q6 = _load_json(os.path.join(run_dir, "q6.json"))
    except (OSError, ValueError):
        return []
    ratio = q6.get("price_vs_current_cost") if isinstance(q6, dict) else None
    if not isinstance(ratio, (int, float)) or v.get("price_override"):
        return []
    limit = 3.0 if q6.get("consumer_impulse") is True else 1.5
    errors = []
    kp4 = next((p for p in v.get("patterns") or [] if p.get("code") == "KP4"), {})
    if ratio > limit and not (kp4.get("fired") and kp4.get("price_route")):
        errors.append(f"verdict.json: q6 price_vs_current_cost {ratio} > {limit} but KP4 is not fired with price_route; fire it or write price_override with a cited reason")
    if ratio <= limit and any(s.get("code") == "AS1" and not s.get("price_checked") for s in v.get("alive_signals") or []):
        errors.append(f"verdict.json: q6 price_vs_current_cost {ratio} <= {limit} but AS1 has price_checked false; set it or write price_override with a cited reason")
    return errors


def _check_substitutes(v, run_dir):
    errors = []
    try:
        dossier = _load_json(os.path.join(run_dir, "dossier.json"))
    except (OSError, ValueError):
        dossier = {}
    ndb = dossier.get("needed_but_different") if isinstance(dossier, dict) else None
    applies = isinstance(ndb, dict) and ndb.get("applies") is True
    for s in v.get("alive_signals") or []:
        if s.get("code") != "AS1":
            continue
        if s.get("substitute") not in SUBSTITUTES:
            errors.append(f"verdict.json: AS1 substitute {s.get('substitute')!r} not in {sorted(SUBSTITUTES)}")
        if applies and not isinstance(s.get("pain_in_substitute"), bool):
            errors.append("verdict.json: dossier needed_but_different applies; AS1 needs pain_in_substitute true or false")
    return errors


def _check_law(v, run_dir):
    kp7 = next((p for p in v.get("patterns") or [] if p.get("code") == "KP7"), {})
    if not (kp7.get("fired") and kp7.get("clear_market")):
        return []
    try:
        law = _load_json(os.path.join(run_dir, "law.json"))
    except (OSError, ValueError):
        law = {}
    places = [j.get("place") for j in (law.get("jurisdictions") or []) if isinstance(j, dict) and j.get("status") == "allowed"]
    if kp7.get("clear_market") not in places:
        return [f"verdict.json: KP7 clear_market {kp7.get('clear_market')!r} is not a place with status allowed in law.json"]
    if kp7.get("threshold_met"):
        return ["verdict.json: KP7 cannot meet its threshold while clear_market names an allowed market"]
    return []


def _check_sheet(v, findings, run_dir="."):
    errors = []
    patterns = v.get("patterns") or []
    codes = {p.get("code") for p in patterns}
    missing = sorted(ALL_PATTERNS - codes, key=lambda c: int(c[2:]))
    if missing:
        errors.append("verdict.json: pattern sheet lacks " + ", ".join(missing))
    for entry in [e for e in patterns if e.get("fired")] + list(v.get("alive_signals") or []):
        for fid in entry.get("finding_ids") or []:
            if fid not in findings:
                errors.append(f"verdict.json: {entry.get('code')} cites unknown finding {fid}")
    errors += _check_price(v, run_dir)
    errors += _check_substitutes(v, run_dir)
    errors += _check_law(v, run_dir)
    expected = decide(v, findings, load_context(run_dir))
    if v.get("verdict") in VERDICTS and v.get("verdict") != expected["verdict"]:
        errors.append(f"verdict.json: verdict {v.get('verdict')} but the pattern sheet gives {expected['verdict']} (rule {expected['rule']}); fix the sheet or the verdict")
    elif v.get("rule_fired") != expected["rule"]:
        errors.append(f"verdict.json: rule_fired {v.get('rule_fired')!r} but the pattern sheet gives {expected['rule']}")
    if expected.get("disputed") and v.get("disputed") is not True:
        errors.append("verdict.json: the judge disputes the DEAD sheet (rule J1); set disputed true and name the dispute in the report")
    p = v.get("p_survive")
    if v.get("verdict") == "DEAD" and p is not None and p > 0.1:
        errors.append("verdict.json: DEAD caps p_survive at 0.1")
    if v.get("verdict") == "ALIVE" and p is not None and p < 0.5:
        errors.append("verdict.json: ALIVE needs p_survive of at least 0.5")
    if v.get("verdict") == "INSUFFICIENT_DATA" and not v.get("to_collect"):
        errors.append("verdict.json: INSUFFICIENT_DATA without to_collect")
    return errors


def _sheet_diff(before, after):
    diffs = []
    bp = {p.get("code"): p for p in before.get("patterns") or [] if isinstance(p, dict)}
    ap = {p.get("code"): p for p in after.get("patterns") or [] if isinstance(p, dict)}
    for code in sorted(set(bp) | set(ap), key=str):
        for field in SHEET_FIELDS:
            if (bp.get(code) or {}).get(field) != (ap.get(code) or {}).get(field):
                diffs.append((code, field))

    def signals(v):
        out = {}
        for s in v.get("alive_signals") or []:
            if isinstance(s, dict):
                out.setdefault(s.get("code"), []).append({k: s.get(k) for k in SIGNAL_FIELDS})
        return out

    bs, as_ = signals(before), signals(after)
    for code in sorted(set(bs) | set(as_), key=str):
        if bs.get(code) != as_.get(code):
            diffs.append((code, "signal"))
    return diffs


def _check_judge_changes(v, run_dir):
    jpath = os.path.join(run_dir, "judge.json")
    if not os.path.exists(jpath):
        return []
    try:
        judge = _load_json(jpath)
    except ValueError:
        return []
    errors = []
    if not isinstance(judge.get("agrees"), bool) or judge.get("verdict_opinion") not in VERDICTS:
        errors.append("judge.json: the judge must read verdict.prejudge.json and set agrees true or false with a verdict_opinion")
    ppath = os.path.join(run_dir, "verdict.prejudge.json")
    if not os.path.exists(ppath):
        return errors + ["verdict.prejudge.json missing: snapshot verdict.json before dispatching the judge"]
    try:
        before = _load_json(ppath)
    except ValueError:
        return errors + ["verdict.prejudge.json: invalid JSON"]
    diffs = _sheet_diff(before, v)
    if not diffs:
        return errors
    try:
        log = _load_json(os.path.join(run_dir, "sheet-changes.json"))
    except (OSError, ValueError):
        log = {}
    changes = log.get("changes") if isinstance(log, dict) else None
    changes = [c for c in changes or [] if isinstance(c, dict)]
    judge_errors = judge.get("rule_table_errors") or []
    for code, field in diffs:
        match = [c for c in changes if c.get("code") == code and c.get("field") == field]
        if not match:
            errors.append(f"sheet-changes.json: {code} {field} changed after the judge without a logged change")
            continue
        for c in match:
            idx = c.get("judge_error")
            if not (isinstance(idx, int) and 0 <= idx < len(judge_errors)):
                errors.append(f"sheet-changes.json: {code} {field} change must cite a judge rule_table_errors index")
            if not str(c.get("reason") or "").strip():
                errors.append(f"sheet-changes.json: {code} {field} change needs a reason")
    return errors


def _check_quotes(v, findings, law, run_dir):
    targets = {}
    for p in v.get("patterns") or []:
        if p.get("code") in ("KP6", "KP7") and p.get("fired"):
            read = p.get("qualifier_read") or {}
            for fid in p.get("finding_ids") or []:
                targets.setdefault(fid, []).append((p.get("code"), read))
    for c in (law or {}).get("constraints") or []:
        if isinstance(c, dict):
            read = c.get("qualifier_read") or {}
            for fid in c.get("finding_ids") or []:
                targets.setdefault(fid, []).append((f"constraint {c.get('id')}", read))
    errors = []
    for fid, users in sorted(targets.items()):
        row = findings.get(fid)
        if not row or row.get("quote_check") != "found":
            continue
        text = cached_text(row.get("url"))
        clause = cut_qualifier(row.get("quote_original") or row.get("quote") or "", text) if text else None
        if not clause:
            continue
        for who, read in users:
            if fid not in read:
                errors.append(f"{fid}: quote cited by {who} stops before a qualifying clause ('{clause}'); cite a finding with the whole sentence or write qualifier_read.{fid} with why the clause does not change the argument")
    return errors


def _check_v3(v, findings, run_dir, header):
    errors = []
    patterns = {p.get("code"): p for p in v.get("patterns") or [] if isinstance(p, dict)}
    for code in NUMERIC_PATTERNS:
        p = patterns.get(code) or {}
        if p.get("fired") and p.get("inputs") not in INPUTS:
            errors.append(f"verdict.json: fired {code} needs inputs findings or assumption")
    kp9 = patterns.get("KP9") or {}
    if kp9.get("fired") and not (isinstance(kp9.get("value_usd"), (int, float)) and isinstance(kp9.get("threshold_usd"), (int, float))):
        errors.append("verdict.json: fired KP9 needs value_usd and threshold_usd")
    if not kp9.get("fired") and not isinstance(kp9.get("value_usd"), (int, float)) and kp9.get("unknown") is not True:
        errors.append("verdict.json: KP9 needs value_usd (the computed ceiling) or unknown true")
    ctx = load_context(run_dir)
    audit = ctx.get("audit") or {}
    for p in v.get("patterns") or []:
        if p.get("fired") and p.get("basis") != "card" and audit_status(p.get("code"), audit) == "unaudited":
            errors.append(f"audit.json: fired {p.get('code')} has no decisive claim with its code; add it to claims.json and rerun recheck")
    for s in v.get("alive_signals") or []:
        if audit_status(s.get("code"), audit) == "unaudited":
            errors.append(f"audit.json: {s.get('code')} has no decisive claim with its code")
    law = ctx.get("law") or {}
    classes = constraint_classes(law, findings)
    for i, c in enumerate(law.get("constraints") or []):
        if not isinstance(c, dict):
            errors.append(f"law.json: constraint {i + 1} is not an object")
            continue
        for key, allowed in CONSTRAINT_ENUMS.items():
            if c.get(key) not in allowed:
                errors.append(f"law.json: constraint {c.get('id') or i + 1} {key} {c.get(key)!r} not in {sorted(allowed)}")
        if not isinstance(c.get("open_routes"), list):
            errors.append(f"law.json: constraint {c.get('id') or i + 1} needs open_routes (empty list when none was found)")
    kp7 = patterns.get("KP7") or {}
    if kp7.get("fired"):
        ids = [str(x) for x in kp7.get("constraint_ids") or []]
        if not ids:
            errors.append("verdict.json: fired KP7 needs constraint_ids naming law.json constraints")
        for cid in ids:
            if cid not in classes:
                errors.append(f"verdict.json: KP7 cites constraint {cid} that law.json does not hold")
    if header.get("early_exit") is not True and v.get("rule_fired") != "D1" and not os.path.exists(os.path.join(run_dir, "killcheck.json")):
        errors.append("killcheck.json missing: the kill check runs for every verdict except D1 and early exit")
    errors += _check_judge_changes(v, run_dir)
    errors += _check_quotes(v, findings, law, run_dir)
    return errors


def _check_v4(v, findings, run_dir):
    errors = check_support(v, run_dir)
    if errors:
        return errors
    expected = decide(v, findings, load_context(run_dir))
    dropped = expected.get("support_dropped") or []
    if dropped and not v.get("support_dropped"):
        errors.append("verdict.json: support_dropped missing; copy it from bin/decide")
    rpath = os.path.join(run_dir, "report.md")
    if dropped and os.path.exists(rpath):
        with open(rpath, errors="ignore") as f:
            report = f.read()
        for d in dropped:
            if d["finding_id"] not in report:
                errors.append(f"report.md: {d['code']} {d['finding_id']} was dropped by the support check ({d['label']}); list it with its reason under the limits")
    return errors


def _check_killcheck(run_dir, findings):
    path = os.path.join(run_dir, "killcheck.json")
    if not os.path.exists(path):
        return []
    try:
        kc = _load_json(path)
    except ValueError:
        return []
    if not isinstance(kc, dict) or not isinstance(kc.get("causes"), list):
        return ["killcheck.json: causes list missing"]
    errors = []
    for c in kc["causes"]:
        if not isinstance(c, dict):
            errors.append("killcheck.json: cause is not an object")
            continue
        if c.get("status") not in CAUSE_STATUS:
            errors.append(f"killcheck.json: {c.get('pattern')} status {c.get('status')!r} not in {sorted(CAUSE_STATUS)}")
        for fid in (c.get("finding_ids") or []) + (c.get("against_ids") or []):
            if fid not in findings:
                errors.append(f"killcheck.json: {c.get('pattern')} cites unknown finding {fid}")
    return errors


def check(run_dir):
    missing, errors = [], []
    header = {}
    try:
        header = _load_json(os.path.join(run_dir, "run.json"))
    except (OSError, ValueError):
        pass
    early = bool(header.get("early_exit"))
    next_stage = None
    for stage, files in STAGES:
        if stage == "reconcile" and early:
            continue
        if stage == "killcheck" and header.get("stage") != "deepen":
            continue
        if stage == "support" and str(header.get("rules_version") or "") < "v4":
            continue
        for name in files:
            p = os.path.join(run_dir, name)
            if not os.path.exists(p):
                missing.append(name)
                next_stage = next_stage or stage
                continue
            if name.endswith(".json"):
                try:
                    _load_json(p)
                except ValueError as e:
                    errors.append(f"{name}: invalid JSON ({e})")
                    next_stage = next_stage or stage
    findings = _findings(run_dir)
    vpath = os.path.join(run_dir, "verdict.json")
    if os.path.exists(vpath):
        try:
            v = _load_json(vpath)
        except ValueError:
            v = None
        if isinstance(v, dict):
            if v.get("verdict") not in VERDICTS:
                errors.append(f"verdict.json: verdict {v.get('verdict')!r} not in {sorted(VERDICTS)}")
            if v.get("p_survive") not in P_VALUES:
                errors.append(f"verdict.json: p_survive {v.get('p_survive')!r} not in {sorted(P_VALUES)}")
            if not v.get("p_survive_basis"):
                errors.append("verdict.json: p_survive_basis empty")
            errors += _check_sheet(v, findings, run_dir)
            if str(header.get("rules_version") or "") >= "v3":
                errors += _check_v3(v, findings, run_dir, header)
            if str(header.get("rules_version") or "") >= "v4":
                errors += _check_v4(v, findings, run_dir)
            cheapest = v.get("cheapest_test") or {}
            if not cheapest.get("threshold"):
                errors.append("verdict.json: cheapest_test.threshold empty")
    errors += _check_killcheck(run_dir, findings)
    rpath = os.path.join(run_dir, "report.md")
    if os.path.exists(rpath) and os.path.exists(vpath):
        with open(rpath, errors="ignore") as f:
            first = f.readline()
        try:
            verdict = _load_json(vpath).get("verdict", "")
        except ValueError:
            verdict = ""
        if verdict and verdict not in first:
            errors.append(f"report.md: first line does not state the verdict {verdict}")
    return {"run_dir": run_dir, "ok": not missing and not errors, "next_stage": next_stage, "missing": missing, "errors": errors, "early_exit": early}
