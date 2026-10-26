-- ============================================================================
-- 04. Vote-weighted rating, discovery shortlist and hidden gems (notebook Q5)
--
-- weighted = v/(v+m) * R + m/(v+m) * C
--   R = movie rating, v = its votes,
--   C = mean rating of rated movies, m = median vote count of rated movies.
--
-- Techniques: parameter CTE, RANK() OVER, PERCENTILE_CONT cut-offs,
--             STRING_AGG to bring genres back onto one row per movie
-- ============================================================================

-- 4a. How the weighting reorders the highest raw ratings -----------------------
WITH params AS (
    SELECT
        AVG(rating)                                                  AS c,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY vote_count)      AS m
    FROM rated_movies
),
scored AS (
    SELECT
        r.*,
        r.vote_count / (r.vote_count + p.m) * r.rating
            + p.m / (r.vote_count + p.m) * p.c                       AS weighted_rating
    FROM rated_movies r
    CROSS JOIN params p
),
ranked AS (
    SELECT
        *,
        RANK() OVER (ORDER BY rating DESC)          AS raw_rank,
        RANK() OVER (ORDER BY weighted_rating DESC) AS weighted_rank
    FROM scored
)
SELECT title, vote_count, rating, raw_rank, weighted_rank,
       ROUND(weighted_rating::numeric, 2) AS weighted_rating
FROM ranked
WHERE raw_rank <= 10
ORDER BY raw_rank, weighted_rank;


-- 4b. Top 15 by weighted rating ----------------------------------------------
WITH params AS (
    SELECT AVG(rating) AS c,
           PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY vote_count) AS m
    FROM rated_movies
),
scored AS (
    SELECT r.*,
           r.vote_count / (r.vote_count + p.m) * r.rating
               + p.m / (r.vote_count + p.m) * p.c AS weighted_rating
    FROM rated_movies r
    CROSS JOIN params p
)
SELECT
    RANK() OVER (ORDER BY s.weighted_rating DESC)        AS weighted_rank,
    s.title,
    EXTRACT(YEAR FROM s.release_date)::int               AS release_year,
    s.original_language,
    s.vote_count,
    s.rating,
    ROUND(s.weighted_rating::numeric, 2)                 AS weighted_rating
FROM scored s
ORDER BY s.weighted_rating DESC
LIMIT 15;


-- 4c. Hidden gems: top 10% by weighted rating, bottom half by popularity -----
WITH params AS (
    SELECT AVG(rating) AS c,
           PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY vote_count) AS m
    FROM rated_movies
),
scored AS (
    SELECT r.*,
           r.vote_count / (r.vote_count + p.m) * r.rating
               + p.m / (r.vote_count + p.m) * p.c AS weighted_rating
    FROM rated_movies r
    CROSS JOIN params p
),
cutoffs AS (
    SELECT
        PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY weighted_rating) AS weighted_p90,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY popularity)      AS popularity_median
    FROM scored
),
gems AS (
    SELECT s.*
    FROM scored s
    CROSS JOIN cutoffs c
    WHERE s.weighted_rating >= c.weighted_p90
      AND s.popularity <= c.popularity_median
)
SELECT
    g.title,
    EXTRACT(YEAR FROM g.release_date)::int                  AS release_year,
    g.original_language,
    STRING_AGG(mg.genre, ', ' ORDER BY mg.genre)            AS genres,
    g.vote_count,
    g.rating,
    ROUND(g.weighted_rating::numeric, 2)                    AS weighted_rating,
    g.popularity,
    COUNT(*) OVER ()                                        AS total_hidden_gems
FROM gems g
JOIN movie_genres mg USING (movie_id)
GROUP BY g.movie_id, g.title, g.release_date, g.original_language,
         g.vote_count, g.rating, g.weighted_rating, g.popularity
ORDER BY g.weighted_rating DESC
LIMIT 12;
