# Project Audit: From Tutorial Notebook to Case Study

Two earlier versions were reviewed: `moviedataanalysis.ipynb` (original, executed) and `moviedataanalysis_v2.ipynb` (first revision, never executed). **v2 was the better starting point**: it had already fixed the silent row loss and the double counting from the genre split. Its structure was kept and extended. The original's exploration summary and question-led layout were also kept.

| # | Issue in earlier versions | Why it matters to a recruiter | Improvement made |
|---|---|---|---|
| 1 | Original: `pd.cut` without `include_lowest=True` turned all 100 zero-rated movies into NaN, then `dropna()` removed them without comment | Silent data loss is the first thing reviewers check | No rows dropped. Zero-vote movies kept with rating set to missing; every step logs its row count |
| 2 | Original: after `explode`, movie-level answers (rating categories, release years) counted movie-genre rows | Inflated counts are a classic analyst error | Separate `movies` and `movie_genres` tables; assertions guarantee each movie is counted once |
| 3 | Original Q2 ("which genres have the highest votes") charted rating buckets with no genre at all | Answer did not match its question | Genre ratings with 95% CIs, medians and top-quartile shares |
| 4 | Conclusion numbers (e.g., "18.5%") had no supporting cell; two lowest-popularity movies were merged into one name | Unverifiable claims undermine trust | Every number in the text was recomputed independently from the raw file |
| 5 | Rating labels `popular / not_popular` were easily confused with the `Popularity` column | Ambiguous metrics confuse stakeholders | Explicit definitions: rating, vote count and popularity treated as three different signals (Q3) |
| 6 | v2 removed "duplicates" by title + date without checking whether any existed | Untested assumptions | Audit shows 0 title + date duplicates; the 314 repeated titles are remakes, so nothing is removed and the key's limits are documented |
| 7 | No treatment of low-vote ratings; a 10.0 from 1 vote counted like a 8.7 from 20,000 | Rankings driven by noise | Rating-noise analysis justifies a 50-vote threshold; vote-weighted rating with a sensitivity test for rankings |
| 8 | Popularity analysed with raw means and histograms despite skewness of 21.9 | Misleading statistics | Log scales, medians and Spearman correlations; extreme values kept but not allowed to dominate |
| 9 | Decade analysis ignored the incomplete 2020s and read the data as film history | Wrong conclusions about the industry | 2020s flagged on the chart; findings framed as "what is popular today", not production history |
| 10 | `Original_Language` dropped without consideration | Lost a genuinely useful business angle | Kept and used: within-genre English vs non-English comparison, with selection-bias caveat |
| 11 | Charts without interpretation; default styling; generic titles | Charts that do not support decisions | 9 charts, each with an insight title and a "what it shows / why it matters / caveat" note |
| 12 | Leftover debugging cells, repeated `df.head()`, order-dependent cells (the double-split NaN bug) | Notebook not reproducible | Logic moved to `src/`, 8 unit tests, validation cell; notebook runs cleanly top to bottom (tested on pandas 2.2 and 3.0) |
| 13 | No business framing, recommendations or limitations | Reads as a tutorial exercise | Business questions with decisions, metrics and methods; recommendations with risks and KPIs; explicit evidence levels |
| 14 | The dataset is a widely used Kaggle tutorial dataset | Recruiters have seen many basic versions | Differentiated by rating-reliability analysis, CIs, weighted ranking, hidden gems and the language-gap analysis |

**Retained:** the question-led structure, the genre split and the exploration summary. The most popular movie (Spider-Man: No Way Home) now appears in the outlier discussion.
**Dropped:** "least popular movie", because the file stops at a popularity floor of 13.35, so the answer is just whichever titles sit on the cut-off and informs no decision.
**Removed:** rating categories as the main rating measure (quartile buckets are equal-sized by construction, so their counts carry no information); redundant `head()` calls.
**Not added, deliberately:** machine learning. No question here needs a predictive model, and a model trained on this data could not be evaluated against a real business outcome.
