# Profiles

A profile adds the selection criteria of one programme (an accelerator, an investor, a grant) to an evaluation. It is optional and never part of the core: a profile never changes the verdict, the fatal causes, `need_label` or `p_survive`. It only fills `profile_criteria` in the Q7 answer card and adds a section to the report.

## Activating a profile
- The run header `run.json` carries `"profile": "<name>"` (the file name without `.md`), or `null` for none.
- From a skill, profiles are read at `${CLAUDE_SKILL_DIR}/../../profiles/<name>.md`.

## File format
File name: `<kind>-<programme>.md`, lowercase, hyphens only (for example `accelerator-yc.md`, `grant-eic-accelerator.md`). English only; programme names and quoted criteria are translated, originals are not copied in.

Sections, in this order:

1. `# <Programme> profile`, then an About paragraph: who runs it, what it selects for, and the date the criteria were collected (`as of YYYY-MM`). Files over 100 lines put a table of contents before it.
2. `## Sources`: each source file or URL the criteria come from, with the date read.
3. `## Stages`: the selection stages (application, pitch days, final) with what each stage decides. Omit when the programme has one stage.
4. `## Criteria`: one table with exactly these columns:

| Column | Content |
|---|---|
| `id` | short stable identifier, e.g. `PD2-3` |
| `criterion` | the programme's criterion in plain English, one line |
| `stage` | the stage from section 3 where it is judged |
| `satisfied_by` | the evidence that makes it `met: yes`, stated so a reader can check it |
| `supplied_by` | which part of the run supplies the evidence: `Q1`…`Q7`, `LAW`, `DOSSIER`, `card`, `verdict`, or `OWNER` when only the team can produce it |
| `source` | source from section 2 |

5. `## Programme filters`: rules the programme applies outside the pitch criteria (eligibility, weak patterns it rejects, deadlines that make some ideas impractical). Same table shape as section 4.
6. Optional sections specific to the programme (application form, how the conductor uses this profile).
7. `## Gaps`: what the profile could not source (weights, rubric scales, missing stages). Always last.

## How the conductor applies a profile
1. After Q1 to Q7 are written, the Q7 owner reads the profile.
2. For each row of `Criteria` and `Programme filters`, it writes one entry to Q7 `profile_criteria`: `{"criterion": "<id>: <criterion>", "met": "yes|no|unknown", "note": "..."}`.
   - `yes` only when the note cites finding IDs or answer-card fields that meet `satisfied_by`.
   - `no` only when findings contradict it.
   - `unknown` otherwise, including every `OWNER` row that the idea text does not already document; the note then says what the owner must produce.
3. `profile_criteria` never enters the verdict table, `fatal`, `need_label` or `p_survive`. A team criterion is never a reason for DEAD.
4. The report prints a "Profile: <programme>" section after the verdict: met, not met, unknown, and the owner actions from the `OWNER` rows.

## Adding a profile
Collect criteria from the programme's own pages or rules, cite them, map every criterion to a question or to `OWNER`, list the gaps, and do not invent weights. When two sources disagree (for example two editions of a programme), keep the newer one and record the disagreement under `Gaps`.
