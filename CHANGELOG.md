# Changelog

## 0.8.0 (2026-09-30)
- No plugin dependencies. The `caveman` dependency is gone from the marketplace manifest and the install steps; agents never referenced it. The README mentions it as an optional add-on for shorter chat output.
- Stop hook: it no longer blocks the conductor while background research agents or background commands of the same session are still running (this showed up as "Stop hook error occurred" right after pass 1 was dispatched). It reads the session transcript, counts background launches that have no completion notice yet, and stays silent while any are pending. It also ignores runs that the current session never mentioned, so a run in progress no longer blocks other sessions. When no transcript is readable it behaves as before.
- Progress hook: messages go only to the session that runs the evaluation. Before, any session whose working directory could see the run directory could post, and consume, another run's stage messages, so parallel runs lost stages and unrelated sessions got them.
- Both hooks find the run from the `RUN_DIR:` lines of the session transcript as well as from `<cwd>/runs` and `~/.idea-evaluator/runs`, so a custom `RUN_DIR` outside those places, or a conductor that changed directory, no longer switches the hooks off. Stop-hook messages name the run by its absolute path.
- Plugin metadata: homepage, repository and keywords; CHANGELOG added.
- Verdict rules, agents and schemas are unchanged from 0.7.3.

## 0.7.3 (2026-09-30)
- Stage progress comes from a `PostToolUse` hook (`bin/progress-hook`) instead of the model: after each of seven stages it posts the stage number, elapsed time and facts read from the run files (competitors with prices and links, dead attempts, who pays today, red flags, live signals, audit numbers, verdict, judge agreement, report path). Labels in English or Ukrainian. Silent when no run is active, never blocks a tool, no network.

## 0.7.2 (2026-09-30)
- `report.md` opens with an "In plain words" section; the final chat reply is a readable summary with the seven answers, key evidence with links, competitors, riskiest assumption, cheapest test and the report path.
- The card shown for confirmation lists customer, payer, market, price and every assumption, and a plain `ok` keeps the card without a second intake call.

## 0.7.1 (2026-09-29)
- Agent prompts and the conductor restored to their tuned 0.6.0 text after the 0.7.0 output-style experiment; `DEPTH: cheap` dropped.
- New optional `MODEL: opus|sonnet` header: with `sonnet` every subagent runs on Sonnet.

## 0.7.0 (2026-09-29)
- Experiment, reverted in 0.7.1: a built-in output style in every agent prompt replaced the `caveman` dependency, and a `DEPTH: cheap` mode ran research agents on Sonnet.
- Stop hook fixed to guard every rules version up to the current one (it had silently stopped firing).
- README discloses measured cost and time, web requests, local scripts and hooks; MIT license added.

## 0.6.0 (2026-09-29)
- The shared online knowledge base is retired. Scouts look up competitors and dead predecessors in an offline, read-only company directory (`plugin/directory/companies.json.gz`, `bin/company-dir`, about 6,700 companies from the YC directory and public failure lists), masked to `AS_OF`.

## 0.5.x (2026-09-29)
- 0.5.0: verdict rules count only independent audited evidence; the judge sees the finished sheet at every depth and its changes are logged; ALIVE requires the killer-scout; legal constraints are classified (binding, conditional, nominal, unknown).
- 0.5.1: support check reads each quote in its place on the page (`support-windows`, support-checker agent); live quote recheck with a page cache TTL; page dates read by code from meta tags.

## 0.4.0 (2026-09-28)
- Short-video criteria: alive signal AS7 (proven short-video channel), supporting pattern KP18 (fad without hold), a consumer-impulse price band; advertising rules count as channel risks, not bans.
- A KP4 price route at threshold needs a dated comparator; only a KP15 at threshold removes the D2 shields.
- Builds on 0.3.0: installable marketplace layout with `plugin/` as the installed directory, optional RTK hook, runs in `~/.idea-evaluator/runs`, pattern review (KP15-KP17, wider KP14), killer-scout agent and `STAGE: deepen`.
