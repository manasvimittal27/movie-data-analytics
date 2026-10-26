"""Reusable cleaning and analysis functions for the TMDB movie catalogue case study.

The notebook in ``notebooks/`` calls these functions so that every cleaning rule
and metric is defined once, documented, and covered by the tests in ``tests/``.

Two tables come out of the cleaning step:

* ``movies``: one row per movie. Use it for anything that counts movies.
* ``movie_genres``: one row per movie per genre. Use it only for per-genre
  questions, because a movie with three genres appears three times.
"""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_PATH = REPO_ROOT / "data" / "raw" / "mymoviedb.csv"

# Ratings based on fewer votes than this are too noisy to compare (see the
# "rating noise" check in the notebook). The threshold is a judgement call and
# is reported wherever it is used.
MIN_VOTES = 50

RAW_COLUMNS = {
    "Release_Date": "release_date",
    "Title": "title",
    "Overview": "overview",
    "Popularity": "popularity",
    "Vote_Count": "vote_count",
    "Vote_Average": "vote_average",
    "Original_Language": "original_language",
    "Genre": "genre",
    "Poster_Url": "poster_url",
}


def resolve_data_path(path: str | os.PathLike | None = None) -> Path:
    """Return the dataset location.

    Order of precedence: an explicit ``path`` argument, then the
    ``MOVIE_DATA_PATH`` environment variable, then ``data/raw/mymoviedb.csv``
    inside the repository.
    """
    candidate = Path(path or os.environ.get("MOVIE_DATA_PATH") or DEFAULT_DATA_PATH)
    if not candidate.exists():
        raise FileNotFoundError(
            f"Dataset not found at {candidate}. Download mymoviedb.csv from "
            "https://www.kaggle.com/datasets/disham993/9000-movies-dataset and "
            "save it to data/raw/, or set MOVIE_DATA_PATH to its location."
        )
    return candidate


def load_raw(path: str | os.PathLike | None = None) -> pd.DataFrame:
    """Load the raw CSV exactly as published.

    ``lineterminator='\\n'`` is needed because some overviews contain carriage
    returns that would otherwise split a record across two rows.
    """
    raw = pd.read_csv(resolve_data_path(path), lineterminator="\n")
    missing = set(RAW_COLUMNS) - set(raw.columns)
    if missing:
        raise ValueError(f"Unexpected file layout, missing columns: {sorted(missing)}")
    return raw


# --------------------------------------------------------------------------- #
# Data quality
# --------------------------------------------------------------------------- #
def split_genres(genre_strings: pd.Series) -> pd.Series:
    """Split comma-separated genre strings into lists of trimmed, non-empty names."""
    return genre_strings.fillna("").astype(str).str.split(",").apply(
        lambda parts: [p.strip() for p in parts if p.strip()]
    )


def quality_audit(raw: pd.DataFrame) -> pd.DataFrame:
    """Run the data-quality checks and return one row per check with its count."""
    dates = pd.to_datetime(raw["Release_Date"], errors="coerce")
    genre_lists = split_genres(raw["Genre"])
    snapshot = infer_snapshot_date(raw)

    checks = [
        ("Rows", len(raw), "Records in the raw file"),
        ("Missing values (any column)", int(raw.isna().any(axis=1).sum()), "Rows with at least one missing field"),
        ("Fully duplicated rows", int(raw.duplicated().sum()), "Identical in every column"),
        ("Unparseable release dates", int(dates.isna().sum()), "Dates that fail to parse"),
        ("Release date after inferred snapshot", int((dates > snapshot).sum()),
         f"Released after {snapshot:%Y-%m-%d}, the latest release date that has any votes"),
        ("Vote count = 0", int((raw["Vote_Count"] == 0).sum()), "No votes, so the 0.0 rating is a placeholder"),
        ("Vote count < 0", int((raw["Vote_Count"] < 0).sum()), "Impossible value"),
        ("Vote average outside 0–10", int((~raw["Vote_Average"].between(0, 10)).sum()), "Impossible value"),
        ("Vote average = 0 with votes > 0", int(((raw["Vote_Average"] == 0) & (raw["Vote_Count"] > 0)).sum()),
         "Would indicate a real zero rating"),
        (f"Vote count 1–{MIN_VOTES - 1}", int(raw["Vote_Count"].between(1, MIN_VOTES - 1).sum()),
         "Rated, but on too few votes to compare reliably"),
        ("Popularity <= 0", int((raw["Popularity"] <= 0).sum()), "Impossible value"),
        ("Empty genre", int((genre_lists.str.len() == 0).sum()), "No usable genre"),
        ("Rows repeating an earlier title", int(raw["Title"].duplicated().sum()), "Title alone, any date"),
        ("Rows repeating title + release date", int(raw.duplicated(["Title", "Release_Date"]).sum()),
         "Likely duplicate entries of the same film"),
        ("Rows repeating title + overview", int(raw.duplicated(["Title", "Overview"]).sum()),
         "Same title and plot text"),
    ]
    return pd.DataFrame(checks, columns=["check", "rows", "meaning"])


def infer_snapshot_date(raw: pd.DataFrame) -> pd.Timestamp:
    """Approximate when the data was collected.

    The file has no collection date. The latest release date that already has
    votes is a reasonable lower bound: films released after it had not been
    rated yet when the data was pulled.
    """
    dates = pd.to_datetime(raw["Release_Date"], errors="coerce")
    return dates[raw["Vote_Count"] > 0].max()


# --------------------------------------------------------------------------- #
# Cleaning and feature engineering
# --------------------------------------------------------------------------- #
def clean_movies(raw: pd.DataFrame, min_votes: int = MIN_VOTES) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build the movie-level table and a log of row counts at each step.

    No movie is dropped silently. Rows are only removed when they are true
    duplicates (same title and release date). Movies with no votes stay in the
    catalogue, but their rating is set to missing because 0.0 means "not rated".
    """
    log = [("Raw file", len(raw), "")]

    movies = raw.rename(columns=RAW_COLUMNS).copy()
    movies["release_date"] = pd.to_datetime(movies["release_date"], errors="coerce")
    bad_dates = movies["release_date"].isna()
    movies = movies[~bad_dates]
    log.append(("Drop unparseable release dates", len(movies), f"{int(bad_dates.sum())} removed"))

    # Keep the entry with the most votes if the same title + date appears twice.
    before = len(movies)
    movies = (movies.sort_values("vote_count", ascending=False)
                    .drop_duplicates(["title", "release_date"])
                    .sort_values("popularity", ascending=False)
                    .reset_index(drop=True))
    log.append(("Drop duplicate title + release date", len(movies), f"{before - len(movies)} removed"))

    snapshot = infer_snapshot_date(raw)
    movies["movie_id"] = np.arange(len(movies))
    movies["release_year"] = movies["release_date"].dt.year
    movies["decade"] = (movies["release_year"] // 10) * 10
    movies["genre_list"] = split_genres(movies["genre"])
    movies["n_genres"] = movies["genre_list"].str.len()
    movies["is_english"] = movies["original_language"].eq("en")
    movies["released_by_snapshot"] = movies["release_date"] <= snapshot
    movies["has_votes"] = movies["vote_count"] > 0
    movies["rating"] = movies["vote_average"].where(movies["has_votes"])
    movies["rating_qualified"] = movies["vote_count"] >= min_votes

    log.append(("Movies with no votes (rating set to missing, kept in catalogue)",
                int((~movies["has_votes"]).sum()), "kept"))
    log.append((f"Rating-qualified movies (>= {min_votes} votes)",
                int(movies["rating_qualified"].sum()), "used for rating analysis"))

    assert movies["movie_id"].is_unique
    assert (movies["n_genres"] > 0).all(), "every movie needs at least one genre"
    assert movies.loc[movies["has_votes"], "rating"].between(0, 10).all()

    log_df = pd.DataFrame(log, columns=["step", "rows", "note"])
    return movies, log_df


def explode_genres(movies: pd.DataFrame) -> pd.DataFrame:
    """Return one row per movie per genre, with ``genre`` as a categorical column."""
    movie_genres = (movies.drop(columns="genre")
                          .explode("genre_list")
                          .rename(columns={"genre_list": "genre"})
                          .reset_index(drop=True))
    movie_genres["genre"] = movie_genres["genre"].astype("category")

    assert movie_genres["movie_id"].nunique() == len(movies), "a movie was lost in the explode"
    assert len(movie_genres) == movies["n_genres"].sum(), "row count must equal total genre tags"
    assert not movie_genres.duplicated(["movie_id", "genre"]).any(), "a movie lists the same genre twice"
    return movie_genres


# --------------------------------------------------------------------------- #
# Statistics
# --------------------------------------------------------------------------- #
def mean_ci(values: pd.Series, confidence: float = 0.95) -> tuple[float, float, float]:
    """Mean and t-based confidence interval of a numeric series."""
    values = values.dropna()
    n = len(values)
    mean = values.mean()
    if n < 2:
        return mean, np.nan, np.nan
    half_width = stats.t.ppf((1 + confidence) / 2, n - 1) * values.std(ddof=1) / np.sqrt(n)
    return mean, mean - half_width, mean + half_width


def genre_prevalence(movies: pd.DataFrame, movie_genres: pd.DataFrame) -> pd.DataFrame:
    """Number and share of movies tagged with each genre (shares sum to more than 100%)."""
    counts = movie_genres.groupby("genre", observed=True)["movie_id"].nunique()
    out = pd.DataFrame({"movies": counts, "pct_of_movies": counts / len(movies) * 100})
    return out.sort_values("movies", ascending=False)


def genre_rating_summary(movie_genres: pd.DataFrame, top_cutoff: float) -> pd.DataFrame:
    """Rating statistics per genre for rating-qualified movies.

    ``top_cutoff`` is the rating at the 75th percentile of all qualified
    movies, so ``pct_top_quartile`` should be about 25% for a genre that rates
    like everything else.
    """
    rated = movie_genres[movie_genres["rating_qualified"]]
    rows = []
    for genre, grp in rated.groupby("genre", observed=True):
        mean, low, high = mean_ci(grp["rating"])
        rows.append({
            "genre": genre,
            "movies": grp["movie_id"].nunique(),
            "mean_rating": mean,
            "ci_low": low,
            "ci_high": high,
            "median_rating": grp["rating"].median(),
            "pct_top_quartile": (grp["rating"] >= top_cutoff).mean() * 100,
        })
    return pd.DataFrame(rows).set_index("genre").sort_values("mean_rating", ascending=False)


def weighted_rating(vote_average: pd.Series, vote_count: pd.Series, prior_votes: float,
                    prior_mean: float) -> pd.Series:
    """Shrink each movie's rating toward ``prior_mean``.

    Behaves as if every movie had ``prior_votes`` extra votes at the overall
    average. A movie with few votes stays close to the average; a movie with
    many votes keeps almost its own rating. This is the same idea as IMDb's
    published "weighted rating" formula.
    """
    v, r = vote_count, vote_average
    return (v / (v + prior_votes)) * r + (prior_votes / (v + prior_votes)) * prior_mean


def correlation_table(df: pd.DataFrame, columns: list[str],
                      log_columns: tuple[str, ...] = ()) -> pd.DataFrame:
    """Pearson (raw and with ``log_columns`` log-scaled) and Spearman correlations.

    Comparing the three shows how much a raw Pearson value is driven by a few
    extreme observations: Spearman uses ranks, so it ignores how extreme they are.
    """
    rows = []
    for i, a in enumerate(columns):
        for b in columns[i + 1:]:
            pair = df[[a, b]].dropna()
            log_a = np.log10(pair[a]) if a in log_columns else pair[a]
            log_b = np.log10(pair[b]) if b in log_columns else pair[b]
            rows.append({
                "pair": f"{a} vs {b}",
                "pearson_raw": pair[a].corr(pair[b]),
                "pearson_log": log_a.corr(log_b),
                "spearman": pair[a].corr(pair[b], method="spearman"),
                "n": len(pair),
            })
    return pd.DataFrame(rows).set_index("pair")


def decade_genre_share(movies: pd.DataFrame, movie_genres: pd.DataFrame, genres: list[str],
                       start_decade: int = 1970) -> pd.DataFrame:
    """Share of each decade's movies tagged with each genre, plus the movie count per decade."""
    in_range = movie_genres[movie_genres["decade"] >= start_decade]
    movies_per_decade = movies[movies["decade"] >= start_decade].groupby("decade")["movie_id"].nunique()
    share = (in_range[in_range["genre"].astype(str).isin(genres)]
             .assign(genre=lambda d: d["genre"].astype(str))
             .groupby(["decade", "genre"])["movie_id"].nunique()
             .unstack("genre")
             .reindex(columns=genres)
             .div(movies_per_decade, axis=0)
             .mul(100))
    share.insert(0, "movies_in_decade", movies_per_decade)
    return share


def language_gap_within_genres(movie_genres: pd.DataFrame, min_movies: int = 30) -> pd.DataFrame:
    """Mean rating of non-English minus English movies, compared inside each genre.

    Comparing within a genre removes the part of the overall gap that comes
    from genre mix (for example, a high share of animation among Japanese films).
    """
    rated = movie_genres[movie_genres["rating_qualified"]]
    rows = []
    for genre, grp in rated.groupby("genre", observed=True):
        en, non_en = grp[grp["is_english"]]["rating"], grp[~grp["is_english"]]["rating"]
        if len(en) >= min_movies and len(non_en) >= min_movies:
            rows.append({"genre": genre, "english_movies": len(en), "non_english_movies": len(non_en),
                         "english_mean": en.mean(), "non_english_mean": non_en.mean(),
                         "gap": non_en.mean() - en.mean()})
    return pd.DataFrame(rows).set_index("genre").sort_values("gap", ascending=False)


# --------------------------------------------------------------------------- #
# Chart styling
# --------------------------------------------------------------------------- #
PRIMARY = "#2a6f97"
MUTED = "#a7b3bd"
ACCENT = "#c8553d"
INK = "#1f2933"


def set_chart_style() -> None:
    """Apply one restrained visual theme to every chart in the project."""
    import matplotlib as mpl
    import seaborn as sns

    sns.set_theme(style="whitegrid", context="notebook")
    mpl.rcParams.update({
        "figure.dpi": 110,
        "savefig.dpi": 150,
        "savefig.bbox": "tight",
        "axes.titlesize": 13,
        "axes.titleweight": "bold",
        "axes.titlelocation": "left",
        "axes.labelsize": 11,
        "axes.labelcolor": INK,
        "axes.edgecolor": "#d0d7de",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "grid.color": "#eef1f4",
        "xtick.color": INK,
        "ytick.color": INK,
        "legend.frameon": False,
    })
