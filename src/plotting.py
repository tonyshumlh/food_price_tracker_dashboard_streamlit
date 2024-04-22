import numpy as np
import pandas as pd
import altair as alt
alt.data_transformers.enable('vegafusion')

def generate_figure_chart(data):
    """
    Generate figure charts displaying the latest average price and period-over-period change for specified commodities.

    Parameters
    ----------
    data : pandas.DataFrame
        Input food price data.
    widget_date_range : tuple
        A tuple containing the start and end dates for filtering the data.
    widget_market_values : list
        A list of market used to filter the data.
    widget_commodity_values : list
        A list of commodities for which figure charts will be generated.

    Returns
    -------
    list of altair.Chart
        A list of Altair figure charts displaying the latest average price and period-over-period change.

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
    >>> generate_figure_chart(data)
    """

    # Default Info
    columns_to_keep = [
        "date",
        "market",
        "commodity",
        "unit",
        "usdprice",
    ]

    # Generate latest average price and period-over-period change
    price_data = data[columns_to_keep]
    price_data = price_data.set_index("date").groupby(
        ["market", "commodity", "unit"]
    )
    price_summary = (
        price_data["usdprice"].apply(lambda x: x).reset_index()
    )
    price_summary["mom"] = (
        price_data["usdprice"]
        .apply(lambda x: x.pct_change(1))
        .reset_index()["usdprice"]
    )
    price_summary["yoy"] = (
        price_data["usdprice"]
        .apply(lambda x: x.pct_change(12))
        .reset_index()["usdprice"]
    )
    price_summary = (
        price_summary.groupby(["market", "commodity", "unit"])
        .last()
        .reset_index()
    )

    return price_summary

def generate_line_chart(data):
    """
    Generates a list of line charts, each representing the price trends of different commodities over time within specified marketplaces.

    The function filters the input data based on a given date range and a list of market values. 
    It then iterates through a list of commodities, creating an individual line chart for each one that visualizes its price trend in USD.

    Parameters
    ----------
    data : pd.DataFrame
        A Pandas DataFrame containing the commodities data including dates, markets, and prices.
        
    widget_date_range : tuple
        A tuple of two strings ('YYYY-MM-DD', 'YYYY-MM-DD') representing the start and end dates for filtering the data.
        
    widget_market_values : list of str)
        A list of string values representing the markets to include in the chart.
    
    widget_commodity_values : list of str)
        A list of string values representing the commodities for which the line charts will be generated.

    Returns:
    list of alt.Chart
        A list containing Altair Chart objects, each representing a line chart for a specific commodity.
        Each chart visualizes the price trend for a specific commodity across all specified markets over the given time period. 
        The y-axis shows the price in USD, and the x-axis shows time by year. 

    Example:
    >>> generate_line_chart(df, ('2011-01-01', '2022-01-01'), ['Osaka', 'Tokyo'], ['Rice', 'Milk'])
    # Returns a list of Altair Chart objects for 'Rice' and 'Milk' with specified configurations.
    """

    # Filter the data for the selected time period and markets
    price_data = data

    charts = {}

    # Change the default color scheme of Altair
    custom_color_scheme = ['#f58518', '#72b7b2', '#e45756', '#4c78a8', '#54a24b',
                           '#eeca3b', '#b279a2', '#ff9da6', '#9d755d', '#bab0ac']
    custom_color_scale = alt.Scale(range=custom_color_scheme)

    # Create charts for each of the commodity
    for market in price_data['market'].unique():
        # Filter the data for the specific commodity
        item_data = price_data[price_data.market.isin([market])]
     
        # Create the chart
        chart = alt.Chart(item_data).mark_line(
            size=3,
            interpolate='monotone', 
            point=alt.OverlayMarkDef(shape='circle', size=50, filled=True)
        ).encode(
            x=alt.X('date:T', axis=alt.Axis(format='%Y-%m', title='Time')),
            y=alt.Y('usdprice:Q', title='Price in USD', scale=alt.Scale(zero=False)),
            color=alt.Color('commodity:N', legend=alt.Legend(title='Commodity'), scale=custom_color_scale),
            tooltip=[
                alt.Tooltip('date:T', title='Time', format='%Y-%m'),
                alt.Tooltip('commodity', title='Commodity'),
                alt.Tooltip('usdprice:Q', title='Price in USD', format='.2f')
            ]
        ).configure_view(
            strokeWidth=0,
        ).configure_axisX(
            grid=False
        ).configure_axisY(
            grid=False
        )

        # Add the chart to the list of charts
        charts[market] = chart

    # Create charts for each of the market
    for commodity in price_data['commodity'].unique():
        # Filter the data for the specific market
        item_data = price_data[price_data.commodity.isin([commodity])]
     
        # Create the chart
        chart = alt.Chart(item_data).mark_line(
            size=3,
            interpolate='monotone', 
            point=alt.OverlayMarkDef(shape='circle', size=50, filled=True)
        ).encode(
            x=alt.X('date:T', axis=alt.Axis(format='%Y-%m', title='Time')),
            y=alt.Y('usdprice:Q', title='Price in USD', scale=alt.Scale(zero=False)),
            color=alt.Color('market:N', legend=alt.Legend(title='Market'), scale=custom_color_scale),
            tooltip=[
                alt.Tooltip('date:T', title='Time', format='%Y-%m'),
                alt.Tooltip('market', title='Market'),
                alt.Tooltip('usdprice:Q', title='Price in USD', format='.2f')
            ]
        ).configure_view(
            strokeWidth=0,
        ).configure_axisX(
            grid=False
        ).configure_axisY(
            grid=False
        )

        # Add the chart to the list of charts
        charts[commodity] = chart

    return charts

if __name__ == '__main__':
    pass
