# Data

The dataset is not committed to this repository because its redistribution terms have not been verified.

1. Download `mymoviedb.csv` from the [9000+ Movies Dataset](https://www.kaggle.com/datasets/disham993/9000-movies-dataset) on Kaggle (free account required).
2. Save it as `data/raw/mymoviedb.csv`.

Alternatively, set the `MOVIE_DATA_PATH` environment variable to the file's location.

Expected file: 9,827 rows, columns `Release_Date, Title, Overview, Popularity, Vote_Count, Vote_Average, Original_Language, Genre, Poster_Url`. The loader checks the column names and stops with a clear error if they differ.
