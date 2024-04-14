import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px
import math

# from fetch_data import fetch_country_data, fetch_country_index
from plotting import *
from calc_index import *
from data_preprocess import get_clean_data

# Page configuration
st.set_page_config(
    page_title="Food Price Tracker",
    layout="wide",
    initial_sidebar_state="expanded")

alt.themes.enable("dark")

# Load data
country_data = pd.read_csv(
    'data/raw/wfp_food_prices_jpn.csv',
    parse_dates=["date"],
    header=0,
    skiprows=[1],
)
country_data = get_clean_data(country_data)

# Sidebar
with st.sidebar:
    st.title('Food Price Tracker')
    
    # country_options = country_index.index.to_list()
    country_options = ['Japan']
    country_dropdown = st.selectbox(
        label='Country',
        options=country_options,
        index=0,
        )

    ## date
    min_date_allowed = country_data.date.min()
    max_date_allowed = country_data.date.max()
    start_date = max(country_data.date.max() + pd.tseries.offsets.DateOffset(years=-2), country_data.date.min())
    end_date = country_data.date.max()
    date_range = st.date_input(
        label='Date',
        value=[start_date, end_date],
        min_value=min_date_allowed,
        max_value=max_date_allowed,
        )

    commodities_options = country_data.commodity.value_counts().index.tolist()
    commodities_selection = commodities_options[:2]
    commodities_dropdown = st.multiselect(label='Commodities', 
                                          options=commodities_options, 
                                          default=commodities_selection,
                                          )

    markets_options = country_data.market.value_counts().index.tolist()
    markets_selection = markets_options[:2]
    markets_dropdown = st.multiselect(label='Markets', 
                                      options=markets_options, 
                                      default=markets_selection,
                                      )
    
    relative_change_options = ['Month-over-Month', 'Year-over-Year']
    relative_change_dropdown = st.selectbox(
        label='Relative Change',
        options=relative_change_options,
        index=0,
        )

# Elements
country_data = generate_food_price_index_data(country_data, pd.to_datetime(date_range), markets_dropdown, commodities_dropdown)
commodities_line = generate_line_chart(
    country_data, pd.to_datetime(date_range), markets_dropdown, commodities_dropdown
)
commodities_figure = generate_figure_chart(
    country_data
)
num_markets = len(markets_dropdown)
num_commodities = len(commodities_dropdown)
values_markets = ['National'] + markets_dropdown
values_commodities = ['Food Price Index'] + commodities_dropdown

# Dashboard Main Panel
rows_l0 = []
for i in range(num_markets+1):
    rows_l1 = []

    first_row = st.empty()
    rows_l1.append(first_row)

    second_row = st.columns([4, 6], gap='medium')
    rows_l1.append(second_row)

    third_row = st.empty()
    rows_l1.append(third_row)

    fourth_row = st.divider()
    rows_l1.append(fourth_row)

    rows_l0.append(rows_l1)

# Dashboard Detail
for row_num, row in enumerate(rows_l0):
    # To be refactored
    num_row = math.floor(num_commodities**0.5)
    num_col = math.ceil(num_commodities/num_row)

    with row[0]:
        market = values_markets[row_num]
        st.markdown(f'### {market}')

    with row[1][0]:
        commodity_num = 0
        commodity = values_commodities[commodity_num]
        card_name = commodity
        card_data = commodities_figure[(commodities_figure['commodity'] == commodity) & (commodities_figure['market'] == market)]
        card_value = "${:.2f}".format(card_data['usdprice'].iloc[0])
        card_delta_mom = f"{card_data['mom'].iloc[0]:.2%} MoM"
        card_delta_yoy = f"{card_data['yoy'].iloc[0]:.2%} YoY"
        card_help = "XX",
        with st.container(border=True, height=125*num_row):
            st.metric(label=card_name,
                    value=card_value,
                    delta = (card_delta_mom if relative_change_dropdown == 'Month-over-Month' else card_delta_yoy),
                    )
        commodity_num += 1

    with row[1][1]:
        # To be refactored
        row_l2 = []
        for i in range(num_row):
            row_l2.append(st.columns(num_col, gap='small'))
            
        for i in range(len(row_l2)):
            for col_j in row_l2[i]:
                with col_j:
                    if commodity_num <= num_commodities:
                        commodity = values_commodities[commodity_num]
                        card_name = commodity
                        card_data = commodities_figure[(commodities_figure['commodity'] == commodity) & (commodities_figure['market'] == market)]
                        card_value = "${:.2f}".format(card_data['usdprice'].iloc[0])
                        card_delta_mom = f"{card_data['mom'].iloc[0]:.2%} MoM"
                        card_delta_yoy = f"{card_data['yoy'].iloc[0]:.2%} YoY"
                        with st.container(border=True):
                            st.metric(label=card_name,
                                    value=card_value,
                                    delta = (card_delta_mom if relative_change_dropdown == 'Month-over-Month' else card_delta_yoy),
                                    )
                        commodity_num += 1
                    else:
                        st.empty()

    with row[2]:
        with st.container(border=True):
            st.altair_chart(commodities_line[0], use_container_width=True)

