from pathlib import Path
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
CLEAN = ROOT / "data" / "clean"
DB = ROOT / "data" / "project.db"


def clean_price(series):
    """
    Convert Airbnb price strings into numeric values.

    Removes dollar signs and commas while preserving missing values.

    Parameters
    ----------
    series : pandas.Series
        Series containing price values such as '$409.00'.

    Returns
    -------
    pandas.Series
        Price values converted to floats.
    """
    return (
        series
        .str.replace("$", "", regex=False)
        .str.replace(",", "", regex=False)
        .astype(float)
    )


def build_locations(df):
    """
    Build the location lookup table from the raw listings data.

    Each Barcelona neighbourhood appears once and retains its
    corresponding district. A numeric location_id is created for use
    as a foreign key in the listings table.

    Parameters
    ----------
    df : pandas.DataFrame
        Raw listings data containing neighbourhood and district fields.

    Returns
    -------
    pandas.DataFrame
        Location table containing location_id, neighbourhood_name
        and district_name.
    """
    locations = (
        df[
            [
                "neighbourhood_cleansed",
                "neighbourhood_group_cleansed"
            ]
        ]
        .drop_duplicates()
        .reset_index(drop=True)
    )

    locations.insert(
        0,
        "location_id",
        range(1, len(locations) + 1)
    )

    return locations.rename(columns={
        "neighbourhood_cleansed": "neighbourhood_name",
        "neighbourhood_group_cleansed": "district_name"
    })


def clean_reviews(df):
    """
    Keep and clean the review fields required for the analysis.

    The original review ID and listing relationship are retained,
    while review dates are converted to datetime values.

    Parameters
    ----------
    df : pandas.DataFrame
        Raw Inside Airbnb reviews data.

    Returns
    -------
    pandas.DataFrame
        Cleaned review data containing review_id, listing_id
        and review_date.
    """
    reviews = df[
        ["id", "listing_id", "date"]
    ].copy()

    reviews = reviews.rename(columns={
        "id": "review_id",
        "date": "review_date"
    })

    reviews["review_date"] = pd.to_datetime(
        reviews["review_date"],
        errors="coerce"
    )

    return reviews


def check_foreign_keys(child_df, child_key, parent_df, parent_key):
    """
    Count child records whose foreign key has no matching parent record.

    This is used before loading data into SQLite so broken relationships
    can be identified rather than being silently lost during joins.

    Parameters
    ----------
    child_df : pandas.DataFrame
        Table containing the foreign key.
    child_key : str
        Name of the foreign-key column.
    parent_df : pandas.DataFrame
        Parent table containing the referenced key.
    parent_key : str
        Name of the referenced parent key.

    Returns
    -------
    int
        Number of child rows without a matching parent record.
    """
    return (
        ~child_df[child_key]
        .isin(parent_df[parent_key])
    ).sum()