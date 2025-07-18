import streamlit as st
import pandas as pd

data_path = r"D:\Intership\Proj-03 Digital-Product Analytics\data\\"
# Sql server connection function
# cache connection to the database to avoid slow reloads

@st.cache_data
def load_csv(filename):
    return pd.read_csv(data_path + filename)

def load_all_data():
    orders = load_csv("orders360.csv")
    order_items = load_csv("order_items.csv")
    refunds = load_csv("order_item_refunds.csv")
    products = load_csv("products.csv")
    pageviews = load_csv("website_pageviews.csv")
    website_session = load_csv("websitesession360.csv")
    customers = load_csv("customers360.csv")

    return orders, order_items, refunds, products, pageviews, website_session, customers

@st.cache_data(show_spinner=False)
def preprocess_session_path_data(website_pageviews):
    website_pageviews['created_at'] = pd.to_datetime(website_pageviews['created_at'])

    # Session paths
    session_paths = (
        website_pageviews.sort_values(['website_session_id', 'created_at'])
        .groupby('website_session_id')['pageview_url']
        .apply(lambda x: ' → '.join(x))
        .reset_index()
    )

    # Session durations
    session_duration = (
        website_pageviews.groupby('website_session_id')['created_at']
        .agg(session_start='min', session_end='max')
        .reset_index()
    )
    session_duration['session_duration_min'] = (
        (session_duration['session_end'] - session_duration['session_start']).dt.total_seconds() / 60
    )

    # Combine both
    combined = session_paths.merge(session_duration, on='website_session_id')
   
    return combined