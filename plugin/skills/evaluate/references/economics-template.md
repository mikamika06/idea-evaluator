# Economics template (Q6)

## Table of contents
1. Purpose and output fields
2. Inputs
3. Acquisition cost benchmarks
4. Optimistic and realistic cases
5. Computation, step by step
6. KP4 and KP15 rules (price and cost to serve)
7. Common traps
8. Worked example A: service marketplace (made-up numbers)
9. Worked example B: hardware device (made-up numbers)

## 1. Purpose and output fields
Q6 asks whether the idea adds up roughly in the realistic case, and whether any sourced path closes the gap. Order of magnitude is enough. Every number is either a finding or a labelled assumption, and every step is written out so a reader can redo it by hand.

The Q6 answer card adds these fields to the common part (`schemas.md` section 6):

| Field | Content |
|---|---|
| `inputs` | list of `{"name", "value", "unit", "basis": "finding\|assumption", "finding_ids": []}`; one entry per input in section 2, per case when the case values differ (suffix the name with `(optimistic)` or `(realistic)`) |
| `steps` | list of strings, one per computation line in section 5, with the numbers substituted |
| `optimistic` | `{"contribution_per_customer": number, "cac": number, "max_revenue_per_customer": number}` |
| `realistic` | same three numbers for the realistic case |
| `currency` | ISO 4217 code used for every money value |
| `realistic_case_fails` | `true` when the realistic case fails the test in section 6, `false` when it passes, `null` when an input needed for the test is missing |
| `optimistic_case_fails` | same test on the optimistic case; `true` means no sourced path closes the gap |
| `deciding_inputs_sourced` | `true` when every input that makes the realistic case fail is a finding with `quote_check: found` or a sourced benchmark for this exact category; `false` when any of them is an assumption |
| `price_vs_current_cost` | the price divided by the payer's sourced current cost of the same step (Q2), or `null`. When the payer does the step with staff, derive the unit cost as loaded wage per hour times sourced time per unit (or monthly wage divided by sourced units per month) and show it in `steps`; when with a tool or service, use its price per unit. Leave `null` only when no wage, time or price for the step could be sourced. |

Definitions of the three numbers, used everywhere in this plugin:
- `max_revenue_per_customer`: net revenue the company keeps from one customer over the customer's whole expected lifetime, after platform and payment take, refunds and discounts, before cost of goods or delivery.
- `contribution_per_customer`: `max_revenue_per_customer` minus all variable cost of serving that customer over the same lifetime (cost of goods, delivery, supplier or performer share, support, hosting, AI usage, one-time onboarding subsidies). Acquisition cost is not subtracted here.
- `cac`: real cost of acquiring one paying customer through the channel the idea will actually use.

## 2. Inputs
Collect each input with a source. When no source exists, write a labelled assumption and say why the value is plausible.

| # | Input | Unit | Where to find it |
|---|---|---|---|
| 1 | Price and price unit | currency per unit (per order, per seat per month, per device) | card `price_unit`; competitor pricing pages; procurement awards |
| 2 | Purchases per period | units per customer per month or year | usage frequency from Q1 and the dossier (aspect 2); competitor case studies |
| 3 | Platform and payment take | % of price or fixed fee | app-store terms, payment processor pricing, marketplace fee pages |
| 4 | Supplier or performer share | % of gross ticket | competitor commission pages, performer forums, job ads for the performer role |
| 5 | Cost of goods or delivery per unit | currency per unit | bill of materials, supplier quotes, API price times usage, hourly wage times hours |
| 6 | Discounts and subsidies | currency or % | first-order discounts, free months, dealer margins, volume discounts of competitors |
| 7 | Gross margin | % of net revenue | computed from 1 to 6; cross-check with public filings of the closest competitor |
| 8 | Churn or retention | % per month or expected lifetime in months | competitor disclosures, reviews mentioning cancellation, category benchmarks |
| 9 | Acquisition cost by channel | currency per paying customer | Q5 channels; sourced benchmarks in section 3; competitor disclosures |
| 10 | Sales cycle | days or months from first contact to payment | card `sales_motion`; competitor sales pages; procurement timelines |
| 11 | One-time costs per customer | currency | onboarding, installation, certification per unit, integration work |

The sales cycle does not enter the arithmetic directly. It sets the realistic CAC (a sales-led cycle of 6 to 12 months carries salaried time) and it is reported in `steps` as a cash-flow risk.

## 3. Acquisition cost benchmarks
Use a finding about the idea's own channel first. When none exists, use a benchmark range and mark the input `basis: assumption`, naming the benchmark in `steps`.

| Benchmark | Value | Source note |
|---|---|---|
| CAC for SaaS | 100 to 500 USD | practitioner rule of thumb; replace with a sourced figure when one exists |
| CAC for e-commerce | 20 to 200 USD | same lecture |
| CAC for consumer subscriptions | 30 to 150 USD | same lecture |
| CAC for professional services | 200 to 1,000 USD | same lecture |
| Healthy lifetime value to CAC | at least 3 to 1; payback within 12 months for SaaS | same lecture; Aulet, Disciplined Entrepreneurship, step 19 |
| Visitor to paid conversion | 1 to 4% for prices under 50 USD; 0.5 to 2% for higher prices or subscriptions | Walling |
| Price band versus sales motion | under 2k USD per year: self-serve and inbound only; 2k to 10k: inside sales, cycle 1 to 3 months; over 25k: enterprise, cycle 6 to 12 months | Hale; a low ticket with a long complex sale is a dead zone |
| Monthly retention compounding | 95% monthly keeps 54 of 100 customers after a year; 90% keeps 28 | arithmetic |

For B2B the channel cost is the cost of a sale (people, demos, pilots), never the cost of an app install. Paid ads as the only channel are a risk even when the arithmetic works.

## 4. Optimistic and realistic cases
- Optimistic: every uncertain input is set at the favourable end of its sourced range (highest price seen, lowest cost, lowest churn, cheapest channel with evidence). An assumption in the optimistic case must favour the idea.
- Realistic: the median or most common value found; when only one source exists, the source value; when none exists, the benchmark midpoint.
- Lifetime: expected lifetime is `1 / monthly churn` from a finding. Without a churn finding use the realistic benchmark for the category: consumer app or consumer subscription 6 months; consumer marketplace buyer 6 months of sourced order frequency; SMB software 24 months; mid-market or enterprise software 36 months; services retainer 18 months. The optimistic lifetime is at most 1.5 times the realistic one and never above 36 months. One-time purchases have a lifetime of one purchase plus sourced repeat purchases.
- Free consumer products: only the sourced paying share counts as customers; revenue from advertisers or venues uses the advertiser as the customer, with its own price, lifetime and CAC.
- The same inputs, units and currency are used in both cases; only values differ.

## 5. Computation, step by step
Write each line into `steps` with the numbers filled in. Always start from the gross ticket and walk down to contribution; never compare CAC with the gross ticket.

1. Gross ticket per unit = price.
2. Net revenue per unit = price − platform and payment take − supplier or performer share − per-unit discount.
3. Variable cost per unit = cost of goods or delivery + support + hosting or AI usage per unit.
4. Contribution per unit = net revenue per unit − variable cost per unit.
5. Units per lifetime = purchases per period × expected lifetime (section 4 caps).
6. `max_revenue_per_customer` = net revenue per unit × units per lifetime − one-time discounts or subsidies.
7. `contribution_per_customer` = contribution per unit × units per lifetime − one-time discounts, subsidies and one-time costs per customer.
8. `cac` = channel cost per paying customer for the channel chosen in Q5.
9. Gross margin = contribution per unit / net revenue per unit (reported, not decisive).
10. Ratio = `contribution_per_customer` / `cac`; payback in months = `cac` / monthly contribution (reported as risk when the realistic ratio is below 3 or payback exceeds 12 months for SaaS).
11. Check: does the result depend on a single assumption? Name it; it is a candidate riskiest assumption.

## 6. KP4 and KP15 rules (price and cost to serve)
A case fails when either
- `contribution_per_customer` ≤ 0, or
- `cac` > `max_revenue_per_customer`.

Set `consumer_impulse: true` when an individual buys the product for themselves at USD 50 or less per purchase. Propose KP4 (price above what the payer pays) in `kill_candidates` when `price_vs_current_cost` is above 1.5 (above 3 with `consumer_impulse: true`) with no axis where the idea is ten times better (threshold met when both sides are findings, below threshold when one is an assumption).

Propose KP15 (cost to serve eats the price) when:
- `realistic_case_fails: true`, `deciding_inputs_sourced: true`, and the deciding cost is part of the model: two or more same-model post-mortems cite it, or the cost inputs come from two or more independent providers (threshold met); or
- `realistic_case_fails: true` with an assumed deciding input, or the cost is one company's (fires below threshold).
Mark KP15 `unfixable` when `optimistic_case_fails: true` as well.

Also record `uses_per_customer` evidence (how often one customer needs the job); a one-off or set-and-forget job with a model that needs repeat use is a KP17 input. Name any sourced path that would change the result (falling model prices, a higher tier, a cheaper channel, density); a path with evidence goes into the answer as a possible rebuttal.

The computation in `steps` always starts from the gross ticket and subtracts take, cost, discounts and real acquisition cost. Missing inputs give `null` flags, `status` at most `partial`, and a line in `unknowns`.

## 7. Common traps
| Trap | What goes wrong | Rule |
|---|---|---|
| Marketplace take versus GMV | Revenue computed from the full order value; past validators gave dead marketplaces lifetime-value-to-CAC ratios of 487 to 1 and 187 to 1 this way | revenue is the take rate on GMV minus payment fees and first-order subsidies; supply acquisition is a second CAC |
| Disintermediation | Buyer and performer meet once, then trade directly | repeat purchases in the realistic case count only with evidence that customers stay on the platform |
| Hardware bill of materials | Only the component cost is counted | add assembly, packaging, shipping, warranty reserve, returns, distributor or dealer margin, and certification amortised over a sourced unit volume; the path to sales is typically 2 to 4 times longer than for software |
| Certification and compliance | Treated as a one-off footnote | medical, radio, safety or food certification cost and time enter one-time costs; the time enters the sales cycle |
| Service businesses' labour | Gross margin assumed to be software-like | skilled labour hours per customer × sourced wage; wages can rise faster than prices (one past case: performer wages up 39% in a year) |
| AI usage cost | Ignored or taken at today's price forever | tokens or calls per user × current API price; a falling price is a named path, not a reason to skip the line |
| Freemium | All users counted as paying | only the paying share with a source; the free users' serving cost is a variable cost of the paying ones |
| Price above the customer's cost of the step | Price exceeds what the step costs the customer today (e.g. a buyer spends 1.5 to 4 EUR per case while the idea charges 5 to 10) | compare price with current spend from Q2; above it without a 10x axis is an input to KP2 and KP4 |
| Integration per customer system | The product must connect to each customer's own system and the cost is left out | cost per integration × systems needed to cover the first market enters one-time costs; many systems with no dominant one is a KP16 input |
| One-time need | Lifetime set as if recurring | a need that happens once per customer has a lifetime of one purchase; a KP17 input |
| Subsidy-dependent market | Revenue assumes a subsidy or rule that may be withdrawn | name the rule and its date; a subsidy already cut to zero feeds KP15 and KP11 |

## 8. Worked example A: service marketplace (made-up numbers)
All numbers below are invented for illustration and are not findings. Idea: a marketplace for home cleaning in one city. Currency USD.

Inputs: order value 60; take rate 20%; payment fee 3% of order value; insurance and support 2 per order; first-order discount 10 (paid by the platform); orders per year 12 (optimistic), 4 (realistic); lifetime 9 months (optimistic), 6 months (realistic, consumer marketplace benchmark); CAC 60 via local social ads (optimistic), 120 (realistic).

Optimistic steps:
1. Gross ticket = 60.
2. Net revenue per order = 60 × 0.20 − 60 × 0.03 = 12 − 1.8 = 10.2.
3. Variable cost per order = 2.
4. Contribution per order = 10.2 − 2 = 8.2.
5. Orders per lifetime = 12 × 0.75 = 9.
6. `max_revenue_per_customer` = 10.2 × 9 − 10 = 81.8.
7. `contribution_per_customer` = 8.2 × 9 − 10 = 63.8.
8. `cac` = 60.
9. Test: 63.8 > 0 and 60 ≤ 81.8, so `optimistic_case_fails: false`.

Realistic steps: orders per lifetime = 4 × 0.5 = 2; `max_revenue_per_customer` = 10.2 × 2 − 10 = 10.4; `contribution_per_customer` = 8.2 × 2 − 10 = 6.4; `cac` = 120. `realistic_case_fails: true`. If order value, take rate and CAC are findings and two cleaning marketplaces' post-mortems cite the same loss, KP15 meets its threshold; the optimistic case passes, so it is not `unfixable`, and a sourced density or repeat-order path could rebut it.

Gross-ticket trap: 24 orders × 60 = 1,440 against a CAC of 60 looks like 24 to 1. The contribution view gives about 1 to 1 in the optimistic case and a loss in the realistic one.

## 9. Worked example B: hardware device (made-up numbers)
All numbers below are invented for illustration and are not findings. Idea: a sensor device sold once through distributors, no subscription. Currency USD.

Inputs: retail price 600; distributor margin 30% of retail; bill of materials 350; certification 100,000 amortised over 2,000 units in the optimistic case; shipping and packaging 30; warranty reserve 5% of retail; one purchase per customer; CAC 40 through distributor co-marketing.

Optimistic steps:
1. Gross ticket = 600.
2. Net revenue per unit = 600 − 600 × 0.30 = 420.
3. Variable cost per unit = 350 + 100,000 / 2,000 + 30 + 600 × 0.05 = 350 + 50 + 30 + 30 = 460.
4. Contribution per unit = 420 − 460 = −40.
5. Units per lifetime = 1.
6. `max_revenue_per_customer` = 420.
7. `contribution_per_customer` = −40.
8. `cac` = 40.
9. Test: contribution −40 ≤ 0, so `optimistic_case_fails: true` (and the realistic case fails too).

KP15 meets its threshold, `unfixable`, only if the bill of materials, distributor margin and certification cost are findings read on the page (for example supplier quotes and a certification body's fee schedule), and no sourced path exists to a cheaper bill of materials, a direct channel, or a recurring revenue line. If the bill of materials were an assumption taken from the unfavourable end, the result would be a risk and the cheapest test would be a supplier quote.
