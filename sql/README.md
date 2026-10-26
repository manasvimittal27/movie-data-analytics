# SQL analysis (PostgreSQL)

The same questions as the notebook, answered in SQL on the cleaned tables. Every figure below matches the pandas results in `notebooks/movie_data_analysis.ipynb`.

## Run it

From the repository root, with PostgreSQL installed and `data/raw/mymoviedb.csv` in place:

```bash
python -m src.export_tables          # writes data/processed/movies.csv and movie_genres.csv
createdb -U postgres movies
psql -U postgres -d movies -f sql/00_setup.sql
psql -U postgres -d movies -f sql/02_genre_performance.sql    # or any other file
```

`00_setup.sql` creates the tables with primary keys, a foreign key and CHECK constraints (including "a rating exists only when there are votes"), loads both CSVs and creates the `rated_movies` view (movies with at least 50 votes).

## Schema

| Table | Grain | Key columns |
|---|---|---|
| `movies` | One row per movie (9,827) | `movie_id` PK, `title`, `release_date`, `popularity`, `vote_count`, `rating` (NULL when no votes), `original_language`, `n_genres` |
| `movie_genres` | One row per movie per genre (25,793) | (`movie_id`, `genre`) PK, `movie_id` FK → `movies` |
| `rated_movies` (view) | Movies with ≥ 50 votes (8,796) | Same columns as `movies` |

## Queries

| File | Question | SQL techniques |
|---|---|---|
| `01_data_checks.sql` | Did the load work, and do the two tables agree? | Anti-join, `HAVING`, `UNION ALL` check report, `FILTER` |
| `02_genre_performance.sql` | Which genres are common, and which rate better? | CTEs, `PERCENTILE_CONT`, `FILTER`, `RANK() OVER`, confidence intervals |
| `03_rating_reliability.sql` | How noisy are low-vote ratings? | `CASE` bucketing, `STDDEV_SAMP`, percentiles |
| `04_weighted_shortlist.sql` | Which movies belong on a discovery shortlist? | Parameter CTE, vote-weighted rating, `RANK()`, `STRING_AGG`, `COUNT(*) OVER ()` |
| `05_popularity_signals.sql` | Are popularity, votes and rating interchangeable? | Spearman correlation from window ranks with tie handling, `CORR`, `LAG` |
| `06_genre_mix_by_decade.sql` | How does the genre mix change by decade? | CTE chain, top-N, `LAG() OVER (PARTITION BY ...)` |
| `07_language_gap.sql` | Do non-English titles rate differently within a genre? | Conditional aggregation with `FILTER`, `HAVING` on filtered counts |

## Selected results

**Genre performance** (`02`, first and last rows)

| rating_rank | genre | pct_of_movies | rated_movies | mean_rating | ci_low | ci_high | pct_top_quartile | vs_catalogue_mean |
|---|---|---|---|---|---|---|---|---|
| 1 | Documentary | 2.2 | 121 | 7.36 | 7.21 | 7.51 | 65.3 | above average |
| 2 | History | 4.3 | 406 | 7.02 | 6.95 | 7.08 | 42.1 | above average |
| 6 | Drama | 38.1 | 3,401 | 6.83 | 6.80 | 6.85 | 36.9 | above average |
| 15 | Comedy | 30.8 | 2,784 | 6.47 | 6.44 | 6.50 | 20.3 | below average |
| 16 | Action | 27.3 | 2,471 | 6.43 | 6.40 | 6.47 | 20.0 | below average |
| 19 | Horror | 15.0 | 1,327 | 6.04 | 5.99 | 6.08 | 9.1 | below average |

**Rating reliability** (`03`)

| vote_bucket | movies | mean_rating | sd_rating |
|---|---|---|---|
| 1-9 votes | 260 | 5.46 | 1.65 |
| 10-49 votes | 671 | 6.21 | 1.04 |
| 50-199 votes | 2,079 | 6.37 | 0.96 |
| 200-999 votes | 3,559 | 6.46 | 0.83 |
| 1,000+ votes | 3,158 | 6.79 | 0.77 |

**Spearman correlations** (`05a`): popularity vs rating 0.13, popularity vs votes 0.40, votes vs rating 0.22 (8,796 movies).

**Median popularity by release year** (`05b`): 20.5–24.2 for every year from 2010 to 2020, then 50.7 for 2021 (+26.6 on the year before).

**Hidden gems** (`04c`): 234 movies in the top 10% by weighted rating and the bottom half by popularity, led by *The Silence of the Lambs*, *Cinema Paradiso* and *Lock, Stock and Two Smoking Barrels*.

## Notes

- **Confidence intervals** use 1.96 (normal approximation) because PostgreSQL has no built-in t-distribution. With at least 121 movies per genre, this differs from the notebook's t-based interval by less than 0.005 rating points.
- **Spearman correlation** is computed as the Pearson correlation of ranks, with tied values given their average rank (`RANK() + (ties − 1) / 2`), the same convention as pandas and SciPy.
- **Medians and percentiles** use `PERCENTILE_CONT`, which interpolates like pandas' default `quantile()`.
