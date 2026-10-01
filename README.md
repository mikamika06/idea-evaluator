# Idea Evaluator — Claude Code plugin that tells you if your startup idea is dead

![A grim reaper in an office suit stamps a stack of startup ideas DEAD while one lands in the ALIVE tray](docs/banner.png)

Idea Evaluator (`idea-evaluator`) is an open-source startup idea validator that runs inside your own Claude Code. You describe an idea in a few sentences; it researches the market on the public web and returns exactly one verdict: `DEAD`, `ALIVE` or `INSUFFICIENT_DATA`, with the evidence, the riskiest assumption and the cheapest 14-day test that would decide it. It is for founders, indie hackers and product people who want to find out what kills an idea before spending months on it.

**How it differs from asking a chatbot or using an AI idea validator website**

- It looks for the cause of death, not for reasons to like the idea. A separate kill-check agent searches for free substitutes, platforms that already ship the feature, earlier startups that died with the same model, cost to serve and licences.
- Every finding carries a verbatim quote and a link, and code checks that the quote is on the page. An auditor rechecks the decisive quotes live and whether each quote supports its claim in context.
- The verdict comes from a deterministic script (`bin/decide`) over a sheet of 18 kill patterns and 7 alive signals, not from the model's mood. An author-blind judge agent gives a second opinion.
- It says `INSUFFICIENT_DATA`, with the facts to collect, rather than killing a real success on thin evidence or rescuing an idea with hypothetical futures.
- MIT-licensed, runs on your existing Claude Code login, no extra API keys or accounts; run files stay on your machine.

## Quick install

```bash
claude plugin marketplace add mikamika06/idea-evaluator
claude plugin install idea-evaluator@idea-evaluator
```

Then, in any Claude Code session:

```
/idea-evaluator:evaluate An AI meeting note-taker for B2B sales teams that pushes notes into the CRM, USD 20 per user per month
```

Requirements, header lines and measured cost are below.

## Example output

The opening of a real full-depth run (plugin 0.8.0, 2026-10-01) on an AI meeting note-taker for B2B sales teams at USD 20 per seat, sold to small and mid-size teams in the US and EU. It stopped early on a strong kill pattern, so the reconcile pass and kill check did not run, and its report says so:

```
Verdict: DEAD · need: NEEDED · p_survive 0.1
Rule D1: one strong pattern at threshold with no allowed rebuttal. KP3: the CRMs
the payer already pays for (HubSpot Sales Hub, Pipedrive) ship the same notetaker
at no extra charge (C-0001..C-0005), and Zoom paid plans bundle AI meeting
summaries (G-0004).

In plain words: The need is real. [...] The problem is that two of the three CRMs
the idea targets now do this themselves at no extra cost. Pipedrive added its
notetaker to every plan on 2026-09-29 (C-0003), and HubSpot includes one with paid
Sales Hub seats (C-0001). [...] Only go on if a 14-day test shows that sales teams
will pay for something the bundled tools miss.

Cheapest test (14 days): contact 60 sales managers of teams with 5-30 reps [...]
ask for a paid 1-month pilot at USD 20 per seat. Pass if at least 3 teams pay for
a pilot, or 6 sign a dated letter of intent. Fewer confirms the kill.

Sources: 109 findings, 96 opened and confirmed by check-quote. The audit checked
21 decisive findings: all 21 found.
```

The full report also has the seven answers, the pattern sheet, competitors with prices, the judge's opinion, an interview kit and an honest-limits section listing what the run did not verify.

## FAQ

**Can AI validate a startup idea?**
Not fully. Only customers who pay validate an idea. What this plugin can do is check an idea against public evidence: who already sells it and at what price, who tried and died, whether the payer has a budget, whether the economics close. It is better at killing ideas with a documented cause of death than at blessing them: `ALIVE` needs a measured pull signal and a passed kill check, and even then it is a reason to run the cheapest test, not a forecast of success.

**How is this different from asking ChatGPT or Claude "is my startup idea good"?**
A single chat answer is one model's opinion, usually agreeable, with sources you have to check yourself. Here six research agents work in parallel, every finding must quote a page that code has confirmed, a separate agent hunts for the cause of death, an auditor rechecks decisive quotes, a fixed script turns the evidence into the verdict and a blind judge reviews it. When the evidence is thin it says so.

**How much does a run cost and how long does it take?**
A run is billed like any Claude Code session: on a subscription it is drawn from plan limits, on the API it costs roughly USD 14.7 and 28 minutes for a full run, USD 8.9 and 15 minutes with `MODEL: sonnet`, and USD 3.9-5.6 for a shallow `DEPTH: calibration` screen (measured on 0.8.0, see the table below).

**How accurate is it?**
Calibration is still thin. On five ideas with a known outcome the shallow `DEPTH: calibration` screen killed no good idea but returned `INSUFFICIENT_DATA` for four of them. Verdicts on the same idea can differ between runs because web search results differ; each report shows the sheet it used. See Limits.

**Does it work for ideas outside the US or in other languages?**
You can write the idea in any language and get the report in another with `OUTPUT_LANGUAGE`. Research quality depends on what is public online: markets that leave little trace (offline B2B, small local trades, communities the agents cannot read) tend to end as `INSUFFICIENT_DATA`.

**Does it send my idea anywhere?**
The plugin itself uploads nothing. It makes web requests to public pages and keyless public APIs (Hacker News Algolia, the Arctic Shift Reddit archive, the Wayback Machine) and uses Claude Code's own search; run files are written to `~/.idea-evaluator/runs/`. Your idea goes to the model provider like any Claude Code prompt.

## What it does

A research pipeline with independent checks; every step writes files you can read.


- Rewrites the idea as a card (customer, payer, market, price, sales motion, business kind, and what it had to assume) and, unless `MODE: batch` is set, asks you to confirm or correct it.
- Answers seven decisive questions (pain, current spend, competitors and dead predecessors, payer and budget, channel, unit economics, law and timing) with six research agents working in parallel. Every finding carries a verbatim quote and a link, and code checks that the quote is on the page.
- Runs a kill check: a separate agent searches for the real cause of death (free substitutes, a platform that already ships it, prior deaths of the same model, cost to serve, licences, and more).
- Audits the decisive quotes live, checks that each quote supports its claim when read in context, and fills a sheet of eighteen kill patterns and seven alive signals.
- `bin/decide`, a deterministic script, turns the sheet into the verdict. An author-blind judge agent gives a second opinion; a dispute between a DEAD sheet and the judge ends as `INSUFFICIENT_DATA`.
- Writes `report.md` with a plain-words summary, the pattern sheet, the riskiest assumption and the cheapest 14-day test that would decide it.

It never rescues an idea with hypothetical futures and prefers `INSUFFICIENT_DATA`, with the facts to collect, over killing a real success on thin evidence.

## Install

Run once in a terminal:

```bash
claude plugin marketplace add mikamika06/idea-evaluator
claude plugin install idea-evaluator@idea-evaluator
```

Requirements: Claude Code with a working login (subscription or API) and Python 3 on `PATH`; the scripts use only the standard library. No API keys, accounts or paid services are needed beyond your Claude Code login. A run is billed like any other Claude Code session: on a subscription it is drawn from plan limits, on the API it costs the amounts in the table below.

The installer may say that the `output_language` option is not set; the default is English, and you can change it with `/plugin configure idea-evaluator@idea-evaluator` or per run with `OUTPUT_LANGUAGE`.

Optional add-ons, not required and not installed by the plugin:
- For shorter chat output you can install [caveman](https://github.com/JuliusBrussee/caveman) (`claude plugin marketplace add JuliusBrussee/caveman`, then `claude plugin install caveman@caveman`). It only affects the style of the main session's messages; research agents, files and verdicts are the same without it.
- For shorter shell output you can install [RTK](https://github.com/rtk-ai/rtk) yourself; the plugin no longer touches it.

## Use

In any Claude Code session:

```
/idea-evaluator:evaluate <your idea in any language>
```

The plugin shows how it understood the idea and waits: reply with corrections or `ok`. Then it researches and decides. While it works, a progress hook posts a message in the chat as each of seven stages finishes (card, research, reconcile and pass 2, kill check, audit, verdict and judge, report) with the stage number, elapsed time and what the run files show: counts, competitors with prices and links, dead attempts, who pays today, red flags warming up, live signals, audit numbers, the judge's agreement and the verdict. It is code, not the model, so it appears even under terse output rules. Labels follow `OUTPUT_LANGUAGE` (English and Ukrainian built in; other languages get English labels); quoted facts stay as the run files state them.

It ends with a readable summary in the chat: the verdict with `p_survive`, a plain-words explanation and why this verdict, the seven answers, the five key findings with links, the competitors, the riskiest assumption and the cheapest 14-day test, and the path of the full report `~/.idea-evaluator/runs/<date-time>/report.md`.

### Header lines

Optional lines before the idea text:

| Line | Effect |
|---|---|
| `DEPTH: calibration` | shallow screening: 3 searches per question, Sonnet research agents, script audit, short report. Without `DEPTH` (or with `DEPTH: full`) the run is the full evaluation |
| `MODEL: sonnet` | every subagent runs on Sonnet; the session you run the command in keeps its own model. Default `MODEL: opus`: agents use their own defaults. At full depth it cost about 40% less and took half the time in one measured run, with fewer findings (57 against 100) and the same verdict |
| `AS_OF: 2024-06` | judge the idea as of that month, using no evidence published later |
| `OUTPUT_LANGUAGE: Ukrainian` | language of the report and of the progress labels |
| `MODE: batch` | no questions during the run (the card is not shown for confirmation) |

Example:

```
/idea-evaluator:evaluate DEPTH: calibration
OUTPUT_LANGUAGE: English
A shift-log app for UK cafes with 1-9 staff that replaces WhatsApp rotas. Subscription per business.
```

### Measured cost and time

Cost is the API-price estimate Claude Code reports for the whole run; on a subscription it is drawn from plan limits instead. Measured on plugin 0.8.0, 2026-09-30:

| Depth and model | Runs | USD per run | Wall time per run |
|---|---|---|---|
| full, default (Opus agents) | 1 | 14.7 | 28 minutes |
| full, `MODEL: sonnet` | 1 | 8.9 | 15 minutes |
| `DEPTH: calibration` | 8 | 3.9-5.6 | 7-20 minutes (three runs in parallel) |

Earlier full runs on 0.6-0.7 measured USD 19.5-21 and 28-34 minutes. At calibration depth every subagent already runs on Sonnet, so `MODEL: sonnet` changes nothing there.

### A shorter command

Claude Code user commands can call the plugin. Create `~/.claude/commands/idea.md` with:

```markdown
---
description: Evaluate a startup idea with idea-evaluator
argument-hint: "[header lines] <idea text>"
---
Invoke the Skill tool with skill `idea-evaluator:evaluate` and args exactly as given below, then follow the skill.

$ARGUMENTS
```

Then type `/idea <your idea>`; header lines work the same way.

## What it runs on your machine

- Web requests to public pages and keyless public APIs (Hacker News Algolia, the Arctic Shift Reddit archive, the Internet Archive Wayback Machine), besides Claude Code's own WebSearch and WebFetch. Page text is cached in the system temp directory (`idea-evaluator-pages`) for 7 days.
- Local Python 3 scripts from `plugin/bin`: page text and quote check, company directory lookup, run validation, the verdict rule. They need only the standard library.
- Run files in `~/.idea-evaluator/runs/<date-time>/` (cards, findings, audit, verdict, report). Nothing is uploaded anywhere by the plugin itself.

## Hooks

Installed hooks are active in every Claude Code session, so here is exactly what they do:

- `Stop` (`bin/stop-hook`): keeps an unfinished evaluation from ending before its files are complete. It acts only on a run that this session started, whose `run.json` says `running` and is less than 12 hours old, and only when no background agent or background command of the session is still pending. It blocks at most 6 times per run. In any other session it does nothing.
- `PostToolUse` on Agent, Task, Bash, Write, Edit and MultiEdit (`bin/progress-hook`): posts the stage messages described above for the run this session started. Silent otherwise; it never blocks a tool and never goes online.

Both hooks read only the run files and the session transcript whose path Claude Code passes to the hook. They read no settings, credentials or other files under `~/.claude`, run no external programs and make no network requests.

## Company directory

The plugin ships a small offline company directory (about 6,700 companies, plain JSON Lines in `plugin/directory/companies-NN.jsonl` with the source list in `plugin/directory/meta.json`): the Y Combinator directory from the [yc-oss API](https://github.com/yc-oss/api) and the dead companies of the Failory cemetery, CB Insights post-mortems and a Kaggle startup-failure dataset, with name, domain, founding year, death year, status, cause and source links. Research agents look up competitors and dead predecessors in it with `bin/company-dir` before searching the web. It is read-only and never goes online. For an `AS_OF` date, deaths, statuses and failure-collection links that came later are hidden. Every row is a lead: agents still open a source page and quote it before a fact counts as evidence.

## Limits

- It judges an idea from public evidence only. Markets that leave little trace online (offline B2B, small local trades, non-English communities the agents cannot read) tend to end as `INSUFFICIENT_DATA`, and the report lists what to collect.
- Verdicts on the same idea can differ between runs, because web search results and agent reading differ. Borderline ideas can move between `DEAD` and `INSUFFICIENT_DATA`; the rule never flips a verdict without a changed pattern sheet, and each report shows the sheet it used.
- Famous companies are recognised by the model, so an `AS_OF` date in the past hides later web evidence but not what the model already knows.
- `ALIVE` needs a measured pull signal and a passed kill check; it is a reason to run the cheapest test, not a forecast of success.
- A full run takes about half an hour and a noticeable share of a subscription's limits; use `DEPTH: calibration` to screen many ideas.
- `DEPTH: calibration` is a first screen, not a decision. On five ideas with a known outcome it killed no good idea but returned `INSUFFICIENT_DATA` for four of them, mostly because the support checker often rates a quote as only partly supporting its claim, and partial support does not count. Use a full run before acting on a verdict.
- Page fetches can fail on sites that block scripts; such quotes count as unverified and the report says so.

## Changelog

See `CHANGELOG.md`.

## Credits

Built by the Blyzki team — https://blyzki.com

## License

MIT, see `LICENSE`.
