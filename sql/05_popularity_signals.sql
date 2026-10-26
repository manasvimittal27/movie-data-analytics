-- ============================================================================
-- 05. Are popularity, vote count and rating interchangeable? (notebook Q3)
--
-- 5a computes Spearman rank correlation in SQL: Pearson correlation (CORR)
-- of the ranks. Tied values get their average rank, as in pandas/SciPy:
-- average rank = RANK() + (number of ties - 1) / 2.
-- 5b shows that popularity is mainly a recency signal.
--
-- Techniques: window functions (RANK, COUNT OVER PARTITION, LAG), CORR
-- ============================================================================

-- 5a. Spearman correlations ---------------------------------------------------
WITH ranked AS (
    SELECT
        RANK() OVER (ORDER BY popularity)
            + (COUNT(*) OVER (PARTITION BY popularity) - 1) / 2.0 AS popularity_rank,
        RANK() OVER (ORDER BY vote_count)
            + (COUNT(*) OVER (PARTITION BY vote_count) - 1) / 2.0 AS votes_rank,
        RANK() OVER (ORDER BY rating)
            + (COUNT(*) OVER (PARTITION BY rating) - 1) / 2.0     AS rating_rank
    FROM rated_movies
)
SELECT
    ROUND(CORR(popularity_rank, rating_rank)::numeric, 2) AS spearman_popularity_rating,
    ROUND(CORR(popularity_rank, votes_rank)::numeric, 2)  AS spearman_popularity_votes,
    ROUND(CORR(votes_rank, rating_rank)::numeric, 2)      AS spearman_votes_rating,
    COUNT(*)                                              AS movies
FROM ranked;


-- 5b. Median popularity by release year, with year-on-year change -------------
WITH by_year AS (
    SELECT
        EXTRACT(YEAR FROM release_date)::int                          AS release_year,
        COUNT(*)                                                      AS movies,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY popularity)       AS median_popularity
    FROM movies
    WHERE release_date < DATE '2023-01-01'   -- 2023-24 hold only 9 announced titles
    GROUP BY 1
)
SELECT
    release_year,
    movies,
    ROUND(median_popularity::numeric, 1)                                       AS median_popularity,
    ROUND((median_popularity - LAG(median_popularity) OVER w)::numeric, 1)     AS change_vs_prior_year
FROM by_year
WHERE release_year >= 2010
WINDOW w AS (ORDER BY release_year)
ORDER BY release_year;
