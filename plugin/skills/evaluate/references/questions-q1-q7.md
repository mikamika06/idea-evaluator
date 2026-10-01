# Seven decisive questions

## Table of contents
1. Rules for every question
2. Q1 Who and pain
3. Q2 Current spend
4. Q3 Competitors and graveyard
5. Q4 Payer
6. Q5 Channel
7. Q6 Rough economics
8. Q7 Why now, why us
9. Law check (KP7)
10. Thirteen life aspects
11. Depth: shallow and deep
12. Ownership

## 1. Rules for every question
- Each question has a fixed set of methods below. Methods are never added mid-run.
- Two methods that agree make the answer `measured`. One method with data, or methods that disagree, make it `partial`. No data makes it `unknown`.
- Disagreement becomes an interview question; it is never averaged away.
- Record evidence for and against the idea. Record `results: null` when a source fails and `0` when it returns nothing.
- Search every language in the card's language plan; phrase queries the way the target people phrase them.
- Ignore the evaluated company itself and any evidence published after `as_of`.
- Missing evidence is `unknown`, never a negative answer.

## 2. Q1 Who and pain
Question: who exactly are these people, how many, and does it really hurt?
Methods:
1. Own words: posts, threads, reviews and comments by the target people, in their language and in their communities (forums, subreddits via Arctic Shift, Facebook/Telegram/Discord groups visible to search, app-store reviews of adjacent tools, trade forums).
2. Numbers: official statistics, registries or industry reports that size the group and show whether it grows.
3. Life dossier (life-dossier agent): the thirteen aspects, ending with "what really hurts" and "do they really need it".
Can yield: `INSUFFICIENT_DATA`, a segment change (loop "pain elsewhere"), `NEEDED_BUT_DIFFERENT`, KP14 (trust sits in a specific person the idea would replace).

## 3. Q2 Current spend
Question: how do they cope today and what do they already spend in money or time?
Methods:
1. Money already paid for workarounds: prices of tools, services, freelancers or staff they use today.
2. Job postings for the work the idea would replace or support (count, salary, country).
3. Complaints about current tools: reviews (G2, Capterra, app stores, Trustpilot), forum threads "what do you use for…".
For a new market: signs of non-consumption (people doing without, costly manual effort).
Can yield: KP2 (free workaround in use), KP8 (resigned users), KP14 (people pay or rely on a specific person for the job and say why, or buy the result done for them instead of tools), KP17 (the job is done once or rarely), AS1 (money already paid for a worse substitute), AS3.

## 4. Q3 Competitors and graveyard
Question: who already does this, is it used, who died trying and why?
Methods:
1. Channel × language competitor matrix from `facets-and-routing.md`, with usage evidence per competitor.
2. Invisible players per jurisdiction from `jurisdictions.md` (registries, procurement, trade shows, job boards), mandatory when market visibility is low.
3. Failure sources: local company directory `company-dir search --dead`, Failory, CB Insights post-mortems, startups.rip, Y Combinator inactive companies, Hacker News, web search for "shut down / closing / post-mortem"; plus the explicit what-changed search.
Can yield: KP1, KP2, KP3 (including the closing gap: dated improvements by the leader on the idea's axis), KP5, AS4, AS5, AS6.

## 5. Q4 Payer
Question: who pays, do they have a budget, who decides?
Methods:
1. Budgets and current spend of the payer: what they pay today for similar things (vendor pricing pages, procurement records, annual reports, salary lines).
2. Buying roles: who signs, procurement rules, job titles that own the budget (job postings, procurement portals, sales playbooks of competitors).
3. Payer incentives: what the payer gains or avoids (regulatory fines, revenue, cost), with sources.
Can yield: KP6, KP13 (the payer earns from the problem continuing), AS1, AS2.

## 6. Q5 Channel
Question: how does a small team reach the first 10 and first 100 customers?
Methods:
1. Where the people cluster: named communities, events, associations, marketplaces, integrations with member counts.
2. Price versus sales motion: whether the price band can pay for the sales motion (self-serve under 2k per year, sales-led above 10k, tender for government).
3. How competitors acquired their first customers (founder interviews, launch posts, case studies).
For consumer products also check the short-video channel: comparable products in the category that grew through TikTok, Reels or Shorts with numbers (news, TikTok for Business success stories, TikTok Shop category data), hashtag and search volume for the category on TikTok, whether the product has a visual proof moment or can be sold by a person on camera, and whether comparable spikes faded.
Can yield: KP6 below threshold (no channel within the price band), KP10, AS7 (proven short-video channel), KP18 (fad without hold), KP16 (the product reaches customers only through an integration with a system they run, and those systems differ).

## 7. Q6 Rough economics
Question: does it add up roughly in the realistic case?
Methods:
1. `economics-template.md` filled with sourced inputs: price, platform take, cost of goods or service delivery, discounts, churn, real acquisition cost.
2. Benchmarks: the same numbers for the closest competitors or dead attempts (public pricing, filings, post-mortems).
Compute an optimistic and a realistic case step by step. Order of magnitude is enough; every input is either a finding or a labelled assumption.
Can yield: KP4 (price above the payer's current cost of the same step), KP15 (realistic case fails with sourced inputs that belong to the model; unfixable when the optimistic case fails too), KP9, KP12, KP16 (integration cost per customer system), KP17.

## 8. Q7 Why now, why us
Question: what changed that makes this possible now, and what advantage does the team have?
Methods:
1. Changes: technology, regulation, cost, behaviour, distribution, dated and sourced (reuse Q3 what-changed findings).
2. Advantage: stated team facts from the idea text only; access, data, distribution or know-how that others lack. If none is stated, write "not stated" and add an interview question.
3. Profile criteria when a profile is active (`profiles/<name>.md`).
Can yield: AS2, AS6, KP11.

## 9. Law check (KP7)
Runs alongside all questions, owned by position-analyst. For each jurisdiction on the card: does the law forbid the product, or require a licence, certification or registration, and how long does it take? Evidence is the statute, regulation or regulator page. Write `law.json`.

## 10. Thirteen life aspects
Built for the user and, when different, for the payer.

| # | Aspect | Evidence that counts | Signal for the verdict |
|---|---|---|---|
| 1 | Who they are | a portrait with a number and a source; growth or decline | invented portrait: unknown |
| 2 | Day, week, year | the hours, days or months when it hurts | no moment of pain: weak need |
| 3 | Money | income versus price versus current spend | price above budget or current spend: KP4 input |
| 4 | Time and energy | hours spent; how many minutes a product can take | no time or energy: risk and test |
| 5 | Emotions | verbatim quotes of fear, shame, fatigue, anger | emotion without a quote does not count |
| 6 | Whom they trust | named trust channels, and for this job whether trust sits in a specific person (tutor, carer, doctor, relative, neighbour), in institutions or in companies | product arrives through a distrusted channel: risk; trust in a specific person the idea replaces: KP14 |
| 7 | Mindset | a stated norm with a source, else "agent hypothesis"; the norm about a person versus a system for this job | product demands behaviour against the norm: risk; "a person, not an app" norm: KP14 input |
| 8 | Law | rule number and effective date | forbidden or licence: KP7; not yet in force: LATER |
| 9 | Technology | the tools they already use daily | needs a tool they lack, or competes with a free installed one: KP2 input |
| 10 | Weaknesses | dependencies, missing skills, vulnerability | product could harm them: risk and ethics flag |
| 11 | How they cope now | workarounds with prices | free workaround in use: KP2 input |
| 12 | What really hurts | one sentence "the pain is in Y" with evidence and who already pays for Y | pain elsewhere: loop and NEEDED_BUT_DIFFERENT |
| 13 | Do they really need it | actions, not words: money spent, days lost, people quitting | resigned or "nice but not needed": NOT_NEEDED |

## 11. Depth: shallow and deep
- `shallow` (pass 1): at most 6 searches and 4 opened pages per question, stop when two methods agree.
- `deep` (pass 2): only the questions and focus given by the conductor; at most 15 searches and 10 opened pages per question; must try every method not yet tried and every language not yet covered.
- `calibration` (pass 1 of a calibration run): at most 3 searches and 2 opened pages per question (Q7 and LAW: 2 searches and 1 page each); one method with data is enough; the users' language and English only. Aim to finish within 6 minutes. Always check the kill patterns and alive signals your questions can yield (the "Can yield" line) and record each as a candidate or say in `unknowns` that it was not checked.
  Write at most 6 findings per agent, choosing those that bear on a "Can yield" code.
- `calibration-deep` (pass 2 of a calibration run, only when a DEAD or ALIVE decision hinges on the focus): at most 2 searches and 2 opened pages, only the FOCUS, at most 3 new findings.

## 12. Ownership

| Agent | Writes | Finding prefix |
|---|---|---|
| voice-scout | q1.json, q2.json | V |
| life-dossier | dossier.json | L |
| competitor-scout | q3-competitors.json | C |
| graveyard-scout | q3-graveyard.json | G |
| position-analyst instance 1 | q4.json, q5.json | P |
| position-analyst instance 2 | q6.json, q7.json, law.json | R |
| auditor | audit.json | A |
| killer-scout | killcheck.json | K |
| judge | judge.json | none |
