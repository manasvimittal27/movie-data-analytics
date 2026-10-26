-- ============================================================================
-- 07. English vs non-English ratings within each genre (notebook Q5)
-- Comparing inside a genre removes the part of the gap caused by genre mix.
-- Caveat: likely selection bias. A non-English film probably only reaches an
-- English-leaning "popular" list if it is unusually acclaimed.
--
-- Techniques: conditional aggregation with FILTER, HAVING on filtered counts
-- ============================================================================

SELECT
    g.genre,
    COUNT(*) FILTER (WHERE r.original_language = 'en')                 AS english_movies,
    COUNT(*) FILTER (WHERE r.original_language <> 'en')                AS non_english_movies,
    ROUND(AVG(r.rating) FILTER (WHERE r.original_language = 'en'), 2)  AS english_mean,
    ROUND(AVG(r.rating) FILTER (WHERE r.original_language <> 'en'), 2) AS non_english_mean,
    ROUND(AVG(r.rating) FILTER (WHERE r.original_language <> 'en')
        - AVG(r.rating) FILTER (WHERE r.original_language = 'en'), 2)  AS gap
FROM movie_genres g
JOIN rated_movies r USING (movie_id)
GROUP BY g.genre
HAVING COUNT(*) FILTER (WHERE r.original_language = 'en')  >= 30
   AND COUNT(*) FILTER (WHERE r.original_language <> 'en') >= 30
ORDER BY gap DESC;
