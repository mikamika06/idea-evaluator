# Facets and routing

Facets from the card decide where each question searches.

| Facet value | Channels switched on |
|---|---|
| customer = consumer | Q1/Q2: Reddit via Arctic Shift, app-store reviews, consumer forums, social groups in the users' language. Q3: app stores of every jurisdiction, Product Hunt, review sites |
| customer = business | Q1/Q2: trade forums, G2 / Capterra reviews, job postings. Q3: G2 / Capterra, integration marketplaces of the tools the customer uses (e.g. Xero App Store, Shopify App Store, Salesforce AppExchange), industry associations, trade-show exhibitor lists, LinkedIn company pages via search. Q4: procurement roles in job postings |
| customer = government | Q3/Q4: public procurement portals and award records of the jurisdiction, regulator lists, municipal budgets |
| customer = solo_professional | Q1/Q2: professional forums and subreddits, professional body publications, tool reviews |
| payer_same_as_user = false | Q1 and dossier for the user and separately for the payer; Q4 searches the payer's own sources |
| buying_driver = regulation | Law check first; regulator pages, effective dates, fines; Q7 what-changed |
| product_type = hardware | Q3: patents, crowdfunding archives, distributor catalogues. Q6: bill of materials and certification costs |
| product_type = marketplace | Q6: take rate, supply acquisition and retention on both sides; Q3: disintermediation in dead attempts |
| market_visibility = low | registries and procurement of the jurisdiction are mandatory in Q3; invisible_player_risk at least medium |
| any | web search in every language of the language plan; Hacker News Algolia; local company directory `company-dir` (YC directory and failure lists, masked to AS_OF); Y Combinator directory; failure collections (Failory, CB Insights post-mortems, startups.rip) |

Every language in the language plan must appear in some `search_matrix` with at least one channel. A missing language is an unmet requirement and is listed in `unknowns`.

Integration marketplaces are the fastest way to find invisible B2B players: a product that plugs into the customer's core system is usually listed there.
