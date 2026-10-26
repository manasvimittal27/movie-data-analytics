-- ============================================================================
-- Create and load the movie tables in PostgreSQL.
--
-- Run from the repository root, after `python -m src.export_tables`:
--     createdb movies
--     psql -d movies -f sql/00_setup.sql
--
-- Two tables, the same grains as the notebook:
--   movies        one row per movie       -> use for anything that counts movies
--   movie_genres  one row per movie+genre -> use only for per-genre questions
-- ============================================================================

\set ON_ERROR_STOP on

DROP VIEW IF EXISTS rated_movies;
DROP TABLE IF EXISTS movie_genres, movies;

CREATE TABLE movies (
    movie_id           INTEGER       PRIMARY KEY,
    title              TEXT          NOT NULL,
    release_date       DATE          NOT NULL,
    popularity         NUMERIC(10,3) NOT NULL CHECK (popularity > 0),
    vote_count         INTEGER       NOT NULL CHECK (vote_count >= 0),
    rating             NUMERIC(3,1)  CHECK (rating BETWEEN 0 AND 10),  -- NULL when vote_count = 0
    original_language  TEXT          NOT NULL,
    n_genres           SMALLINT      NOT NULL CHECK (n_genres >= 1),
    CONSTRAINT rating_needs_votes CHECK ((vote_count = 0) = (rating IS NULL))
);

CREATE TABLE movie_genres (
    movie_id  INTEGER NOT NULL REFERENCES movies (movie_id),
    genre     TEXT    NOT NULL,
    PRIMARY KEY (movie_id, genre)
);

\copy movies FROM 'data/processed/movies.csv' WITH (FORMAT csv, HEADER true)
\copy movie_genres FROM 'data/processed/movie_genres.csv' WITH (FORMAT csv, HEADER true)

CREATE INDEX movie_genres_genre_idx ON movie_genres (genre);

-- Ratings based on fewer than 50 votes are too noisy to compare
-- (see sql/03_rating_reliability.sql). Every rating analysis uses this view.
CREATE VIEW rated_movies AS
SELECT *
FROM movies
WHERE vote_count >= 50;

ANALYZE movies;
ANALYZE movie_genres;

SELECT
    (SELECT COUNT(*) FROM movies)       AS movies,
    (SELECT COUNT(*) FROM movie_genres) AS movie_genre_rows,
    (SELECT COUNT(*) FROM rated_movies) AS rated_movies;
