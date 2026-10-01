# Anti-patterns

| Anti-pattern | Rule |
|---|---|
| Missing data scored as low | unmeasured questions go to `unmeasured`, never move `p_survive` |
| Crowded market as death | see false kills; paid competitors are evidence of a market |
| English-only search | every language of the language plan appears in a `search_matrix` |
| Found precedent ignored | dead attempts feed KP1 and KP5 only with the what-changed search |
| Verifier never opens links | a finding without `opened: true` and `quote_check: found` cannot support a kill pattern or an alive signal |
| Summary instead of source | quotes are copied from raw page text and confirmed with `check-quote`, never from a tool's summary |
| Unlimited angles | only the methods in `questions-q1-q7.md` and channels in `facets-and-routing.md`; no new angles mid-run |
| No competitors = open market | set `invisible_player_risk` and add the interview question "who else did you consider?" |
| Anachronism | ignore the evaluated company itself and any evidence published after `as_of` |
| Flip under pressure | only new findings change a verdict; restating doubts does not |
| Paraphrase drift | answer cards reference finding IDs; the judge reads cards, never raw pages |
| Averaging disagreement | disagreeing methods become `partial` plus an interview question |
| Gross-ticket economics | KP4 is computed from contribution after platform take, cost of goods, discounts and real acquisition cost |
| Endless loops | at most 2 back-loops per run and at most 2 auditor returns per agent |
| Verdict leaks into research | researchers never see the verdict rules or other questions' conclusions |
| Author bias | the card is third person; the judge never sees the original text |
| Invented numbers | every number in a report points to a finding ID or is labelled an assumption |
| Kill signals waved through one by one | the pattern sheet lists all fourteen patterns; three firing together with no paying or obliged buyer is DEAD (D2) |
| Absence of complaints about a free tool read as missing evidence | continued use of a free substitute with no paid alternative gaining traction is KP2 evidence |
| A new free substitute counted as "what changed" | it counts for KP2 or KP3, never as AS6 |
| Card drift before the verdict | the verdict judges `card.v1.json`; a pivot is judged beside it |
| Hedged middle verdict | `INSUFFICIENT_DATA` must name the facts that would move it to DEAD or ALIVE |
