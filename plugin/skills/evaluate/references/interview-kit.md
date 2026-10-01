# Interview kit

## Table of contents
1. Purpose and rules
2. Who to ask
3. Where to find them, per facet
4. Question templates
5. Questions never to ask
6. What counts as a commitment
7. Auditing the notes afterwards
8. How the report picks 5 to 8 questions

## 1. Purpose and rules
Desk research tops out at public evidence that people already pay. The kit tells the owner how to get the next rung: facts about past behaviour and commitments from real people. It follows the Mom Test (Fitzpatrick), Migicovsky's "How to Talk to Users" and Savoia's skin-in-the-game scale.

Three rules for every conversation:
1. Talk about their life, not the idea. Show the idea only at the end, if at all.
2. Ask about specific past events, not opinions or the future.
3. Talk less, listen more. Notes where the interviewer spoke more than the interviewee are weak.

Aim for at least 10 conversations per segment, or until new conversations stop teaching anything new. A 20-minute call beats a survey of hundreds.

## 2. Who to ask
Ask every party separately. When the card has `payer_same_as_user: false`, user and payer get separate conversations.

| Party | Why | What they can settle |
|---|---|---|
| User | lives with the pain | Q1 pain, Q2 current workaround, frequency, triggers |
| Payer and decider | owns the budget | Q4 budget line, who signs, procurement steps, price anchor |
| Ex-customers of competitors | already paid and left | why they switched or quit, what the paid tool missed, real churn reasons |
| Current customers of competitors | pay today | spend, satisfaction, switching cost; feeds KP2 and AS1 |
| People who left dead attempts | founders, employees or customers of the prior attempts in `q3.json` `dead_attempts` | the real cause of death and whether it still holds; feeds KP1, KP5 and `what_changed` |
| Performers or intermediaries | for marketplaces and services: the supply side, brokers, installers, distributors | supply willingness, disintermediation, margins |

## 3. Where to find them, per facet

| Facet value | Where to find people |
|---|---|
| customer = consumer | subreddits and forums found in Q1; Facebook, Telegram and Discord groups in the users' language; app-store reviewers of adjacent tools; local community centres and events |
| customer = business | LinkedIn by job title owning the problem; trade associations and chambers; trade-show exhibitor and attendee lists; reviewers on G2 or Capterra (reviews show job title and company size); integration marketplaces of the tools they use |
| customer = government | officials named in procurement award records and tender contacts; public meeting minutes; regulator consultation respondents; municipal budget owners |
| customer = solo_professional | professional bodies and their events; professional forums and subreddits; continuing-education courses; directories of licensed practitioners |
| product_type = hardware | distributors, installers and repair shops; crowdfunding backers of prior devices; trade shows |
| product_type = marketplace | both sides separately: buyers where they complain, sellers or performers in their own groups and job boards |
| market_visibility = low | registries and procurement records from `jurisdictions.md`; industry associations; field visits; warm introductions from the first interviewees |
| ex-customers of competitors | negative and "switched from" reviews on G2, Capterra, app stores, Trustpilot; forum threads "alternatives to X" |
| people who left dead attempts | post-mortem authors; "former" roles at the dead company on LinkedIn; Hacker News comments on the shutdown post; the dead product's review pages |

Ask every interviewee for two more people like them. Warm introductions are the most reliable channel in low-visibility markets.

## 4. Question templates
Fill `<the thing>` and `<the problem>` with the idea's words, phrased the way the target people phrase them. Always keep question 7.

1. What is the hardest part about <the thing>?
2. Tell me about the last time you ran into <the problem>. What happened, step by step?
3. Why was that hard? What did it cost you in time, money or trouble?
4. What, if anything, have you done to solve it? (Nothing tried means the pain is probably not burning.)
5. What do you use today for this, and what did you pay for it last month or last year?
6. What don't you love about the solutions you have already tried?
7. Who else did you consider? What made you choose, or reject, each of them?
8. Who decided on that purchase, and who else had to agree?
9. Which budget did the money come from, and how is that budget set each year?
10. How often does this happen: in the last month, how many times?
11. When you stopped using <competitor or dead attempt>, what was the moment you decided to stop?
12. What would have happened if you had done nothing about it that last time?
13. Walk me through how you found the tool or person you use now.
14. Is there anyone else I should talk to about this, and would you introduce me?
15. (Payer, end of conversation) Would you commit <time, an introduction, a deposit> to try a first version on <date>?

The scary question: each kit contains at least one question whose honest answer could kill the idea (for example "Is the free tool you use now good enough that you would not switch?"). Ask it early enough to hear the answer.

## 5. Questions never to ask
- "Would you use this?", "Would you buy this?", "How much would you pay for this?"
- "Do you think this is a good idea?"
- Feature wish lists ("What features would you want?"); ask about the motive behind a request instead.
- Yes or no questions, and two questions in one.
- Anything the desk research has already answered.

## 6. What counts as a commitment
A lead is real only after they were given a concrete chance to say no. Commitments come in three currencies.

| Currency | Examples | Skin-in-the-game points (Savoia) |
|---|---|---|
| None | compliments, "let me know when it launches", "I would definitely buy", survey answers, likes | 0 |
| Time | confirmed email for a follow-up (1), phone number (10), a scheduled 30-minute demo or feedback session (30), a trial on their own data | 1 to 30 |
| Reputation | introduction to the boss, colleagues or the budget owner; a public testimonial; agreeing to be a named pilot | 30 or more |
| Money | letter of intent with a price, deposit (a 50 USD deposit is 50 points), pre-order or paid pilot (a 250 USD order is 250 points) | 50 or more |

Words without a commitment never count toward a test threshold. A meeting that ends with no next step is a red flag, as are "zombie leads" who meet and praise but never pay.

## 7. Auditing the notes afterwards
The `post-test` skill audits notes sentence by sentence:
- compliment (discarded);
- fluff: generic ("I usually"), future ("I would"), hypothetical ("I might") (discarded unless anchored to a past event);
- past specific (a dated event, an amount paid, a tool used): counts as evidence;
- commitment, with its currency and points.
Notes with only compliments are a zombie result. Scattered answers from one segment suggest the segment is too broad.

## 8. How the report picks 5 to 8 questions
The report builds one interview section per idea from the `interview_questions` of every answer card and of `dossier.json`.

1. Collect all candidate questions with their source card (Q1 to Q7, LAW, DOSSIER).
2. Keep, in this order of priority:
   1. questions created by `agreement: disagree` or by contradictions in `reconcile.json`;
   2. questions that test the `riskiest_assumption` or would set the `cheapest_test` threshold;
   3. questions for critical unmeasured questions (Q2, Q4, Q6) listed in `verdict.json.unmeasured`;
   4. questions for Q7 "why us" when it is "not stated";
   5. the scary question from section 4.
3. Remove duplicates and any question already answered by a finding.
4. Rewrite each kept question into past-behaviour form using the templates in section 4; drop any that stay hypothetical.
5. Always include "Who else did you consider?" (template 7).
6. Stop at 8 questions; if fewer than 5 remain, fill from templates 2, 4, 5 and 8 adapted to the idea.
7. Print each question with the party to ask (user, payer, ex-customer, dead-attempt insider, performer), where to find them from section 3, and the commitment to ask for at the end.
