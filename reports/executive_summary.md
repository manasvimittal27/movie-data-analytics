# Executive Summary: Movie Catalogue Analytics

*Simulated case study using the public TMDB "9000+ Movies" dataset (9,827 movies popular on TMDB around March 2022). No viewing, revenue or subscriber data is available, so no finding is about commercial performance.*

## The question

How can a streaming or entertainment company use catalogue data to understand audience preferences, identify promising content categories and make better content-discovery decisions?

## What we found

| # | Finding | Evidence |
|---|---|---|
| 1 | **The genres that dominate the catalogue are not the best rated.** | Drama 38%, Comedy 31%, Action 27%, Thriller 25% of movies. Comedy (6.47), Action (6.43) and Thriller (6.33) rate below the 6.56 average; Horror is lowest (6.04). Documentary (7.36), History (7.02), Music (7.01), War (6.99) and Animation (6.97) rate highest, all with 95% confidence intervals above average. |
| 2 | **Popularity measures current attention, not quality.** | Spearman correlation with rating: 0.13. Median popularity is 20–24 for 2010–2020 releases and about 51 for 2021 releases. |
| 3 | **Raw ratings from few votes are unreliable.** | Rating SD is 1.65 below 10 votes vs 0.77 above 1,000 votes. 7 of the 10 highest raw ratings have fewer than 350 votes. |
| 4 | **Non-English titles rate higher within every genre compared.** | +0.14 (History) to +0.62 (Action) points across 15 genres; non-English titles are 20% of rated movies. Likely partly selection bias. |
| 5 | **There is a pool of well-rated, low-attention titles.** | 234 movies in the top 10% by vote-weighted rating and the bottom half by popularity; 54% pre-2000, 32% non-English. |

## Recommendations

| # | Action | Why | Risk / trade-off | KPI (needs data not in this set) |
|---|---|---|---|---|
| 1 | Rank "highly rated" surfaces by **vote-weighted rating**; keep popularity for "trending now" | Each surface then reflects what its label promises | New releases need time to accumulate votes | Click-through and completion rate per surface |
| 2 | Use Documentary, History, Music, War and Animation as **curation themes**, not volume targets | Well received but each is 15% of the catalogue or less | Ratings may come mainly from enthusiasts | Completion and rating of curated titles vs average |
| 3 | Pilot a **"hidden gems" row** as an A/B test | Under-exposed, well-liked titles at no content cost | Low attention may mean low demand | Starts and completions vs control row |
| 4 | Pilot an **international picks** collection (Action, Horror, Science Fiction first) | Largest within-genre rating gaps | Selection bias; subtitles and dubbing affect uptake | Share of users starting a non-English title |
| 5 | Report **catalogue mix and audience reception separately** | Mix and reception are unrelated in this data | One more metric in reviews | Adoption in planning dashboards |

## Evidence levels

- **Observed** (calculated from the data): findings 1–5.
- **Hypotheses** (plausible, not testable here): self-selected raters inflate niche-genre ratings; international titles are a selected, acclaimed subset; low popularity reflects low exposure rather than low demand.
- **Needs validation** (requires new data): any effect on viewing, retention or revenue.

## Main limitations

Single snapshot of the most popular TMDB titles (not a random sample); self-selected raters; survivorship bias for older films; overlapping genre groups; judgement-call thresholds (50 votes, prior of 555 votes, hidden-gem cut-offs).
