import itertools
import pandas as pd
import country_converter as coco

from hdx.api.configuration import Configuration
from hdx.data.dataset import Dataset

# Data Loading

# create HDX configuration
Configuration.create(
    hdx_site="prod",
    user_agent="DSCI-532_2024_19_food-price-tracker-indiv",
    hdx_read_only=True,
)

def fetch_country_index():
    """
    Fetch country index and preprocess into dataframe.

    Returns
    -------
    pd.DataFrame
        Dataframe that contains all countries in the WFP dataset, and their corresponding HDX entries.
        Metadata such as URL, Start / End Dates, are included

    Examples
    --------
    >>> country_index = fetch_country_index()
    """

    cc = coco.CountryConverter()

    country_index_df = pd.read_csv(
        Dataset.read_from_hdx("global-wfp-food-prices").get_resource(0)["url"],
        parse_dates=["start_date", "end_date"],
        header=0,
        skiprows=[1],
    )

    country_index_df = country_index_df.assign(
        country=cc.pandas_convert(series=country_index_df.countryiso3, to="name_short"),
        hdx_identifier=country_index_df.url.str.rsplit("/", n=1).str[1],
    ).set_index("country")

    return country_index_df


def fetch_country_data(country, country_index_df=fetch_country_index()):
    """
    Fetch and preprocess data from HDX (https://data.humdata.org/)
    Dynamically load the corresponding country dataset and preprocess.

    Parameters
    ----------
    country : str
        The country of which data should be recieved. Must be within the HDX and country_index_df. By default "Japan"

    country_index_df : pd.DataFrame, optional
        Index dataset from "global-wfp-food-prices" in the HDX, the output from fetch_country_index_df(). By default, the output from fetch_country_index_df().

    Returns
    -------
    pd.DataFrame
        Dataframe of WFP data from the given country, retrieved from the HDX and minimially preprocessed.

    Examples
    --------
    >>> country_json = fetch_country_data("Japan")
    """

    columns_to_keep = [
        "date",
        "market",
        "latitude",
        "longitude",
        "commodity",
        "unit",
        "usdprice",
    ]

    country_df = pd.read_csv(
        Dataset.read_from_hdx(
            country_index_df.loc[country, "hdx_identifier"]
        ).get_resource(0)["url"],
        parse_dates=["date"],
        header=0,
        skiprows=[1],
    )[columns_to_keep]

    return country_df

# Data Preprocessing

def filter_major_data(data, date_abundance_threshold=0.5, market_abundance_threshold=0.7):
    """
    Filter major data based on specified thresholds for date and market abundance.

    Parameters
    ----------
    data : pandas.DataFrame
        Input food price raw data.
    date_abundance_threshold : float, optional
        The threshold percentage of data existence for each (commodity, market) pair relative to the full duration length. Defaults to 0.5.
    market_abundance_threshold : float, optional
         The threshold percentage of markets where data of a commodity exists, relative to the total number of markets. Defaults to 0.7.

    Returns
    -------
    pandas.DataFrame
        A DataFrame containing major data filtered based on the specified thresholds.

    """

    # Default Info
    columns_to_keep = [
        "date",
        "market",
        "latitude",
        "longitude",
        "commodity",
        "unit",
        "usdprice",
    ]

    clean_data_df = data

    # Rule 0 - Deduplication on unit and (date, commodity, market)
    map_df = (
        clean_data_df.groupby(["commodity", "unit"])
        .agg({"unit": "count"})
        .groupby(["commodity"])
        .idxmax()
    )
    map_df["unit"] = map_df["unit"].apply(lambda x: x[1])
    map_df = map_df.reset_index()
    clean_data_df = clean_data_df.merge(
        map_df, how="inner", on=["commodity", "unit"]
    )
    clean_data_df = (
        clean_data_df[columns_to_keep]
        .groupby(columns_to_keep[:-1])
        .first(["usdprice"])
        .reset_index()
    )

    # Rule 1 - data existence for each (commodity, market) pair relative to the full duration length >= x%
    num_date = clean_data_df["date"].nunique()
    map_df = (
        clean_data_df.groupby(["market", "commodity"]).agg(
            {"usdprice": "count"}
        )
        >= date_abundance_threshold * num_date
    )
    map_df = map_df.rename(columns={"usdprice": "is_kept"})
    clean_data_df = clean_data_df.merge(
        map_df, how="left", on=["market", "commodity"]
    )
    clean_data_df = clean_data_df[
        clean_data_df["is_kept"] == True
    ].drop(columns=["is_kept"])

    # Rule 2 - data of a commodity exists, relative to the total number of markets >= x%
    num_market = clean_data_df["market"].nunique()
    map_df = (
        clean_data_df.groupby(["commodity"]).agg(
            {"market": "nunique"}
        )
        >= market_abundance_threshold * num_market
    )
    map_df = map_df.rename(columns={"market": "is_kept"})
    clean_data_df = clean_data_df.merge(
        map_df, how="left", on=["commodity"]
    )
    clean_data_df = clean_data_df[
        clean_data_df["is_kept"] == True
    ].drop(columns=["is_kept"])

    return clean_data_df

def fill_missing_data(data, method="forward"):
    """
    Fills missing values in the USD price column based on specified method.

    Parameters
    ----------
    data : pandas.DataFrame
        Input food price raw data.
    method : str, optional
        Method to fill missing values. Default is "forward" (forward fill).

    Returns
    -------
    pandas.DataFrame
        A DataFrame with missing values filled based on the specified method.

    """

    # Default Info
    columns_to_keep = [
        "date",
        "market",
        "latitude",
        "longitude",
        "commodity",
        "unit",
        "usdprice",
    ]

    # Generate dataframe with full combinations of factors
    full_data_df = pd.DataFrame(
        itertools.product(
            pd.date_range(data["date"].min(), data["date"].max(), freq='MS') + pd.DateOffset(days=14),
            # data["date"].unique(),
            data["market"].unique(),
            data["commodity"].unique(),
        ),
        columns=["date", "market", "commodity"],
    )

    # Fill the missing value per (date, commodity, market)
    full_data_df = full_data_df.merge(
        data, how="left", on=["date", "market", "commodity"]
    )
    if method == "forward":
        full_data_df = full_data_df.merge(
            full_data_df.groupby(
                ["market", "commodity"]
            ).ffill(),
            how="inner",
            left_index=True,
            right_index=True,
            suffixes=("_drop", None),
        )
    full_data_df = full_data_df[columns_to_keep].dropna(
        subset=["usdprice"], axis=0
    )

    return full_data_df

def get_clean_data(data_df):
    """
    Returns data containing cleaned data.

    Parameters
    ----------
    data_df : str
        Raw data.

    Returns
    -------
    pandas.DataFrame
        Dataframe containing cleaned major data.
    """

    # data_df = pd.read_json(StringIO(data_json), orient='split')
    data_df = filter_major_data(data_df)
    data_df = fill_missing_data(data_df)

    # return data_df.to_json(date_format='iso', orient='split')
    return data_df

# Data Enrichment

def generate_food_price_index_data(data, widget_date_range, widget_market_values, widget_commodity_values):
    """
    Generate food price index data based on the selected markets and commodities.

    Parameters
    ----------
    data : pandas.DataFrame
        The dataset containing price information for various commodities across different markets.
    widget_date_range : tuple
        A tuple containing the start and end dates for filtering the data.        
    widget_market_values : list
        A list of selected market names to filter the data.
    widget_commodity_values : list
        A list of selected commodity names to include in the food price index calculation.

    Returns
    -------
    pandas.DataFrame
        A DataFrame containing the original data appended with the calculated food price index
        for the selected markets and commodities. 

    Examples
    --------
    >>> import pandas as pd
    >>> data = pd.DataFrame({
    ...     'date': ['2022-01-01', '2022-01-01', '2022-01-02'],
    ...     'market': ['A', 'B', 'A'],
    ...     'latitude': [1, 2, 1],
    ...     'longitude': [1, 2, 1],
    ...     'commodity': ['Rice', 'Radish', 'Sugar'],
    ...     'unit': ['kg', 'kg', 'kg'],
    ...     'usdprice': [1.0, 2.0, 3.0]
    ... })
    >>> widget_market_values = ['A', 'B']
    >>> widget_commodity_values = ['Rice', 'Radish', 'Sugar']
    >>> generate_food_price_index_data(data, widget_market_values, widget_commodity_values)
    """

    # Default Info
    columns_to_keep = [
        "date",
        "market",
        "latitude",
        "longitude",
        "commodity",
        "unit",
        "usdprice",
    ]
    
    # Generate Food Price Index Data
    price_data = data[columns_to_keep]
    price_data = price_data[
        price_data.date.between(
            widget_date_range[0], widget_date_range[1]
        )
        & (price_data.commodity.isin(widget_commodity_values))
        & (price_data.market.isin(widget_market_values))
    ]

    # Calculate index (formula: sum of the index by date and market)
    index = (
        price_data.groupby(
            ["date", "market", "latitude", "longitude"]
        ).agg({
            "usdprice": "sum"
        })
    ).reset_index()

    # Aggregate price index back to the price data
    index['commodity'] = "Food Price Index"
    index["unit"] = "AGG"
    price_data = pd.concat((price_data, index), axis=0, ignore_index=True)

    return price_data

def generate_overall_data(data):
    """
    Generate overall data based on the selected markets and commodities.

    Parameters
    ----------
    data : pandas.DataFrame
        The dataset containing price information for various commodities across different markets.

    Returns
    -------
    pandas.DataFrame
        A DataFrame containing the original data appended with the calculated food price index
        for the selected markets and commodities. 

    Examples
    --------
    >>> import pandas as pd
    >>> data = pd.DataFrame({
    ...     'date': ['2022-01-01', '2022-01-01', '2022-01-02'],
    ...     'market': ['A', 'B', 'A'],
    ...     'latitude': [1, 2, 1],
    ...     'longitude': [1, 2, 1],
    ...     'commodity': ['Rice', 'Radish', 'Sugar'],
    ...     'unit': ['kg', 'kg', 'kg'],
    ...     'usdprice': [1.0, 2.0, 3.0]
    ... })
    >>> generate_food_price_index_data(data)
    """

    # Default Info
    columns_to_keep = [
        "date",
        "market",
        "latitude",
        "longitude",
        "commodity",
        "unit",
        "usdprice",
    ]
    
    # Generate Food Price Index Data
    price_data = data[columns_to_keep]

    # Calculate index (formula: average of the index by date and commodity)
    overall_data = (
        price_data.groupby(["date", "commodity", "unit"])
        .agg({"usdprice": "mean"})
        .reset_index()
    )
    overall_data['market'] = "Overall"
    price_data = pd.concat((price_data, overall_data), axis=0, ignore_index=True)

    return price_data

if __name__ == "__main__":
    pass