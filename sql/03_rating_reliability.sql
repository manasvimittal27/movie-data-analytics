-- ============================================================================
-- 03. Rating reliability by vote count (justifies the 50-vote threshold)
-- How much do ratings swing when they rest on only a few votes?
--
-- Techniques: CASE bucketing, STDDEV_SAMP, PERCENTILE_CONT, ordering by a
--             bucket's lower bound rather than its label
-- ============================================================================

WITH bucketed AS (
    SELECT
        rating,
        CASE
            WHEN vote_count < 10   THEN 1
            WHEN vote_count < 50   THEN 10
            WHEN vote_count < 200  THEN 50
            WHEN vote_count < 1000 THEN 200
            ELSE 1000
        END AS bucket_floor
    FROM movies
    WHERE vote_count > 0
)
SELECT
    CASE bucket_floor
        WHEN 1    THEN '1-9 votes'
        WHEN 10   THEN '10-49 votes'
        WHEN 50   THEN '50-199 votes'
        WHEN 200  THEN '200-999 votes'
        ELSE           '1,000+ votes'
    END                                                                  AS vote_bucket,
    COUNT(*)                                                             AS movies,
    ROUND(AVG(rating), 2)                                                AS mean_rating,
    ROUND(STDDEV_SAMP(rating), 2)                                        AS sd_rating,
    ROUND(PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY rating)::numeric, 1) AS p05_rating,
    ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY rating)::numeric, 1) AS p95_rating
FROM bucketed
GROUP BY bucket_floor
ORDER BY bucket_floor;
