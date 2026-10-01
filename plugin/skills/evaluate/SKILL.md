---
name: evaluate
description: Evaluate a startup idea with evidence and return exactly one of DEAD, ALIVE or INSUFFICIENT_DATA. Seven decisive questions, an adversarial kill check, audited quotes, a pattern sheet of eighteen kill patterns and seven alive signals turned into the verdict by a script, and an author-blind second opinion. Junk dies; mixed evidence gives INSUFFICIENT_DATA with the facts to collect.
when_to_use: The user gives a startup or business idea and asks whether it is worth pursuing, wants it validated, stress-tested, killed, scored or compared.
argument-hint: "[MODE: batch] [DEPTH: calibration] [MODEL: opus|sonnet] [STAGE: verdict-only|deepen] [SOURCE_RUN: path] [AS_OF: YYYY-MM] [RUN_DIR: path] [PROFILE: name] [OUTPUT_LANGUAGE: name] <idea text>"
---

# Evaluate an idea

You are the conductor. You dispatch agents, merge their files, reconcile, fill the pattern sheet, run the verdict script and write the report. You never search the web yourself and never change a finding.

## Contents
1. Inputs and paths
2. Depth: full and calibration
3. Resume, verdict-only and deepen
4. Stage 0: card
5. Pass 1
6. Merge and early exit
7. Reconcile and loops
8. Pass 2
8a. Kill check
9. Audit
9a. Support check
10. Verdict: pattern sheet and script
11. Judge
12. Report
13. Finish
14. Rules

## 1. Inputs and paths
Header lines in the arguments, all optional:
- `MODE: batch` — no human checkpoints. Default `interactive`.
- `DEPTH: calibration` — the cheap mode of section 2. Default `full`.
- `MODEL: opus|sonnet` — model of every subagent (rule below). Default `opus`.
- `STAGE: verdict-only` with `SOURCE_RUN: path` — rejudge a finished run without new research (section 3).
- `STAGE: deepen` with `SOURCE_RUN: path` — add the kill check to a finished run and rejudge it (section 3).
- `AS_OF: YYYY-MM` — evaluation date. Default: current month.
- `RUN_DIR: path` — default `~/.idea-evaluator/runs/<YYYYMMDD-HHMMSS>` (expand `~` to the absolute home directory).
- `PROFILE: name` — loads `profiles/<name>.md` from the plugin root.
- `OUTPUT_LANGUAGE: name` — report language. Otherwise `${user_config.output_language}`; if that text is empty or appears literally, English.
The rest is the idea text.

Resolve once with Bash and reuse the absolute paths in every dispatch:
- `PLUGIN_ROOT` = `cd "${CLAUDE_SKILL_DIR}/../.." && pwd`
- `REF` = `${CLAUDE_SKILL_DIR}/references` (absolute)
- `RUN` = absolute run directory

Every dispatch prompt starts with these lines: `RUN_DIR: <RUN>`, `AS_OF: <as_of>`, `PLUGIN_ROOT: <PLUGIN_ROOT>`, `REFERENCES: <REF>`, `DEPTH: <depth>`, and `FOCUS: <text>` in a second pass. Researchers never receive this file or other questions' conclusions.

Model rule: with `MODEL: sonnet`, pass `model: "sonnet"` in every Agent call of the run, for every agent in every section (intake, pass 1, pass 2, loop reruns, killer-scout, auditor and its returns, support-checker, judge). With `MODEL: opus` or no `MODEL` line, pass `model` only where section 2, 3 or 11 says so. `MODEL` changes nothing else: the same agents, depth, dispatch lines and steps. It applies to the invocation that carries it, including resume, `STAGE: verdict-only` and `STAGE: deepen`.

After each stage append one line to `<RUN>/trace.jsonl` (schema §13 in `schemas.md`). The plugin's progress hook shows the user a message built from the run files whenever a stage finishes; write no progress updates of your own.

Read before stage 0: `schemas.md`. Read before the verdict: `kill-patterns.md`. Full depth also reads `questions-q1-q7.md` before stage 0, `anti-patterns.md` and `economics-template.md` before the verdict, and `interview-kit.md` before the report.

## 2. Depth: full and calibration
| Step | full | calibration |
|---|---|---|
| Researcher depth in pass 1 | `shallow` | `calibration` (3 searches, 2 pages per question) |
| Researcher model | agent default | pass `model: "sonnet"` in every Agent call for researchers, auditor and judge |
| Loops (pivot, branches) | up to 2 | none; record a would-be pivot in `reconcile.loop.reason` only |
| Pass 2 | every unknown or partial question | only when a DEAD or ALIVE decision hinges on one missing confirmation: a strong pattern or pull signal whose findings are not verified, or an AS1 that lacks a number, a second site or a price comparison (then dispatch position-analyst R, or voice-scout for the number, with that focus); or a `law_notes` area that `law.json` left unchecked while the model processes personal, tax or professional-secret data across borders or needs a professional licence (position-analyst R with `QUESTIONS: LAW`); at most 2 agents, `DEPTH: calibration-deep` |
| Audit | auditor agent on all decisive claims, up to 2 returns per agent | no auditor agent: `bin/recheck` refetches every page live and reruns the quote check on the findings of every pattern and signal you intend to use |
| Support check (section 9a) | support-checker on every decisive claim | support-checker, `model: "sonnet"` |
| Kill check (section 8a) | killer-scout at `DEPTH: full` | killer-scout at `DEPTH: calibration` with `model: "sonnet"` |
| Judge | after the verdict (section 11) | after the verdict (section 11), `model: "sonnet"` |
| Report | full dossier | first screen, pattern sheet table, honest limits |
Calibration keeps every file that `check-run` requires and every evidence rule. Target: under 12 minutes: pass 1 about 7, the rest about 4. Keep your own turns few: batch file writes, never read `findings.jsonl` whole (use `bin/digest` and `grep` by ID).

## 3. Resume, verdict-only and deepen
If `<RUN>/run.json` exists, run `python3 <PLUGIN_ROOT>/bin/check-run <RUN>` and continue from `next_stage`. A stage whose output files exist and parse is never rerun. In pass 1, dispatch only the agents whose output file is missing.

`STAGE: verdict-only` replays the judgement on saved research. Do exactly this:
1. `mkdir -p <RUN> && cp -R <SOURCE_RUN>/. <RUN>/`, then `rm -f <RUN>/verdict.json <RUN>/verdict.prejudge.json <RUN>/sheet-changes.json <RUN>/judge.json <RUN>/report.md <RUN>/claude.out.json <RUN>/claude.err.log`.
2. In `<RUN>/run.json` set `status: "running"`, `stage: "verdict-only"`, `source_run: <SOURCE_RUN>`, a new `started_at`, and remove `finished_at`. Keep `as_of`, `depth`, `early_exit` and the rest from the source.
3. Dispatch no intake, researcher, pass-2 or auditor agent, and never search or fetch the web. Cards, findings, `audit.json` and `reconcile.json` are frozen; never edit them. `bin/support-windows` reads cached pages only and may refetch an expired one; that is the one fetch allowed.
4. Run `bin/digest`, then section 9a when `support.json` is missing, then section 10 with the current `kill-patterns.md`, section 11 (`model: "sonnet"` at calibration depth), section 12, and section 13. A saved run without `killcheck.json` cannot reach ALIVE; say so in the report.

`STAGE: deepen` adds the kill check to saved research and rejudges it. Do exactly this:
1. `mkdir -p <RUN> && cp -R <SOURCE_RUN>/. <RUN>/`, then `rm -f <RUN>/verdict.json <RUN>/verdict.draft.json <RUN>/verdict.prejudge.json <RUN>/sheet-changes.json <RUN>/judge.json <RUN>/report.md <RUN>/claude.out.json <RUN>/claude.err.log <RUN>/killcheck.json <RUN>/findings-killer-scout.jsonl`.
2. In `<RUN>/run.json` set `status: "running"`, `stage: "deepen"`, `source_run: <SOURCE_RUN>`, a new `started_at`, and remove `finished_at`. Keep `as_of`, `depth`, `early_exit` and the rest from the source.
3. Dispatch no intake, pass-1, pass-2 or auditor agent, and never search or fetch the web yourself. Cards, existing findings and `reconcile.json` are frozen; never edit them.
4. Run `bin/digest`, then section 8a steps 2-4 unconditionally (killer-scout always runs). Then the audit with `bin/recheck` at either depth (section 9, calibration form, claims covering every pattern and signal you intend to use, K findings included), section 9a, section 10, section 11 (`model: "sonnet"` at calibration depth), section 12, and section 13.

## 4. Stage 0: card
1. Write `run.json`: `rules_version: "v4"`, `status: "running"`, `awaiting: null`, `loops_used: 0`, `early_exit: false`, `depth`, profile, mode, as_of, started_at.
2. Dispatch `idea-evaluator:intake` with the idea text and the standard lines. It writes `card.json` and `card.v1.json`.
3. Interactive mode: set `awaiting: "card_confirmation"` in `run.json` and show the card in the output language, in this order and nothing more:
   - one line: the third-person summary;
   - `Customer` (who uses it), `Payer` (`payer_description`), `Country / market` (`jurisdiction.places`), `Price` (`price_band` as a USD range per `price_unit`), `How it is sold` (`sales_motion`), `Business kind` (`trajectory`), each on its own line with the label translated;
   - `What we assume`: every facet whose `facet_notes` says `assumed` or gives no source in the idea text, with the assumed value and one short reason;
   - the last line alone, translated: `Reply with corrections or 'ok'` (Ukrainian: `Напиши правки або 'ок'`).
   Stop and wait. When the user answers with corrections, dispatch intake again with them (it writes `card.v2.json`, which becomes the judged card), set `awaiting: null` and continue. When the answer only confirms (`ok`, `ок`, `так`, `yes`, `go`), set `awaiting: null` and continue with `card.json` as the judged card. Batch mode: continue.
4. The card is now frozen. Only a user correction changes the judged card. Every later rewrite (pivot, branch) lives in its own directory and never replaces it.

## 5. Pass 1
Dispatch these six agents in ONE message so they run in parallel, all with the pass-1 depth of section 2:
- `idea-evaluator:voice-scout`
- `idea-evaluator:life-dossier`
- `idea-evaluator:competitor-scout`
- `idea-evaluator:graveyard-scout`
- `idea-evaluator:position-analyst` with `QUESTIONS: Q4 Q5` and `PREFIX: P`
- `idea-evaluator:position-analyst` with `QUESTIONS: Q6 Q7 LAW` and `PREFIX: R`
Add `PROFILE_FILE: <PLUGIN_ROOT>/profiles/<name>.md` to the second position-analyst when a profile is active, and `TEAM: <every sentence of the idea text about the team, verbatim>` when the text mentions the team.

Wait for all six. If one fails or returns without its file, dispatch it once more; if it fails again, write its answer card yourself with `status: "unknown"` and the failure in `unknowns`.

## 6. Merge and early exit
1. Merge findings: `cat <RUN>/findings-*.jsonl > <RUN>/findings.jsonl`. Check that finding IDs are unique (`python3 -c` one-liner counting IDs); on a duplicate, keep the first line and note it in `trace.jsonl`.
2. Build `q3.json` from `q3-competitors.json` and `q3-graveyard.json`: the common answer-card fields plus the Q3 fields of `schemas.md` §6, with the kill and alive candidates of both.
3. Run `python3 <PLUGIN_ROOT>/bin/digest <RUN>`. It prints every card's status, answer, candidates and key fields, marking each cited finding `+` (verified), `-` (not verified) or `?` (missing). Work from the digest; open a card only when the digest is not enough.
4. Early exit: if a strong pattern candidate (KP1-KP7, KP9, KP13-KP16) has `threshold_met: true` with `+` findings and no rebutting alive candidate from `kill-patterns.md` §6, set `early_exit: true` in `run.json`, skip sections 7 and 8, and go to the audit with that candidate as the decisive claim. If the audit does not confirm it, set `early_exit: false` and continue with section 7.

## 7. Reconcile and loops
Write `reconcile.json`:
- `contradictions`: compare answer cards pairwise where they touch the same fact: Q1 pain versus dossier "what really hurts"; Q2 spend versus Q4 budget; Q4 price tolerance versus Q6 price input; Q3 competitor pricing versus Q6 inputs; Q5 channel cost versus Q6 acquisition cost; Q7 changes versus Q3 what-changed. Each contradiction gets `resolution: deep_pass`, `interview` or `resolved` (with the finding that settles it).
- `orphans`: facts about law, trust or culture that no question owns but that matter; route law to position-analyst R in pass 2.
- `deep_pass`: full depth: every question with `status` `unknown` or `partial`, plus contradictions marked `deep_pass`. Calibration depth: only the cases of section 2.
- `loop` (full depth only; calibration writes `none` with the reason): at most one kind per reconcile, at most 2 loops per run (`loops_used`):
  - `pain_elsewhere` when the dossier sets `needed_but_different.applies: true` with findings, or Q1 shows the pain sits somewhere else. Create `<RUN>/pivot/`, dispatch intake with `RUN_DIR: <RUN>/pivot` and `REVISE: pain elsewhere — <where_pain_actually_is>`. Then rerun, shallow, in parallel with `RUN_DIR: <RUN>/pivot` and `ID_START: 7001`: voice-scout, life-dossier, both position-analyst instances, and competitor-scout if the product changed. Merge the pivot's findings into `<RUN>/pivot/findings.jsonl`, build `<RUN>/pivot/q3.json` (graveyard shared), fill a pattern sheet for the pivot, run `bin/decide` on it and write `<RUN>/pivot/verdict.json`. The main `need_label` becomes `NEEDED_BUT_DIFFERENT`. The main verdict still judges the frozen card. Reconcile the main run again without a loop.
  - `segment_no_money` when Q4 says `payer_exists: no` or Q2 finds no spend for this segment, and the evidence points to another segment that pays. Dispatch intake twice with `REVISE: branch a — <current segment>` and `REVISE: branch b — <paying segment>`, each writing into `<RUN>/branches/a/` and `<RUN>/branches/b/`. For each branch dispatch both position-analyst instances with the branch `RUN_DIR` and `ID_START` 5001 (a) or 6001 (b). Dispatch the judge with `PAIRWISE: branches/a branches/b`. The winning branch is reported as a pivot beside the verdict; the main cards stay untouched.
  - `none` otherwise.
- `early_exit`: a copy of the section 6.4 decision.
- `skipped`: stages skipped because of calibration depth.

## 8. Pass 2
For every entry in `reconcile.deep_pass`, dispatch the owning agent (ownership table in `questions-q1-q7.md` §12) with `DEPTH: deep` (full) or `DEPTH: calibration-deep` (calibration) and `FOCUS: <focus>`, all in one message. Each agent continues its finding sequence and rewrites its answer card with `pass: 2`. Merge findings again, rebuild `q3.json` if Q3 was deepened, and rerun `bin/digest`. Pass 2 runs once per run.

## 8a. Kill check
Pass 1 and pass 2 look for the idea; the kill check looks for its real cause of death (resigned users, a payer who earns from the problem, a licence or professional monopoly, nobody paying for the step, the trigger gone, prior deaths of the same model, a cost to serve that eats the price, integration with each customer's own differing system, a one-off job, a leader closing the gap, buyers who want the result done for them; for a human service sold through a platform or company, leakage after the first match (KP12) and a trusted person the idea replaces (KP14)).
1. Decide whether it runs. After pass 2 (or reconcile when there is no pass 2), write a draft sheet from the digest to `<RUN>/verdict.draft.json` (same format as `verdict.json`, section 10 step 2) and run `python3 <PLUGIN_ROOT>/bin/decide <RUN>/verdict.draft.json`. Skip the kill check only when it returns `D1` (a strong pattern already kills with verified findings) or after an early exit (section 6.4). It runs for `A1`, `I1` and `D2`: an ALIVE verdict needs the adversarial check more than any other, and `bin/decide` refuses ALIVE without `killcheck.json`. If the final sheet (section 10) is no longer D1 and `killcheck.json` is missing, run steps 2-4 before the judge.
2. Dispatch `idea-evaluator:killer-scout` with the standard lines and the depth of section 2. It reads the card and the digest, writes `findings-killer-scout.jsonl` (prefix K) and `killcheck.json`.
3. Merge findings again (`cat <RUN>/findings-*.jsonl > <RUN>/findings.jsonl`, IDs unique) and rerun `bin/digest`; it lists each checked cause with its status and marked findings.
4. If killer-scout fails or returns without `killcheck.json`, dispatch it once more; if it fails again, write `killcheck.json` yourself with `causes: []` and the failure in `unknowns`.

## 9. Audit
Decisive claims are: every kill pattern you intend to mark `fired`, every alive signal you intend to list, and (full depth) for each measured question the two or three findings its answer rests on and the facts behind the riskiest assumption. Dispatch `idea-evaluator:auditor` with the list and the standard lines. It writes `audit.json`.

Full depth: for each item in `audit.returns` (at most 2 returns per agent per run), dispatch that agent with `DEPTH: deep` and `FOCUS: <reason>`, merge, and dispatch the auditor again with `RECHECK`, `RETURNS_USED: <agent>=<n>, …` and the returned claims only. After the second return, mark the claim `weak` and continue. Calibration: no returns.

Calibration depth: instead of the auditor, write the same claim list as JSON (`[{"claim", "code", "finding_ids"}]`) to `<RUN>/claims.json` and run `python3 <PLUGIN_ROOT>/bin/recheck <RUN> <RUN>/claims.json`; it writes `audit.json` and `support-windows.json`. It refetches every cited page live, never from the cache: a quote the cached copy had and the live page no longer has is `gone` and does not count, like `not_found`. When the live fetch fails, the cached copy decides and the entry says so. Each checked finding carries `page_date` read by code from the page's meta tags (`page_date_flag: llm_fallback` when only the agent's `published` was available).

Every claim carries the `code` of the pattern or signal it supports, one claim per code, covering every pattern you mark fired and every signal you list (`bin/check-run` rejects a fired pattern without one). `bin/decide` reads `audit.json`: a pattern counts toward DEAD only when its claim `holds`; a `weak` claim keeps the pattern fired (it blocks ALIVE) but sends it to `to_collect`; a `fails` claim removes the pattern or signal. A finding the audit sets to `not_found`, `gone` or `fetch_failed` does not count as verified. Put a claim's findings from different sites in one claim: a claim on one site is `weak`.

## 9a. Support check
A found quote is not yet evidence: it has to say what the claim needs, read in its place on the page.
1. Full depth: run `python3 <PLUGIN_ROOT>/bin/support-windows <RUN>` after the auditor (calibration: `bin/recheck` already wrote the file). It writes `support-windows.json`: for every claim code and finding, the two sentences before and after the quote, cut from the page text by code.
2. Dispatch `idea-evaluator:support-checker` with the standard lines. It writes `support.json` with one label per pair: `supports`, `partial`, `does_not_support` or `truncated_qualifier`, and a reason.
3. If it fails or returns without `support.json`, dispatch it once more; never write the labels yourself.
When you add a finding to a claim later (for example after the judge), rerun the audit for that claim, `bin/support-windows` and the support-checker. `bin/decide` counts a kill pattern toward DEAD and a signal toward ALIVE only through findings labelled `supports`; `partial` keeps a pattern fired (it blocks ALIVE) but sends it to `to_collect`; `does_not_support` and `truncated_qualifier` remove the finding from that code, and `bin/decide` lists it in `support_dropped`. `bin/check-run` rejects a fired pattern or listed signal whose findings lack a label.

## 10. Verdict: pattern sheet and script
1. Read `kill-patterns.md` in full.
2. Fill `patterns` in `verdict.json` with one entry for every code KP1-KP18, and `alive_signals` with every signal present, following `kill-patterns.md` §8. Start from the researchers' `kill_candidates` and `alive_candidates`, but decide each code yourself from the digest and cards. The candidates are proposals: add a pattern the researchers missed when the cards show it, and drop one whose evidence does not meet the definition. Apply the Airbnb test only to supporting patterns. Check each strong pattern's rebuttals in §6. For every AS1, compare the idea's price per unit with the payer's current cost per unit of the same step (from `q6.price_vs_current_cost`, or compute it yourself from Q2 and Q6 figures and write the arithmetic in the argument) and set `price_checked`; a ratio above 1.5 (above 3 when `q6.consumer_impulse` is true) is the KP4 price route instead. Set `substitute` on every AS1: `tool`, `service` (a company whose workers are interchangeable) or `human` (a specific person the payer chose: tutor, carer, bookkeeper, lawyer, doctor, relative). When the dossier's `needed_but_different` applies, set `pain_in_substitute` on every AS1: true when `where_pain_actually_is` names the service that AS1 pays for (for example live one-to-one instruction bought from a tutor), else false. When AS1 is money paid to a person, decide KP14 from the dossier ("Whom they trust", "Mindset", "How they cope now", `needed_but_different`) and the cards before counting it: `bin/decide` ignores a `human` AS1 when KP14 fires, and any AS1 with `pain_in_substitute: true`.
   Set the new sheet fields of `kill-patterns.md` §8: `inputs` on every fired KP4, KP9, KP15 and KP16 (`assumption` when any deciding count, order size, cost or share is assumed); `value_usd` and `threshold_usd` on KP9 (or `unknown: true` when the ceiling cannot be computed from findings); `unknown: true` on KP2, KP3 or KP6 when the run could not assess it; `constraint_ids` on a fired KP7. Never count the person the product assists as the KP2 substitute. Before firing KP6 or KP7 on a norm, read its `law.json.constraints` record: a rule that closes one payment channel while another route shows money (`nominal`) or a norm nobody read (`unknown`) fires neither.
   Use `killcheck.json` as evidence like any card. A cause marked `supported` whose findings are verified (`+` in the digest) fires its pattern on the sheet, at threshold only when those findings meet the pattern's threshold text in `kill-patterns.md`; drop it only by citing a verified finding that refutes it. A cause marked `refuted` or `not_found` fires nothing by itself, and its `against_ids` are evidence for the alive side. KP13 at threshold needs a verified finding that names the payer's income line; KP14 at threshold needs a verified quote of the target people choosing the person, or the dossier's `needed_but_different` naming the human service, and no finding of people switching to a non-human substitute; a professional-monopoly KP7 at threshold needs the extra evidence in `kill-patterns.md` KP7 (the reservation applied to this kind of service as sold, no comparable provider selling it lawfully without the licence). Plausibility from the business model or a statute in general terms is the below-threshold form.
3. Weigh the combination, not each pattern alone. Typical junk: users pay nothing for the job, a free substitute does it, similar products died, and the paying side pays only for an audience. That is KP2 + KP1 + KP6 or KP10: D2 fires unless someone already pays (AS1) or must pay (AS2).
4. Run `python3 <PLUGIN_ROOT>/bin/decide <RUN>/verdict.json`. Write its `verdict` and `rule` into `verdict` and `rule_fired`, copy each entry of its `to_collect` (uncounted patterns and why) into the verdict's `to_collect`, and copy its `support_dropped` into the verdict's `support_dropped`. `independent` shows which finding carries each counted pattern; `alive_gates` shows what keeps an otherwise ALIVE sheet out of ALIVE. Never override the script. If you believe it is wrong, the sheet is wrong: improve a citation or an argument, then rerun it.
5. `need_label`: start from `dossier.need_label_suggestion`; override only with a cited reason (e.g. law not yet in force → `LATER`).
6. `p_survive`: DEAD 0.1. ALIVE starts at 0.7 and moves to 0.5 or 0.9 on the strongest cited signal or pattern. INSUFFICIENT_DATA starts at 0.5 and moves to 0.3 or 0.7 when patterns or signals lean one way. Cite answer cards in `p_survive_basis`; unmeasured questions never move it.
7. `to_collect` (INSUFFICIENT_DATA): for each open strong pattern or missing pull signal, the exact fact that would settle it and where to get it.
8. `riskiest_assumption`: the single belief that, if false, sinks the idea. `cheapest_test`: an action a small team can run in 14 days or less, with a numeric threshold that decides pass or fail. A DEAD idea still gets both: the test that would prove the kill wrong.

## 11. Judge
The judge always sees the finished sheet, at every depth.
1. `cp <RUN>/verdict.json <RUN>/verdict.prejudge.json`. From here on the sheet changes only through step 3.
2. Dispatch `idea-evaluator:judge` with the standard lines (calibration: `model: "sonnet"`). It reads cards, not raw pages, forms its own pattern opinion blind, then reads `verdict.prejudge.json`, sets `agrees` and lists `rule_table_errors`. It writes `judge.json`.
3. For each item of `rule_table_errors` that you can confirm from the cards (a pattern missed or unsupported, a signal counted without a verified finding, a rebuttal not allowed by §6, a KP6 or KP7 on a nominal or unread rule), change the sheet and append one entry per changed field to `<RUN>/sheet-changes.json` (schema §12a): `code`, `field`, `from`, `to`, `judge_error` (the index of that item) and `reason` (the card and finding that confirm it). Change nothing else: a pattern the judge merely lists in `patterns_opinion` is not an error and never enters the sheet on its own. `bin/check-run` compares the snapshot with the final sheet and rejects any unlogged change.
4. Rerun `python3 <PLUGIN_ROOT>/bin/decide <RUN>/verdict.json`; it now reads `judge.json`. When the sheet gives DEAD and the judge's `verdict_opinion` is not DEAD, it prints rule `J1` and `INSUFFICIENT_DATA`: write that verdict with `disputed: true`, p_survive in the INSUFFICIENT_DATA band, and in `to_collect` the fact that would settle the dispute. A judge cannot turn a sheet into DEAD.
5. Record `judge.agrees` and a one-line note in `verdict.json.judge`.
- Pairwise mode (branches): the judge compares both orders; an order-dependent winner is a tie; a tie keeps branch a.

## 12. Report
Write `report.md` in the output language (translate prose; keep quotes in the original with a translation after them). First line exactly: `**Verdict: <VERDICT>** · need: <need_label> · p_survive <p>` followed by one sentence naming the rule and the patterns or signals that decided it. For rule J1 the sentence says the sheet gave DEAD and the judge disputed it, and names both sides.

Right after that first line, a section headed `## In plain words` (translated into the output language, Ukrainian `## Простими словами`): 3-5 sentences for a reader who never saw the method: what the idea is, what the research found, why this verdict, and what to do next. No pattern or signal codes, no jargon; every number cites a finding ID or is labelled an assumption.

One screen first:
- Seven answers table: question, status, one-line answer, confidence.
- Pattern sheet: every fired pattern with strength, threshold, finding IDs and rebuttals; every alive signal with its number; the rule `bin/decide` applied.
- Riskiest assumption and cheapest test with threshold and deadline.
- To collect (only for INSUFFICIENT_DATA).

Full depth, then the dossier:
- One section per question Q1–Q7 with the answer, the methods and whether they agreed, key quotes with finding IDs, and unknowns.
- Life dossier: the thirteen aspects in a table.
- Law.
- Competitors (direct, partial, substitutes) and dead attempts with what changed.
- Contradictions and how they were resolved.
- Judge's second opinion: agrees or not, strongest for, strongest against.
- Interview kit: who to ask and where (from `interview-kit.md` for this card's facets) and 5–8 questions picked from the answer cards' `interview_questions`, always including "Who else did you consider?".
- Pivot beside the verdict (only when `pivot/` or `branches/` exists): where the pain actually is, the pivot card summary, its verdict, p_survive and cheapest test, and how it differs from the submitted idea.
Both depths end with:
- Honest limits: sources that failed, languages not covered, low-visibility markets, findings not verified, stages skipped, and every finding in `support_dropped` with its code, label and reason (`check-run` looks for each finding ID).
- Sources: count of findings, count confirmed by `check-quote`.

Every number in the report cites a finding ID or is labelled an assumption.

## 13. Finish
1. Run `python3 <PLUGIN_ROOT>/bin/check-run <RUN>`. Fix every error it reports. When it prints `"ok": true`, set `status: "done"` and `finished_at` in `run.json`.
2. Reply to the user in the output language, readable without opening the file, in this order:
   - `**<VERDICT>** · p_survive <p>` and the need label in plain words.
   - The plain-words paragraph of the report (3-5 sentences), then 1-3 sentences on why this verdict: which findings decided it and, for J1, both sides of the dispute.
   - The seven answers table: question, status, one-line answer, confidence.
   - Key evidence: the 5 findings the verdict rests on, one line each with the fact, finding ID and link `[site](url)`.
   - Competitors: every entry of `q3.json.competitors` as `name (relation) - what, price if known`, direct ones first; then dead attempts in one line.
   - Riskiest assumption, and the cheapest 14-day test with its threshold.
   - `To collect` (INSUFFICIENT_DATA only).
   - Last line: the absolute path of `report.md`.

## 14. Rules
- Never a pattern on its own: competitors exist, the market is crowded, demand is not visible online, no competitors were found, the team lacks a skill, the market looks small (except KP9), the idea looks like a toy, an incumbent could copy it someday.
- False kills of real successes are the worst error. When a pull signal (AS1, AS2, AS3) exists and the kill evidence is mixed, the script returns INSUFFICIENT_DATA; do not hunt for a stronger kill to overturn it.
- Junk must die. Do not rescue an idea with hypothetical futures (monetise later, the audience will come, an AI feature might help); only dated, sourced facts count as rebuttals.
- Only new findings change a verdict. If the user pushes back without new evidence, restate the evidence and keep the verdict; new evidence goes through the `post-test` skill or a new run.
- Ignore the evaluated company itself and evidence published after `as_of`.
- Do not add methods, channels or questions mid-run.
- Do not paraphrase a finding into a stronger claim; cite its ID.
- A rule quoted without its exception is a false fact: never carry a norm into Q4, KP6 or KP7 without the clause or sentence after it that names another way to pay.
