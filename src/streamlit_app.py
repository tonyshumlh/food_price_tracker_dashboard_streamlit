import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px
import math

# from fetch_data import fetch_country_data, fetch_country_index
# from plotting import *
# from calc_index import *
# from data_preprocess import get_clean_data

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
#TBC data preprocess

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
    # df_selected_year = df_reshaped[df_reshaped.year == selected_year]
    # df_selected_year_sorted = df_selected_year.sort_values(by="population", ascending=False)

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

# Dashboard Main Panel
rows_l0 = []
num_markets = len(markets_dropdown)
num_commodities = len(commodities_dropdown)
for i in range(num_markets+1):
    rows_l1 = []

    first_row = st.columns([4, 6], gap='medium')
    rows_l1.append(first_row)

    second_row = st.container()
    rows_l1.append(second_row)

    third_row = st.divider()
    rows_l1.append(third_row)

    rows_l0.append(rows_l1)

# Dashboard Detail
for row in rows_l0:
    with row[0][0]:
        st.markdown('#### 0')

        card_name = 'Index'
        card_value = '$2.0'
        card_delta1 = '-0.52% MoM'
        card_delta2 = '-0.52% YoY'
        with st.container(border=True):
            st.metric(label=card_name,
                    value=card_value,
                    delta=card_delta2
                    )

    with row[0][1]:
        num_row = math.floor(num_commodities**0.5)
        num_col = math.ceil(num_commodities/num_row)
        row_l2 = []
        for i in range(num_row):
            row_l2.append(st.columns(num_col, gap='small'))
        for i in range(len(row_l2)):
            for col_j in row_l2[i]:
                with col_j:
                    with st.container(border=True):
                        st.metric(label=card_name,
                                value=card_value,
                                delta=card_delta2
                                )

    with row[1]:
        st.markdown('#### 2')
        st.write('Some chart')
