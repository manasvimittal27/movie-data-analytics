"""Unit tests for the cleaning and metric functions, using a small hand-made dataset."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import data_analysis as da  # noqa: E402


@pytest.fixture
def raw():
    return pd.DataFrame({
        "Release_Date": ["2020-01-01", "1994-05-01", "2019-03-01", "2022-06-01", "1992-11-25"],
        "Title": ["A", "B", "Aladdin", "D", "Aladdin"],
        "Overview": ["a", "b", "remake", "d", "original"],
        "Popularity": [100.0, 20.0, 30.0, 50.0, 15.0],
        "Vote_Count": [1000, 60, 500, 0, 9000],
        "Vote_Average": [7.0, 8.0, 6.5, 0.0, 7.6],
        "Original_Language": ["en", "ja", "en", "en", "en"],
        "Genre": ["Action, Drama", "Animation", "Family,  Fantasy ", "Horror", "Animation, Family"],
        "Poster_Url": ["u"] * 5,
    })


def test_split_genres_trims_whitespace_and_empty_parts():
    result = da.split_genres(pd.Series(["Action,  Drama ", "Comedy,,", None]))
    assert result.tolist() == [["Action", "Drama"], ["Comedy"], []]


def test_clean_keeps_same_title_different_dates(raw):
    movies, _ = da.clean_movies(raw, min_votes=50)
    assert len(movies) == 5
    assert (movies["title"] == "Aladdin").sum() == 2


def test_clean_drops_true_duplicates(raw):
    doubled = pd.concat([raw, raw.iloc[[0]]], ignore_index=True)
    movies, log = da.clean_movies(doubled, min_votes=50)
    assert len(movies) == 5
    assert "1 removed" in log["note"].tolist()


def test_zero_vote_rating_is_missing_not_zero(raw):
    movies, _ = da.clean_movies(raw, min_votes=50)
    unrated = movies[movies["title"] == "D"].iloc[0]
    assert np.isnan(unrated["rating"])
    assert not unrated["rating_qualified"]


def test_explode_counts_each_movie_once_per_genre(raw):
    movies, _ = da.clean_movies(raw, min_votes=50)
    movie_genres = da.explode_genres(movies)
    assert len(movie_genres) == 8  # 2 + 1 + 2 + 1 + 2 genre tags
    prevalence = da.genre_prevalence(movies, movie_genres)
    assert prevalence.loc["Animation", "movies"] == 2
    assert prevalence.loc["Family", "pct_of_movies"] == pytest.approx(40.0)


def test_weighted_rating_shrinks_low_vote_movies_more():
    ratings = pd.Series([9.0, 9.0])
    votes = pd.Series([10, 10_000])
    weighted = da.weighted_rating(ratings, votes, prior_votes=500, prior_mean=6.0)
    assert weighted[0] < weighted[1] < 9.0
    assert weighted[0] == pytest.approx(10 / 510 * 9 + 500 / 510 * 6)


def test_mean_ci_contains_mean_and_narrows_with_n():
    rng = np.random.default_rng(0)
    small = pd.Series(rng.normal(6.5, 1, 20))
    large = pd.Series(rng.normal(6.5, 1, 2000))
    m_small, lo_small, hi_small = da.mean_ci(small)
    m_large, lo_large, hi_large = da.mean_ci(large)
    assert lo_small < m_small < hi_small
    assert (hi_large - lo_large) < (hi_small - lo_small)


def test_snapshot_is_latest_release_with_votes(raw):
    assert da.infer_snapshot_date(raw) == pd.Timestamp("2020-01-01")
