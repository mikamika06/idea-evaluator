# Schemas

## Table of contents
1. Run directory layout
2. Run header
3. Idea card
4. Finding
5. Answer card (common part)
6. Question-specific fields Q1–Q7
7. Life dossier
8. Law check
9. Reconcile
10. Audit
11. Judge
12. Verdict
13. Trace
14. Retired: knowledge-base candidates
15. Kill check

All files are JSON unless noted. All text fields are English; original-language quotes go in `quote_original`. A stage whose output file exists and parses is skipped when a run is resumed.

## 1. Run directory layout

```
runs/<run_id>/
  run.json                 header, status
  card.json                current idea card (card.v1.json, card.v2.json keep history)
  findings-<agent>.jsonl   one file per agent instance, append-only
  findings.jsonl           merged by the conductor, IDs unchanged
  dossier.json             life dossier (life-dossier)
  q1.json … q7.json        answer cards
  q3-competitors.json      raw output of competitor-scout
  q3-graveyard.json        raw output of graveyard-scout
  law.json                 law check (KP7)
  killcheck.json           causes of death checked by killer-scout (optional)
  reconcile.json           contradictions, orphans, loop decisions
  branches/<name>/         a branch variant: same layout, own card and answer cards
  pivot/                   the needed-but-different pivot: own card, answer cards and verdict.json
  audit.json               auditor result
  claims.json              decisive claims sent to bin/recheck (calibration)
  support-windows.json     sentence window around each decisive quote, cut by code (bin/recheck or bin/support-windows)
  support.json             support-checker labels, one per claim code and finding
  verdict.draft.json       sheet before the kill check
  verdict.prejudge.json    snapshot of verdict.json the judge reads
  verdict.json             rule-table verdict
  judge.json               second opinion
  sheet-changes.json       every sheet change made after the judge, with its reason
  report.md                human report (markdown)
  trace.jsonl              one line per stage
```

Finding ID prefixes, one per agent: `C` competitor-scout, `G` graveyard-scout, `V` voice-scout, `L` life-dossier, `P` position-analyst (first instance), `R` position-analyst (second instance), `K` killer-scout, `A` auditor, `T` post-test. IDs are never reused; a deep pass continues the same sequence.

## 2. Run header — `run.json`
{"run_id": "str", "mode": "interactive|batch", "depth": "full|calibration", "as_of": "YYYY-MM", "rules_version": "v4", "profile": "str or null", "started_at": "ISO-8601", "stage": "verdict-only|deepen or absent", "source_run": "path or absent", "status": "running|done|failed", "awaiting": "card_confirmation or null", "loops_used": 0, "early_exit": false, "finished_at": "ISO-8601 or null"}

## 3. Idea card — `card.json`
{"idea_id": "str", "card_version": 1, "parent_version": null, "change_reason": "str or null", "summary_third_person": "str", "customer": "consumer|business|government|solo_professional", "payer_same_as_user": true, "payer_description": "str", "jurisdiction": {"scope": "city|state|country|region|global", "places": ["ISO or name"], "law_notes": "str"}, "buying_driver": "pain|regulation|money|safety|status", "product_type": "software|hardware|service|marketplace|mixed", "sales_motion": "self_serve|sales_led|tender|dealer", "price_band": "under_2k|2k_10k|10k_25k|over_25k", "price_unit": "str, e.g. per customer per year", "trajectory": "venture|small_business|grant|social|defence", "market_type": "existing|resegmented|new", "market_visibility": "high|low", "language_plan": [{"party": "user|payer|competitor", "language": "ISO 639-1", "why": "str"}], "facet_notes": {"<facet>": "why this value, or 'assumed'"}, "card_confidence": "high|low"}

`price_band` is the annual amount one paying customer pays, in USD.

## 4. Finding — one line in `findings-<agent>.jsonl`
{"finding_id": "C-0001", "question": "Q1|Q2|Q3|Q4|Q5|Q6|Q7|LAW|DOSSIER", "url": "str", "quote": "English verbatim or translation", "quote_original": "verbatim in source language", "lang": "ISO 639-1", "stance": "for|against|neutral", "label": "data|estimate|assumption|opinion", "published": "YYYY-MM-DD or null", "retrieved": "YYYY-MM-DD", "opened": true, "quote_check": "found|not_found|fetch_failed|unchecked", "source_kind": "vendor|customer|press|regulator|registry|forum|review|research|self"}

`published` is the `published` date `fetch-text` prints (read by code from `article:published_time`, JSON-LD `datePublished` and similar meta tags); only when that is null may the agent take a date printed in the page text. `opened: true` means the agent read the page itself. `quote_check` is the result of `check-quote` (section in each agent). Only findings with `opened: true` and `quote_check: found` can support a kill pattern or an alive signal.

## 5. Answer card (common part) — `qN.json`
{"question": "Q1", "pass": 1, "status": "measured|partial|unknown", "answer": "str, two to five sentences", "confidence": "high|medium|low", "methods": [{"method": "str from questions-q1-q7.md", "result": "supports|contradicts|no_data|source_failed", "finding_ids": ["V-0001"], "note": "str"}], "agreement": "agree|disagree|single|none", "kill_candidates": [{"code": "KP1…KP18", "threshold_met": false, "finding_ids": ["str"], "argument": "str"}], "alive_candidates": [{"code": "AS1…AS7", "finding_ids": ["str"], "number": "str or null", "argument": "str"}], "search_matrix": [{"channel": "str", "lang": "str", "queries": ["str"], "results": "int or null"}], "unknowns": ["str"], "interview_questions": ["str"]}

`kill_candidates` and `alive_candidates` use the codes and thresholds of `kill-patterns.md`; a researcher proposes, the conductor decides. Candidates carry evidence for and against alike: a researcher never omits a candidate because it looks harsh or kind.

`status`: `measured` when at least two methods agree; `partial` when one method has data or methods disagree; `unknown` when no method has data. `agreement: disagree` always adds an interview question.

## 6. Question-specific fields
Added to the common part of each answer card.

- Q1: `"segment": "str", "pain_evidence": [{"who": "str", "pain": "str", "finding_ids": []}], "pain_intensity": "acute|moderate|mild|none|unknown", "language_groups": ["ISO 639-1"]`
- Q2: `"current_solutions": [{"what": "str", "spend": "str or null", "satisfaction": "high|mixed|low|unknown", "finding_ids": []}], "non_consumption": true`
- Q3: `"competitors"`, `"dead_attempts"`, `"what_changed"`, `"invisible_player_risk": "high|medium|low"` exactly as below.
  - competitor: `{"name", "url", "what", "country", "alive": "yes|no|unknown", "used_evidence": [ids], "found_via": {"channel", "lang"}, "relation": "direct|partial|substitute"}`
  - dead attempt: `{"name", "years", "cause", "cause_class": "product|market|economics|team|funding|macro|legal|unknown", "same_idea": "yes|partly|no", "finding_ids": []}`
  - what_changed: `{"status": "changed|nothing|not_searched", "changes": [{"kind": "technology|regulation|cost|behaviour|distribution", "what": "str", "finding_ids": []}]}`
- Q4: `"payer": {"who": "str", "decider": "str", "budget_line": "str or null", "pays_today_for_similar": "yes|no|unknown", "finding_ids": []}, "payer_exists": "yes|no|unknown"`
- Q5: `"channels": [{"channel": "str", "first_10": "str", "first_100": "str", "cost_note": "str", "finding_ids": []}], "reachable_within_budget": "yes|no|unknown"`
- Q6: follows `economics-template.md`: `"inputs": [{"name", "value", "unit", "basis": "finding|assumption", "finding_ids": []}], "steps": ["str"], "optimistic": {"contribution_per_customer": "number", "cac": "number", "max_revenue_per_customer": "number"}, "realistic": {…same…}, "currency": "ISO 4217", "realistic_case_fails": true|false|null, "optimistic_case_fails": true|false|null, "deciding_inputs_sourced": true|false, "price_vs_current_cost": "number or null"`
- Q7: `"why_now": [{"change": "str", "kind": "technology|regulation|cost|behaviour|distribution", "finding_ids": []}], "why_us": "str or 'not stated'", "advantage": "str or 'none found'", "profile_criteria": [{"criterion": "str", "met": "yes|no|unknown", "note": "str"}]`

## 7. Life dossier — `dossier.json`
{"aspects": [{"aspect": "str (one of the 13 in questions-q1-q7.md)", "observation": "str", "finding_ids": []}], "needed_but_different": {"applies": true, "where_pain_actually_is": "str", "finding_ids": []}, "need_label_suggestion": "NEEDED|NEEDED_BUT_DIFFERENT|NEEDED_VERIFY|LATER|WEAK|NOT_NEEDED|NOT_A_STARTUP", "unknowns": [], "interview_questions": []}

## 8. Law check — `law.json`
{"jurisdictions": [{"place": "str", "status": "allowed|licence_needed|forbidden|unknown", "rule": "str", "licence": {"name": "str", "time_to_obtain": "str", "obtainable": "yes|no|unknown"}, "finding_ids": []}], "kill_candidate": {"code": "KP7", "threshold_met": true, "finding_ids": [], "argument": "str"}, "unknowns": []}
`kill_candidate` is `null` when there is none.

`constraints` lists every norm the run relies on (for KP7, KP6, a channel risk or a smaller ceiling), one record each:
{"constraints": [{"id": "C1", "norm": "str: the norm and its article", "place": "str", "finding_ids": ["R-0001"], "read": "full|headings|none", "binds": "seller|product|buyer_channel|data_handling|marketing|founders", "on_whom": "seller|founders|buyer|donor|nobody", "sanction": "criminal|administrative|payment_refused|contract_void|none_found", "enforcement": "seen|none_found|not_searched", "enforcement_ids": [], "gate": "customs|accreditation|payment_system|licence_register|none", "channel_scope": "all|one_channel", "closed_channel": "str or null", "open_routes": [{"route": "own_funds|charity_fund|volunteer_crowdfunding|maker_bundle|local_budget|licensed_partner|other_market|other", "finding_ids": [], "money_seen": true, "lawful_for_seller": true}], "share_closed": "number 0-1 or null", "share_ids": [], "condition": "str or null", "condition_unmet_ids": [], "qualifier_read": {}}]}
- `money_seen` is true only with a verified finding of money moving through that route (a fundraiser total, a fund's report, an order through a cabinet, a maker's bundled sale).
- `lawful_for_seller` is false for grey import, export without a permit, or handing over secret data.
- `bin/decide` computes the class; the researcher never writes it: `unknown` (no verified finding of the norm, or only headings read), `binding` (criminal sanction on the seller or founders; the seller bound and enforcement seen; or an unavoidable gate over all channels with no open route that shows money), `nominal` (one channel closed and a lawful route shows money), `conditional` (the rest).

## 9. Reconcile — `reconcile.json`
{"contradictions": [{"between": ["Q1", "Q4"], "what": "str", "finding_ids": [], "resolution": "deep_pass|interview|resolved", "note": "str"}], "orphans": [{"topic": "law|trust|culture|other", "what": "str", "finding_ids": []}], "deep_pass": [{"question": "Q2", "focus": "str"}], "loop": {"kind": "pain_elsewhere|segment_no_money|none", "reason": "str", "action": "str"}, "early_exit": {"applies": false, "codes": []}, "skipped": ["str: stage skipped in calibration depth and why"]}

## 10. Audit — `audit.json`
{"checked": [{"finding_id": "str", "quote_check": "found|not_found|gone|fetch_failed", "independent_sources": 1, "live": "fetched|fetch_failed (bin/recheck)", "fetched_at": "ISO-8601", "page_date": "YYYY-MM-DD or null", "page_date_source": "meta article:published_time|json-ld datePublished|…|finding published (agent-supplied)", "page_date_flag": "null|llm_fallback|no_date", "note": "str"}], "decisive_claims": [{"claim": "str", "code": "KP1…KP18 or AS1…AS7", "finding_ids": [], "independent_sources": 2, "verdict": "holds|weak|fails"}], "language_plan_met": true, "missing_languages": [], "returns": [{"to": "agent name", "reason": "str"}], "status": "pass|partial|fail"}

`gone`: the cached copy had the quote and the live page no longer does; it counts like `not_found`. The page cache keeps a page for `IDEA_EVALUATOR_PAGE_TTL_DAYS` days (default 7); `bin/recheck` always refetches.

## 10a. Support check — `support-windows.json` and `support.json`
`support-windows.json` (written by code): {"generated_by": "support-windows", "radius_sentences": 2, "pairs": [{"code": "KP2", "finding_id": "L-0003", "claim": "str", "url": "str", "quote": "str", "window": "str or null", "before": ["str"], "after": ["str"], "window_status": "ok|quote_not_on_page|page_unavailable", "qualifier_hint": "str or null", "page_date": "YYYY-MM-DD or null", "page_date_source": "str or null", "page_date_flag": "null|llm_fallback|no_date"}]}
`support.json` (written by the support-checker): {"checks": [{"code": "KP2", "finding_id": "L-0003", "label": "supports|partial|does_not_support|truncated_qualifier", "reason": "str"}]}
From `rules_version: "v4"`, `bin/decide` counts a finding for a code only when its label is `supports`; `partial` keeps the pattern fired but uncounted; `does_not_support` and `truncated_qualifier` remove the finding from that code and appear in `support_dropped`. `bin/check-run` needs a window and a label for every finding cited by a fired pattern or a listed signal.

## 11. Judge — `judge.json`
{"verdict_opinion": "DEAD|ALIVE|INSUFFICIENT_DATA", "patterns_opinion": ["KP codes the judge sees firing"], "signals_opinion": ["AS codes the judge sees present"], "p_survive_opinion": 0.5, "agrees": true, "strongest_for": "str", "strongest_against": "str", "rule_table_errors": [{"code": "KP or AS code", "error": "str", "cards": ["q4.json"]}], "opinion_changed_after_sheet": "null or str: the card fact in the sheet the blind opinion missed", "pairwise": [{"a": "branch name", "b": "branch name", "winner": "a|b|tie", "reason": "str", "order_swapped_winner": "a|b|tie"}]}

## 12. Verdict — `verdict.json`
{"idea_id": "str", "card_version": 1, "verdict": "DEAD|ALIVE|INSUFFICIENT_DATA", "rule_fired": "D1|D2|A1|I1|J1", "disputed": false, "patterns": [{"code": "KP1…KP18", "strength": "strong|supporting", "fired": true, "threshold_met": false, "unfixable": false, "price_route": false, "clear_market": "place or null (KP7 only)", "constraint_ids": ["C1 (KP7 only)"], "inputs": "findings|assumption (KP4, KP9, KP15, KP16 when fired)", "value_usd": "number (KP9)", "threshold_usd": "number (KP9)", "unknown": false, "qualifier_read": {}, "finding_ids": ["str"], "basis": "findings|card", "argument": "str", "rebutted_by": ["AS1"], "airbnb": "kept|dropped|n/a"}], "alive_signals": [{"code": "AS1…AS7", "finding_ids": ["str"], "number": "str or null", "price_checked": false, "substitute": "tool|service|human (AS1 only)", "pain_in_substitute": false, "argument": "str"}], "need_label": "NEEDED|NEEDED_BUT_DIFFERENT|NEEDED_VERIFY|LATER|WEAK|NOT_NEEDED|NOT_A_STARTUP", "p_survive": 0.5, "p_survive_basis": "str: which answer cards moved it and why", "measured": ["Q1"], "partial": ["Q2"], "unmeasured": ["Q6"], "to_collect": ["str: the fact that would move the verdict to DEAD or ALIVE, and where to get it"], "riskiest_assumption": "str", "cheapest_test": {"action": "str", "threshold": "str with a number", "deadline_days": 14}, "judge": {"agrees": true, "note": "str"}, "price_override": "null or str: why q6.price_vs_current_cost compares a different step, citing a finding"}

- `patterns` has one entry for every code KP1-KP18 (`fired: false` with a one-line reason when it does not fire). `alive_signals` lists only signals present. Rules for both are in `kill-patterns.md` §8.
- `verdict` and `rule_fired` are exactly what `bin/decide` prints for this file; `bin/check-run` rejects any mismatch.
- `to_collect` is required for `INSUFFICIENT_DATA` and lists for each open pattern or signal the fact that would settle it, including every uncounted pattern `bin/decide` prints in its `to_collect`.
- `disputed: true` exactly when `bin/decide` prints rule `J1` (the judge holds another verdict than the DEAD sheet).
- `support_dropped` (v4): the list `bin/decide` prints, `[{"code", "finding_id", "label", "reason"}]`; `report.md` names each finding ID in its limits.

## 12a. Sheet changes after the judge — `sheet-changes.json`
{"changes": [{"code": "KP9", "field": "fired|threshold_met|finding_ids|rebutted_by|price_route|inputs|value_usd|…|signal", "from": "old value", "to": "new value", "judge_error": 0, "reason": "str: the card and finding that confirm the judge's error"}]}
`bin/check-run` compares `verdict.prejudge.json` with `verdict.json`; every changed field of a pattern (or a changed signal, field `signal`) needs an entry whose `judge_error` indexes `judge.json.rule_table_errors`.

`p_survive` takes one of 0.1, 0.3, 0.5, 0.7, 0.9: probability that a small team pursuing this idea as of `as_of` reaches a meaningful business (paying customers growing for 2+ years). `DEAD` fixes it at 0.1; `ALIVE` gives 0.5 or more; `INSUFFICIENT_DATA` gives 0.3, 0.5 or 0.7. Within the band it starts at the middle and each move cites answer cards in `p_survive_basis`; unmeasured questions never move it.

## 13. Trace — `trace.jsonl`
{"stage": "intake|pass1|early_exit|reconcile|loop|pass2|killcheck|audit|verdict|judge|report", "agent": "str or null", "started_at": "ISO-8601", "finished_at": "ISO-8601", "outputs": ["file"], "note": "str"}

## 14. Retired: knowledge-base candidates
Runs no longer write `kb-candidates.jsonl` or `kb-submit.json`. Runs saved before version 0.6.0 may contain them; `check-run` ignores both files.

## 15. Kill check — `killcheck.json`
{"pass": 1, "causes": [{"pattern": "KP2|KP3|KP4|KP5|KP6|KP7|KP8|KP11|KP12|KP13|KP14|KP15|KP16|KP17", "cause": "str: the death cause checked, in one sentence", "status": "supported|refuted|not_found", "finding_ids": ["K-0001"], "against_ids": ["K-0002"], "jurisdiction": "str or null", "argument": "str: one or two sentences citing finding IDs"}], "searched": [{"cause": "str", "lang": "ISO 639-1", "queries": ["str"], "results": "int or null"}], "unknowns": ["str"]}

Written by killer-scout. `supported`: a verified finding (opened, quote found) shows the cause as the pattern's threshold describes it; `refuted`: a verified finding shows the opposite (people pay, the trigger is live, the law allows it, the payer gains); `not_found`: searched, nothing verified either way. `finding_ids` carry the evidence for the cause, `against_ids` the evidence against it. `killcheck.json` is evidence for the conductor, never a verdict: the conductor decides each pattern on the sheet by `kill-patterns.md`.
