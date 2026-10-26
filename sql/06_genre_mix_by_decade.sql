-- ============================================================================
-- 06. Genre mix by release decade (notebook Q4)
-- Share of each decade's movies tagged with each of the six most common
-- genres, and the change from the previous decade.
--
-- The denominator is movies released in the decade (not genre tags), so shares
-- are comparable across decades. The 2020s are incomplete (mostly 2020 to
-- early 2022). These are movies popular on TMDB in 2022, not all films made.
--
-- Techniques: CTE chain, top-N with LIMIT, window LAG partitioned by genre
-- ============================================================================

WITH decades AS (
    SELECT movie_id, (EXTRACT(YEAR FROM release_date)::int / 10) * 10 AS decade
    FROM movies
),
decade_totals AS (
    SELECT decade, COUNT(*) AS movies_in_decade
    FROM decades
    GROUP BY decade
),
top_genres AS (
    SELECT genre
    FROM movie_genres
    GROUP BY genre
    ORDER BY COUNT(*) DESC
    LIMIT 6
),
shares AS (
    SELECT
        d.decade,
        g.genre,
        COUNT(*)                                       AS movies_tagged,
        100.0 * COUNT(*) / t.movies_in_decade          AS pct_of_decade,
        t.movies_in_decade
    FROM decades d
    JOIN movie_genres g USING (movie_id)
    JOIN top_genres USING (genre)
    JOIN decade_totals t USING (decade)
    WHERE d.decade >= 1970
    GROUP BY d.decade, g.genre, t.movies_in_decade
)
SELECT
    genre,
    decade,
    movies_in_decade,
    ROUND(pct_of_decade, 1)                                                    AS pct_of_decade,
    ROUND(pct_of_decade - LAG(pct_of_decade) OVER (PARTITION BY genre ORDER BY decade), 1)
                                                                               AS change_pts,
    decade = 2020                                                              AS incomplete_decade
FROM shares
ORDER BY genre, decade;
