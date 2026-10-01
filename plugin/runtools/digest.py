import json
import os

from runtools.rule import constraint_classes
from runtools.runcheck import _findings

FILES = ["q1.json", "q2.json", "q3-competitors.json", "q3-graveyard.json", "q3.json", "q4.json",
         "q5.json", "q6.json", "q7.json", "law.json", "dossier.json", "killcheck.json"]


def _load(path):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def _ids(ids, findings):
    out = []
    for fid in ids or []:
        row = findings.get(fid)
        if row is None:
            mark = "?"
        elif row.get("opened") is True and row.get("quote_check") == "found":
            mark = "+"
        else:
            mark = "-"
        out.append(fid + mark)
    return ",".join(out)


def _cands(card, findings, key):
    lines = []
    for c in card.get(key) or []:
        if not isinstance(c, dict):
            continue
        extra = ""
        if key == "kill_candidates":
            extra = " threshold_met" if c.get("threshold_met") else " below_threshold"
        if c.get("number"):
            extra += f" number={c.get('number')}"
        lines.append(f"  {key[:-11]} {c.get('code')}{extra} [{_ids(c.get('finding_ids'), findings)}] {c.get('argument', '')}")
    return lines


def _specific(name, card, findings):
    out = []
    if name == "q1.json":
        out.append(f"  pain_intensity={card.get('pain_intensity')} segment={card.get('segment')}")
    elif name == "q2.json":
        for s in card.get("current_solutions") or []:
            out.append(f"  solution: {s.get('what')} | spend={s.get('spend')} | satisfaction={s.get('satisfaction')} [{_ids(s.get('finding_ids'), findings)}]")
        out.append(f"  non_consumption={card.get('non_consumption')}")
    elif name == "q3-competitors.json":
        for c in card.get("competitors") or []:
            out.append(f"  competitor: {c.get('name')} | {c.get('relation')} | alive={c.get('alive')} | {c.get('what', '')[:120]} [{_ids(c.get('used_evidence'), findings)}]")
        out.append(f"  invisible_player_risk={card.get('invisible_player_risk')}")
    elif name == "q3-graveyard.json":
        for d in card.get("dead_attempts") or []:
            out.append(f"  dead: {d.get('name')} {d.get('years')} | same_idea={d.get('same_idea')} | {d.get('cause_class')} | {d.get('cause', '')[:120]} [{_ids(d.get('finding_ids'), findings)}]")
        wc = card.get("what_changed") or {}
        out.append(f"  what_changed={wc.get('status')}")
        for c in wc.get("changes") or []:
            out.append(f"   change: {c.get('kind')} {c.get('what', '')[:120]} [{_ids(c.get('finding_ids'), findings)}]")
    elif name == "q4.json":
        payer = card.get("payer") or {}
        out.append(f"  payer_exists={card.get('payer_exists')} pays_today_for_similar={payer.get('pays_today_for_similar')} who={payer.get('who')} budget={payer.get('budget_line')} [{_ids(payer.get('finding_ids'), findings)}]")
    elif name == "q5.json":
        out.append(f"  reachable_within_budget={card.get('reachable_within_budget')}")
    elif name == "q6.json":
        out.append(f"  realistic_case_fails={card.get('realistic_case_fails')} optimistic_case_fails={card.get('optimistic_case_fails')} deciding_inputs_sourced={card.get('deciding_inputs_sourced')} price_vs_current_cost={card.get('price_vs_current_cost')}")
        out.append(f"  realistic={card.get('realistic')} optimistic={card.get('optimistic')} {card.get('currency')}")
    elif name == "q7.json":
        for w in card.get("why_now") or []:
            out.append(f"  why_now: {w.get('kind')} {w.get('change', '')[:120]} [{_ids(w.get('finding_ids'), findings)}]")
    elif name == "law.json":
        for j in card.get("jurisdictions") or []:
            lic = j.get("licence") or {}
            out.append(f"  law {j.get('place')}: {j.get('status')} | {j.get('rule', '')[:120]} | obtainable={lic.get('obtainable')} [{_ids(j.get('finding_ids'), findings)}]")
        for cid, (cls, c) in constraint_classes(card, findings).items():
            routes = ", ".join(f"{r.get('route')}{'$' if r.get('money_seen') else ''}" for r in c.get("open_routes") or [] if isinstance(r, dict))
            out.append(f"  constraint {cid} class={cls} | {str(c.get('norm', ''))[:100]} | on={c.get('on_whom')} sanction={c.get('sanction')} scope={c.get('channel_scope')} routes=[{routes}] [{_ids(c.get('finding_ids'), findings)}]")
        kc = card.get("kill_candidate")
        if kc:
            out.append(f"  kill KP7 threshold_met={kc.get('threshold_met')} [{_ids(kc.get('finding_ids'), findings)}] {kc.get('argument', '')}")
    elif name == "killcheck.json":
        for c in card.get("causes") or []:
            if isinstance(c, dict):
                out.append(f"  cause {c.get('pattern')} {c.get('status')}: {str(c.get('cause', ''))[:120]} for[{_ids(c.get('finding_ids'), findings)}] against[{_ids(c.get('against_ids'), findings)}] {str(c.get('argument', ''))[:200]}")
    elif name == "dossier.json":
        nbd = card.get("needed_but_different") or {}
        out.append(f"  need_label_suggestion={card.get('need_label_suggestion')} needed_but_different={nbd.get('applies')} {nbd.get('where_pain_actually_is', '')}")
        for a in card.get("aspects") or []:
            if any(k in str(a.get("aspect", "")).lower() for k in ("cope", "hurts", "need it", "money")):
                out.append(f"  aspect {a.get('aspect')}: {a.get('observation', '')[:160]} [{_ids(a.get('finding_ids'), findings)}]")
    return out


def digest(run_dir):
    findings = _findings(run_dir)
    lines = []
    card = _load(os.path.join(run_dir, "card.v1.json")) or _load(os.path.join(run_dir, "card.json")) or {}
    lines.append(f"CARD v{card.get('card_version')}: {card.get('summary_third_person')}")
    lines.append(f"  customer={card.get('customer')} payer_same_as_user={card.get('payer_same_as_user')} driver={card.get('buying_driver')} product={card.get('product_type')} price_band={card.get('price_band')} trajectory={card.get('trajectory')} market={card.get('market_type')}")
    for name in FILES:
        c = _load(os.path.join(run_dir, name))
        if not isinstance(c, dict):
            lines.append(f"{name}: missing")
            continue
        lines.append(f"{name}: status={c.get('status')} confidence={c.get('confidence')} :: {str(c.get('answer', ''))[:400]}")
        lines += _specific(name, c, findings)
        lines += _cands(c, findings, "kill_candidates")
        lines += _cands(c, findings, "alive_candidates")
        for u in (c.get("unknowns") or [])[:3]:
            lines.append(f"  unknown: {str(u)[:160]}")
    verified = sum(1 for r in findings.values() if r.get("opened") is True and r.get("quote_check") == "found")
    lines.append(f"FINDINGS: {len(findings)} total, {verified} verified (+ verified, - not verified, ? missing)")
    return "\n".join(lines)
