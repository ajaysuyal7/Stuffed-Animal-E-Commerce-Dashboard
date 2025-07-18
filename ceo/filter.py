import streamlit as st
import pandas as pd

# filter for CEO
def apply_filters(filtered_df):
    st.sidebar.header("📂 Filter Data")

    utm_filter = st.sidebar.multiselect("UTM Source", filtered_df["utm_source"].dropna().unique())
    device_filter = st.sidebar.multiselect("Device Type", filtered_df["device_type"].dropna().unique())
    product_filter = st.sidebar.multiselect("Product Name", filtered_df["product_name"].dropna().unique())
    campaign_filter = st.sidebar.multiselect("UTM Campaign", filtered_df["utm_campaign"].dropna().unique())

    filtered_df=filtered_df.copy()

    if utm_filter:
        filtered_df = filtered_df[filtered_df["utm_source"].isin(utm_filter)]
    if device_filter:
        filtered_df = filtered_df[filtered_df["device_type"].isin(device_filter)]
    if product_filter:
        filtered_df = filtered_df[filtered_df["product_name"].isin(product_filter)]
    if campaign_filter:
        filtered_df = filtered_df[filtered_df["utm_campaign"].isin(campaign_filter)]
    return filtered_df


##################

#filter for marketing
def apply_filter(order_data, website_pageviews, website_sessions):
    st.sidebar.title("🔍 Filters")

    # --- Date conversion ---
    order_data['order_date'] = pd.to_datetime(order_data['order_date'])
    website_pageviews['created_at'] = pd.to_datetime(website_pageviews['created_at'])
    website_sessions['session_created_at'] = pd.to_datetime(website_sessions['session_created_at'])

    # --- Setup default values ---
    product_list = sorted(order_data['product_name'].dropna().unique())
    utm_sources = sorted(order_data['utm_source'].dropna().unique())
    device_types = sorted(order_data['device_type'].dropna().unique())
    min_date = order_data['order_date'].min().to_pydatetime()
    max_date = order_data['order_date'].max().to_pydatetime()


    # --- Handle Clear Filters ---
    if st.sidebar.button("❌ Clear Filters"):
        st.session_state['selected_products'] = []
        st.session_state['selected_sources'] = []
        st.session_state['selected_devices'] = []
        st.session_state['selected_date_range'] = (min_date, max_date)

    # --- Multiselects with session_state fallback ---
    selected_products = st.sidebar.multiselect(
        "🧸 Product(s)",
        options=product_list,
        default=st.session_state.get('selected_products', []),
        key='selected_products'
    )

    selected_sources = st.sidebar.multiselect(
        "🎯 UTM Source(s)",
        options=utm_sources,
        default=st.session_state.get('selected_sources', []),
        key='selected_sources'
    )

    selected_devices = st.sidebar.multiselect(
        "💻 Device Type(s)",
        options=device_types,
        default=st.session_state.get('selected_devices', []),
        key='selected_devices'
    )


    # Handle session state default date range
    default_range = st.session_state.get('selected_date_range', (min_date, max_date))
    if isinstance(default_range[0], pd.Timestamp):
        default_range = (default_range[0].to_pydatetime(), default_range[1].to_pydatetime())

    selected_date_range = st.sidebar.slider(
        "📅 Date Range:",
        min_value=min_date,
        max_value=max_date,
        value=default_range,
        format="YYYY-MM-DD",
        key='selected_date_range'
    )

    # --- Filters (All shown if nothing selected) ---
    product_mask = order_data['product_name'].isin(selected_products) if selected_products else True
    source_mask = order_data['utm_source'].isin(selected_sources) if selected_sources else True
    device_mask = order_data['device_type'].isin(selected_devices) if selected_devices else True
    date_mask = (order_data['order_date'] >= selected_date_range[0]) & \
                (order_data['order_date'] <= selected_date_range[1])

    filtered_order_data = order_data[product_mask & source_mask & device_mask & date_mask]

    # Filter pageviews and sessions
    filtered_pageviews = website_pageviews[
        (website_pageviews['created_at'] >= selected_date_range[0]) &
        (website_pageviews['created_at'] <= selected_date_range[1])
    ]
    filtered_session_ids = filtered_pageviews['website_session_id'].unique()
    filtered_sessions = website_sessions[
        website_sessions['website_session_id'].isin(filtered_session_ids)
    ]

    return {
        "order_data": filtered_order_data,
        "pageviews": filtered_pageviews,
        "sessions": filtered_sessions,
        "selected_products": selected_products,
        "selected_sources": selected_sources,
        "selected_devices": selected_devices,
        "selected_date_range": selected_date_range
    }



