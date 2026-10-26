-- ============================================================================
-- 02. Genre prevalence and rating performance (notebook Q1 and Q2)
-- Which genres make up the catalogue, and which rate consistently better?
--
-- Techniques: CTEs, PERCENTILE_CONT, conditional aggregation with FILTER,
--             window functions (RANK, aggregate OVER ())
--
-- The 95% interval uses the normal value 1.96. The notebook uses the
-- t-distribution; with at least 121 movies per genre the two differ by less
-- than 0.005 rating points.
-- ============================================================================

WITH catalogue AS (
    SELECT COUNT(*) AS total_movies FROM movies
),
benchmarks AS (
    SELECT
        AVG(rating)                                          AS catalogue_mean,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY rating) AS top_quartile_cutoff
    FROM rated_movies
),
prevalence AS (
    SELECT genre, COUNT(*) AS movies_tagged          -- one row per movie per genre,
    FROM movie_genres                                -- so COUNT(*) counts movies
    GROUP BY genre
),
genre_ratings AS (
    SELECT
        g.genre,
        COUNT(*)                                                         AS rated_movies,
        AVG(r.rating)                                                    AS mean_rating,
        STDDEV_SAMP(r.rating) / SQRT(COUNT(*)::numeric)                  AS std_error,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY r.rating)            AS median_rating,
        COUNT(*) FILTER (WHERE r.rating >= b.top_quartile_cutoff)::numeric
            / COUNT(*)                                                   AS share_top_quartile
    FROM movie_genres g
    JOIN rated_movies r USING (movie_id)
    CROSS JOIN benchmarks b
    GROUP BY g.genre
)
SELECT
    RANK() OVER (ORDER BY gr.mean_rating DESC)                      AS rating_rank,
    gr.genre,
    p.movies_tagged,
    ROUND(100.0 * p.movies_tagged / c.total_movies, 1)              AS pct_of_movies,
    RANK() OVER (ORDER BY p.movies_tagged DESC)                     AS prevalence_rank,
    gr.rated_movies,
    ROUND(gr.mean_rating, 2)                                        AS mean_rating,
    ROUND(gr.mean_rating - 1.96 * gr.std_error, 2)                  AS ci_low,
    ROUND(gr.mean_rating + 1.96 * gr.std_error, 2)                  AS ci_high,
    ROUND(gr.median_rating::numeric, 1)                             AS median_rating,
    ROUND(100 * gr.share_top_quartile, 1)                           AS pct_top_quartile,
    CASE
        WHEN gr.mean_rating - 1.96 * gr.std_error > b.catalogue_mean THEN 'above average'
        WHEN gr.mean_rating + 1.96 * gr.std_error < b.catalogue_mean THEN 'below average'
        ELSE 'not distinguishable'
    END                                                             AS vs_catalogue_mean
FROM genre_ratings gr
JOIN prevalence p USING (genre)
CROSS JOIN catalogue c
CROSS JOIN benchmarks b
ORDER BY rating_rank;
