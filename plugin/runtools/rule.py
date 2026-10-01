import re
from urllib.parse import urlparse

STRONG = {"KP1", "KP2", "KP3", "KP4", "KP5", "KP6", "KP7", "KP9", "KP13", "KP14", "KP15", "KP16"}
SUPPORTING = {"KP8", "KP10", "KP11", "KP12", "KP17", "KP18"}
ALL_PATTERNS = STRONG | SUPPORTING
CORE = {"KP1", "KP2", "KP4", "KP5", "KP6", "KP13", "KP14", "KP15", "KP16"}
PULL = {"AS1", "AS2", "AS3"}
SIGNALS = {"AS1", "AS2", "AS3", "AS4", "AS5", "AS6", "AS7"}
CARD_BASIS = {"KP9", "KP10"}
NUMERIC = {"KP4", "KP9", "KP15", "KP16"}
NEEDS_INPUTS_BELOW = {"KP9", "KP15", "KP16"}
ALIVE_ASSESSED = ("KP2", "KP3", "KP6", "KP9")
KP9_BAND = 0.2
VERDICTS = {"DEAD", "ALIVE", "INSUFFICIENT_DATA"}
REBUTTALS = {
    "KP1": {"AS3", "AS6", "AS7"},
    "KP2": {"AS1", "AS3"},
    "KP3": {"AS4"},
    "KP4": {"AS5", "AS6"},
    "KP5": {"AS6", "AS7"},
    "KP6": {"AS1", "AS2"},
    "KP7": set(),
    "KP9": set(),
    "KP13": {"AS2"},
    "KP14": {"AS3"},
    "KP15": {"AS5", "AS6"},
    "KP16": {"AS5", "AS6"},
}
AUDIT_RANK = {"holds": 3, "weak": 2, "fails": 1}
SELLER = {"seller", "founders"}
UNAVOIDABLE_GATES = {"customs", "accreditation", "payment_system", "licence_register"}
SUPPORT_DROP = {"does_not_support", "truncated_qualifier"}
RULES_VERSION = "v4"
SUPPORT_RULES_VERSION = "v4"


def _verified(fid, findings, bad=frozenset()):
    row = findings.get(fid)
    return bool(row) and fid not in bad and row.get("opened") is True and row.get("quote_check") == "found"


def confirmed(entry, findings, code_key="code", bad=frozenset()):
    if entry.get("basis") == "card":
        return entry.get(code_key) in CARD_BASIS and bool(entry.get("argument"))
    return any(_verified(fid, findings, bad) for fid in entry.get("finding_ids") or [])


ARCHIVE = re.compile(r"^https?://(?:web\.)?archive\.org/web/[^/]+/(.+)$")


def _domain(url):
    m = ARCHIVE.match(url or "")
    if m:
        inner = m.group(1)
        url = inner if "://" in inner else "http://" + inner
    host = urlparse(url or "").netloc.lower()
    host = host.split(":")[0]
    return host[4:] if host.startswith("www.") else host


def _audit_bad_findings(audit):
    if not isinstance(audit, dict):
        return frozenset()
    return frozenset(c.get("finding_id") for c in audit.get("checked") or []
                     if isinstance(c, dict) and c.get("quote_check") in ("not_found", "fetch_failed", "gone"))


def support_mode(ctx):
    if not ctx:
        return None
    support = ctx.get("support")
    run = ctx.get("run") if isinstance(ctx.get("run"), dict) else {}
    if support is None and str(run.get("rules_version") or "") < SUPPORT_RULES_VERSION:
        return None
    return support or {}


def _label(support, code, fid):
    entry = support.get((code, fid)) if support else None
    return entry.get("label") if isinstance(entry, dict) else None


def split_by_support(code, fids, support, findings, bad=frozenset()):
    kept, removed, full, partial, unchecked = [], [], [], [], []
    for fid in fids or []:
        label = _label(support, code, fid)
        if label in SUPPORT_DROP:
            entry = support.get((code, fid)) or {}
            removed.append({"code": code, "finding_id": fid, "label": label, "reason": entry.get("reason") or ""})
            continue
        kept.append(fid)
        if not _verified(fid, findings, bad):
            continue
        if label == "supports":
            full.append(fid)
        elif label == "partial":
            partial.append(fid)
        else:
            unchecked.append(fid)
    return kept, removed, full, partial, unchecked


def audit_status(code, audit):
    if not isinstance(audit, dict):
        return None
    best = None
    for c in audit.get("decisive_claims") or []:
        if not isinstance(c, dict) or c.get("code") != code:
            continue
        v = c.get("verdict")
        if v in AUDIT_RANK and (best is None or AUDIT_RANK[v] > AUDIT_RANK[best]):
            best = v
    return best or "unaudited"


def constraint_class(c, findings):
    if not isinstance(c, dict):
        return "unknown"
    if c.get("read") in ("headings", "none") or not any(_verified(f, findings) for f in c.get("finding_ids") or []):
        return "unknown"
    if c.get("sanction") == "criminal" and c.get("on_whom") in SELLER:
        return "binding"
    money_routes = [r for r in c.get("open_routes") or [] if isinstance(r, dict) and r.get("money_seen") is True
                    and r.get("lawful_for_seller") is not False
                    and any(_verified(f, findings) for f in r.get("finding_ids") or [])]
    if c.get("channel_scope") == "one_channel" and money_routes:
        return "nominal"
    enforced = c.get("enforcement") == "seen" and any(_verified(f, findings) for f in c.get("enforcement_ids") or [])
    if c.get("on_whom") in SELLER and enforced:
        return "binding"
    if c.get("gate") in UNAVOIDABLE_GATES and c.get("channel_scope") == "all" and not money_routes:
        return "binding"
    return "conditional"


def constraint_classes(law, findings):
    out = {}
    for i, c in enumerate((law or {}).get("constraints") or [] if isinstance(law, dict) else []):
        if isinstance(c, dict):
            out[str(c.get("id") or f"C{i + 1}")] = (constraint_class(c, findings), c)
    return out


def _legacy_law_unknown(law):
    if not isinstance(law, dict):
        return False
    js = [j for j in law.get("jurisdictions") or [] if isinstance(j, dict)]
    if not js:
        return False
    for j in js:
        status = j.get("status")
        obtainable = (j.get("licence") or {}).get("obtainable") if isinstance(j.get("licence"), dict) else None
        if status == "unknown":
            continue
        if status == "licence_needed" and obtainable in (None, "unknown", ""):
            continue
        return False
    return True


def _kp7_state(p, classes, findings, law):
    ids = [str(i) for i in p.get("constraint_ids") or []]
    if not ids:
        if _legacy_law_unknown(law):
            return False, "KP7 rests on a norm whose status or obtainability is unknown in every jurisdiction"
        return True, None
    cited = [classes.get(i) for i in ids]
    cited = [c for c in cited if c]
    if not cited:
        return False, "KP7 cites constraint ids that law.json does not hold"
    binding = [c for cls, c in cited if cls == "binding"]
    conditional = [c for cls, c in cited if cls == "conditional"
                   and any(_verified(f, findings) for f in c.get("condition_unmet_ids") or [])]
    if p.get("threshold_met"):
        if any(c.get("channel_scope") == "all" for c in binding):
            return True, None
        if binding or conditional:
            return True, "below"
        return False, "KP7 at threshold needs a binding constraint over all channels"
    if binding or conditional:
        return True, None
    kinds = sorted({cls for cls, _ in cited})
    return False, f"KP7 rests only on {'/'.join(kinds)} constraints"


def _price_route(verdict, findings, bad=frozenset()):
    return any(p.get("code") == "KP4" and p.get("fired") and p.get("price_route") and confirmed(p, findings, bad=bad)
               for p in verdict.get("patterns") or [])


def _human_substitute(verdict, findings, bad=frozenset()):
    return any(p.get("code") == "KP14" and p.get("fired") and confirmed(p, findings, bad=bad)
               for p in verdict.get("patterns") or [])


def _void_as1(entry, price_route, human):
    if price_route or entry.get("pain_in_substitute") is True:
        return True
    return human and entry.get("substitute") == "human"


def signal_codes(verdict, findings, audit=None, support=None, removed=None, partial_out=None):
    out = {}
    bad = _audit_bad_findings(audit)
    price_route = _price_route(verdict, findings, bad)
    human = _human_substitute(verdict, findings, bad)
    for s in verdict.get("alive_signals") or []:
        code = s.get("code")
        if code == "AS1" and _void_as1(s, price_route, human):
            continue
        if audit is not None and audit_status(code, audit) == "fails":
            continue
        if code not in SIGNALS:
            continue
        if support is not None:
            kept, gone, full, partial, unchecked = split_by_support(code, s.get("finding_ids"), support, findings, bad)
            if removed is not None:
                removed.extend(gone)
            if full:
                out.setdefault(code, []).append({**s, "finding_ids": full})
            elif (partial or unchecked) and partial_out is not None:
                partial_out.setdefault(code, []).append({**s, "finding_ids": partial + unchecked, "_unchecked": not partial})
            continue
        if confirmed(s, findings, bad=bad):
            out.setdefault(code, []).append(s)
    return out


def _spending_seen(verdict, findings, bad):
    return any(s.get("code") == "AS1" and confirmed(s, findings, bad=bad) for s in verdict.get("alive_signals") or [])


def _sites(entries, findings):
    return {_domain(findings[f].get("url")) for s in entries for f in s.get("finding_ids") or []
            if _verified(f, findings)}


def fired_patterns(verdict, findings, ctx=None):
    strict = ctx is not None
    ctx = ctx or {}
    audit = ctx.get("audit")
    bad = _audit_bad_findings(audit)
    law = ctx.get("law")
    classes = constraint_classes(law, findings)
    weak_rule_ids = {f for cls, c in classes.values() if cls in ("nominal", "unknown") for f in c.get("finding_ids") or []}
    spending = _spending_seen(verdict, findings, bad)
    support = support_mode(ctx)
    out, dropped = [], []
    for p in verdict.get("patterns") or []:
        code = p.get("code")
        if code not in ALL_PATTERNS or not p.get("fired"):
            continue
        entry = dict(p)
        if code == "KP6" and weak_rule_ids:
            kept = [f for f in entry.get("finding_ids") or [] if f not in weak_rule_ids]
            if len(kept) != len(entry.get("finding_ids") or []):
                entry["finding_ids"] = kept
                entry["_rule_trimmed"] = True
        if support is not None and entry.get("basis") != "card":
            kept, removed, full, partial, _ = split_by_support(code, entry.get("finding_ids"), support, findings, bad)
            if removed:
                entry["finding_ids"] = kept
                entry["_support_removed"] = removed
            entry["_supported_ids"] = full
            entry["_partial_ids"] = partial
        if not confirmed(entry, findings, bad=bad):
            reason = "KP6 rested only on a nominal or unknown rule" if entry.get("_rule_trimmed") else "no verified finding"
            if entry.get("_support_removed"):
                reason = "support check: no cited finding supports the claim"
            dropped.append({"code": code, "reason": reason})
            continue
        strong_at_threshold = code in STRONG and bool(entry.get("threshold_met"))
        if entry.get("airbnb") == "dropped" and not strong_at_threshold:
            continue
        if audit is not None and audit_status(code, audit) == "fails" and entry.get("basis") != "card":
            dropped.append({"code": code, "reason": "audit marks its claim fails"})
            continue
        if code == "KP7" and strict:
            keep, note = _kp7_state(entry, classes, findings, law)
            if not keep:
                dropped.append({"code": code, "reason": note})
                continue
            if note == "below":
                entry["threshold_met"] = False
        if code == "KP8" and spending:
            dropped.append({"code": code, "reason": "a confirmed AS1 shows spending on a workaround, which refutes KP8"})
            continue
        out.append(entry)
    return out, dropped


def strong_signals(signals):
    out = set()
    for code, entries in signals.items():
        if code == "AS1" and not any(s.get("price_checked") for s in entries):
            continue
        out.add(code)
    return out


def valid_rebuttals(pattern, signals):
    if pattern.get("code") in ("KP4", "KP15") and pattern.get("unfixable"):
        return []
    allowed = REBUTTALS.get(pattern.get("code"), set())
    usable = strong_signals(signals)
    return sorted(c for c in (pattern.get("rebutted_by") or []) if c in allowed and c in usable)


def _num(x):
    return x if isinstance(x, (int, float)) and not isinstance(x, bool) else None


def _count_block(p, audit):
    code = p["code"]
    if p.get("basis") == "card":
        return "rests on the card, not on findings"
    if p.get("inputs") == "assumption":
        return "a deciding input is an assumption"
    if code == "KP9":
        if p.get("inputs") != "findings":
            return "ceiling inputs not marked as findings"
        value, threshold = _num(p.get("value_usd")), _num(p.get("threshold_usd"))
        if value is None or not threshold:
            return "ceiling value or threshold missing"
        if value >= threshold * (1 - KP9_BAND):
            return f"ceiling {value:g} within {int(KP9_BAND * 100)}% of the threshold {threshold:g}"
    elif code in NEEDS_INPUTS_BELOW and not p.get("threshold_met") and p.get("inputs") != "findings":
        return "below-threshold form rests on an assumed input"
    if "_supported_ids" in p and not p["_supported_ids"]:
        return "support check: the quotes only partly support the claim" if p.get("_partial_ids") else "support check: no support label"
    if audit is not None:
        status = audit_status(code, audit)
        if status != "holds":
            return f"audit status {status}"
    return None


def _support(p, findings, bad):
    out = []
    ids = p["_supported_ids"] if "_supported_ids" in p else p.get("finding_ids") or []
    for fid in ids:
        if _verified(fid, findings, bad) and findings[fid].get("label") != "assumption":
            out.append((fid, _domain(findings[fid].get("url")) or fid))
    return out


def _units(counted):
    codes = {p["code"] for p in counted}
    units = []
    merged = {"KP4", "KP6"} <= codes
    for p in counted:
        if merged and p["code"] == "KP6":
            continue
        if merged and p["code"] == "KP4":
            other = next(q for q in counted if q["code"] == "KP6")
            units.append({"codes": ["KP4", "KP6"], "patterns": [p, other]})
        else:
            units.append({"codes": [p["code"]], "patterns": [p]})
    return units


def _match(units, options, fixed=None):
    owner = {}
    chosen = {}
    if fixed:
        u, dom, fid = fixed
        owner[dom] = u
        chosen[u] = (dom, fid)

    def augment(u, seen):
        for dom, fid in options[u]:
            if dom in seen:
                continue
            seen.add(dom)
            if fixed and dom == fixed[1]:
                continue
            if dom not in owner or augment(owner[dom], seen):
                owner[dom] = u
                chosen[u] = (dom, fid)
                return True
        return False

    for u in range(len(units)):
        if fixed and u == fixed[0]:
            continue
        augment(u, set())
    return {u: chosen[u] for u in chosen if owner.get(chosen[u][0]) == u}


def independent_units(counted, findings, bad=frozenset()):
    units = _units(counted)
    options = []
    for unit in units:
        opts, seen = [], set()
        for p in unit["patterns"]:
            for fid, dom in _support(p, findings, bad):
                if dom not in seen:
                    seen.add(dom)
                    opts.append((dom, fid))
        options.append(opts)
    best = _match(units, options)
    core_units = [i for i, u in enumerate(units) if CORE & set(u["codes"])]
    if not any(i in best for i in core_units):
        trials = [_match(units, options, fixed=(i, dom, fid)) for i in core_units for dom, fid in options[i]]
        trials = [t for t in trials if any(i in t for i in core_units)]
        if trials:
            top = max(trials, key=len)
            if len(top) >= len(best) or len(top) >= 3:
                best = top
    return [(units[i]["codes"], best[i][1]) for i in sorted(best)]


def _judge_dispute(result, judge):
    if not isinstance(judge, dict) or result["verdict"] != "DEAD":
        return result
    opinion = judge.get("verdict_opinion")
    if opinion not in VERDICTS or opinion == "DEAD":
        return result
    return {**result, "verdict": "INSUFFICIENT_DATA", "rule": "J1", "disputed": True,
            "sheet_verdict": "DEAD", "sheet_rule": result["rule"],
            "to_collect": result["to_collect"] + [{"code": "judge", "reason": f"judge disputes the DEAD sheet ({opinion})"}]}


def _alive_gates(verdict, ctx):
    if not ctx:
        return []
    gates = []
    kc = ctx.get("killcheck")
    if not (isinstance(kc, dict) and isinstance(kc.get("causes"), list) and kc["causes"]):
        gates.append("kill check has not run")
    sheet = {p.get("code"): p for p in verdict.get("patterns") or []}
    for code in ALIVE_ASSESSED:
        p = sheet.get(code)
        if not p or not str(p.get("argument") or "").strip():
            gates.append(f"{code} not assessed")
        elif p.get("unknown") is True:
            gates.append(f"{code} unknown")
    q3 = ctx.get("q3")
    if not isinstance(q3, dict):
        gates.append("competitors unmeasured")
    elif q3.get("invisible_player_risk") == "high":
        gates.append("competitors unknown (invisible_player_risk high)")
    return gates


def decide(verdict, findings, ctx=None):
    audit = (ctx or {}).get("audit") if ctx else None
    if ctx is not None and audit is None:
        audit = {}
    bad = _audit_bad_findings(audit)
    support = support_mode(ctx)
    removed, partial_signals = [], {}
    signals = signal_codes(verdict, findings, audit if ctx is not None else None, support, removed, partial_signals)
    blocking = {code: signals.get(code, []) + partial_signals.get(code, []) for code in set(signals) | set(partial_signals)}
    fired, dropped = fired_patterns(verdict, findings, ctx)
    for p in fired:
        removed.extend(p.get("_support_removed") or [])
    for p in verdict.get("patterns") or []:
        if p.get("fired") and p.get("code") not in {q["code"] for q in fired} and support is not None and p.get("basis") != "card":
            removed.extend(split_by_support(p.get("code"), p.get("finding_ids"), support, findings, bad)[1])
    fired_codes = sorted({p["code"] for p in fired})
    counted, to_collect = [], list(dropped)
    for p in fired:
        block = _count_block(p, audit if ctx is not None else None)
        if block:
            to_collect.append({"code": p["code"], "reason": block})
        else:
            counted.append(p)
    seen, support_dropped = set(), []
    for r in removed:
        key = (r["code"], r["finding_id"])
        if key not in seen:
            seen.add(key)
            support_dropped.append(r)
    for code in sorted(set(partial_signals) - set(signals)):
        unchecked = all(e.get("_unchecked") for e in partial_signals[code])
        to_collect.append({"code": code, "reason": "support check: no support label" if unchecked else "support check: the quotes only partly support the signal"})
    base = {"fired": fired_codes, "counted": sorted({p["code"] for p in counted}),
            "signals": sorted(signals), "to_collect": to_collect, "disputed": False,
            "support_checked": support is not None, "support_dropped": support_dropped}
    judge = (ctx or {}).get("judge")
    killers = [p["code"] for p in counted
               if p["code"] in STRONG and p.get("threshold_met") and not valid_rebuttals(p, blocking)]
    if killers:
        return _judge_dispute({**base, "verdict": "DEAD", "rule": "D1", "decisive": sorted(set(killers))}, judge)
    counted_codes = {p["code"] for p in counted}
    unshielded = any(p["code"] == "KP15" and p.get("threshold_met") for p in counted) or "KP18" in counted_codes
    shields = set() if unshielded else {"AS1", "AS2"} & strong_signals(blocking)
    independent = independent_units(counted, findings, bad)
    base["independent"] = [{"codes": codes, "finding_id": fid} for codes, fid in independent]
    unit_codes = [set(codes) for codes, _ in independent]
    if len(unit_codes) >= 3 and any(CORE & c for c in unit_codes) and not shields:
        decisive = sorted({c for codes in unit_codes for c in codes})
        return _judge_dispute({**base, "verdict": "DEAD", "rule": "D2", "decisive": decisive}, judge)
    pulls = {c for c in PULL & set(signals) if c != "AS1" or any(s.get("price_checked") for s in signals[c])}
    multi_site = any(len(_sites(signals[code], findings)) >= 2 for code in pulls & {"AS1", "AS3"})
    numbered = multi_site or any(s.get("number") not in (None, "", "null") for code in pulls for s in signals[code])
    corroborated = len(signals) >= 2 or multi_site
    limit = 2 if len(pulls) >= 2 else 1
    priced = any(s.get("price_checked") for s in signals.get("AS1", []))
    price_risk = "KP4" in fired_codes and not priced
    law_block = any(p["code"] == "KP7" and not p.get("clear_market") for p in fired)
    count = [c for c in fired_codes if not (c == "KP7" and not law_block)]
    gates = _alive_gates(verdict, ctx)
    if "KP9" in fired_codes and "KP9" not in base["counted"]:
        gates.append("KP9 ceiling unresolved")
    base["alive_gates"] = gates
    if pulls and numbered and corroborated and len(count) <= limit and not law_block and not price_risk and not gates:
        return {**base, "verdict": "ALIVE", "rule": "A1", "decisive": sorted(signals)}
    return {**base, "verdict": "INSUFFICIENT_DATA", "rule": "I1", "decisive": []}
