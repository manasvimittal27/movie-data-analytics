"""Export the cleaned tables to CSV so they can be loaded into PostgreSQL.

Run from the repository root:

    python -m src.export_tables

Writes ``data/processed/movies.csv`` (one row per movie) and
``data/processed/movie_genres.csv`` (one row per movie per genre), using the
same cleaning rules as the notebook. ``sql/00_setup.sql`` then loads them.
"""
from __future__ import annotations

from src import data_analysis as da

PROCESSED_DIR = da.REPO_ROOT / "data" / "processed"

MOVIE_COLUMNS = [
    "movie_id", "title", "release_date", "popularity", "vote_count",
    "rating", "original_language", "n_genres",
]


def main() -> None:
    raw = da.load_raw()
    movies, _ = da.clean_movies(raw)
    movie_genres = da.explode_genres(movies)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    movies_out = movies[MOVIE_COLUMNS].assign(release_date=movies["release_date"].dt.date)
    movies_out.to_csv(PROCESSED_DIR / "movies.csv", index=False)  # missing ratings become empty -> NULL
    movie_genres[["movie_id", "genre"]].to_csv(PROCESSED_DIR / "movie_genres.csv", index=False)

    print(f"movies.csv:       {len(movies_out):,} rows")
    print(f"movie_genres.csv: {len(movie_genres):,} rows")
    print(f"Written to {PROCESSED_DIR}")


if __name__ == "__main__":
    main()
