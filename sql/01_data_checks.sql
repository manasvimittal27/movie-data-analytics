-- ============================================================================
-- 01. Data checks
-- Confirms the load is complete and the two tables agree with each other.
-- Every check should return 0 problems.
-- Techniques: anti-joins, aggregate comparisons, UNION ALL report
-- ============================================================================

WITH genre_tags AS (
    SELECT movie_id, COUNT(*) AS tags
    FROM movie_genres
    GROUP BY movie_id
)
SELECT 'Movies with no genre rows' AS check_name,
       COUNT(*) AS problems
FROM movies m
LEFT JOIN genre_tags g USING (movie_id)
WHERE g.movie_id IS NULL

UNION ALL
SELECT 'Movies whose n_genres differs from their genre rows',
       COUNT(*)
FROM movies m
JOIN genre_tags g USING (movie_id)
WHERE g.tags <> m.n_genres

UNION ALL
SELECT 'Genres with leading or trailing spaces',
       COUNT(*)
FROM movie_genres
WHERE genre <> BTRIM(genre)

UNION ALL
SELECT 'Duplicate title + release date',
       COUNT(*)
FROM (
    SELECT title, release_date
    FROM movies
    GROUP BY title, release_date
    HAVING COUNT(*) > 1
) duplicates

UNION ALL
SELECT 'Zero-vote movies with a non-NULL rating',
       COUNT(*)
FROM movies
WHERE vote_count = 0 AND rating IS NOT NULL;


-- Context, not problems: how many movies sit outside the rating analysis, and why.
SELECT
    COUNT(*) FILTER (WHERE vote_count = 0)              AS no_votes_rating_null,
    COUNT(*) FILTER (WHERE vote_count BETWEEN 1 AND 49) AS under_50_votes,
    COUNT(*) FILTER (WHERE vote_count >= 50)            AS rated_movies,
    COUNT(*)                                            AS all_movies
FROM movies;
