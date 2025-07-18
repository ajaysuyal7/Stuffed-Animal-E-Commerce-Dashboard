
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import streamlit as st
from sklearn.preprocessing import StandardScaler
import plotly.graph_objects as go


# using plotly

def line_chart_conversion_rate_1(order_data, website_sessions):
    website_sessions['year_month'] = pd.to_datetime(website_sessions['session_created_at']).dt.to_period('M')
    order_data['year_month'] = pd.to_datetime(order_data['order_date']).dt.to_period('M')

    sessions_by_month = website_sessions.groupby('year_month')['website_session_id'].nunique().reset_index(name='total_sessions')
    converted_by_month = order_data.groupby('year_month')['website_session_id'].nunique().reset_index(name='converted_sessions')

    df = pd.merge(sessions_by_month, converted_by_month, on='year_month', how='left').fillna(0)
    df['conversion_rate_pct'] = (df['converted_sessions'] / df['total_sessions']) * 100
    df['year_month'] = df['year_month'].astype(str)

    fig = px.line(
        df,
        x='year_month',
        y='conversion_rate_pct',
        markers=True,
        title='Conversion Rate (%) by Year and Month',
        labels={'conversion_rate_pct': 'Conversion Rate (%)', 'year_month': 'Year-Month'}
    )
    fig.update_traces(line=dict(color='green'))
    fig.update_layout(xaxis_tickangle=45)

    st.plotly_chart(fig, use_container_width=True)


def line_chart_conversion_rate_by_product(order_data, website_sessions):
    # Ensure datetime format
    website_sessions['year_month'] = pd.to_datetime(website_sessions['session_created_at']).dt.to_period('M')
    order_data['year_month'] = pd.to_datetime(order_data['order_date']).dt.to_period('M')

    # --- Total sessions per month ---
    sessions_by_month = website_sessions.groupby('year_month')['website_session_id'].nunique().reset_index()
    sessions_by_month.rename(columns={'website_session_id': 'total_sessions'}, inplace=True)

    # --- Converted sessions per month and product ---
    converted = order_data.groupby(['year_month', 'product_name'])['website_session_id'].nunique().reset_index()
    converted.rename(columns={'website_session_id': 'converted_sessions'}, inplace=True)

    # Merge sessions to get conversion rate
    df = converted.merge(sessions_by_month, on='year_month', how='left')
    df['conversion_rate_pct'] = (df['converted_sessions'] / df['total_sessions']) * 100
    df['year_month'] = df['year_month'].astype(str)

    # Product filter
    all_products = df['product_name'].dropna().unique().tolist()
    selected_products = st.multiselect("🧸 Select Products:", sorted(all_products), default=all_products)

    filtered_df = df[df['product_name'].isin(selected_products)]

    # Plot using Plotly
    fig = px.line(
        filtered_df,
        x='year_month',
        y='conversion_rate_pct',
        color='product_name',
        title="Conversion Rate (%) by Year-Month and Product",
        markers=True,
        labels={'year_month': 'Year-Month', 'conversion_rate_pct': 'Conversion Rate %'}
    )

    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)


def pie_chart_total_sessions_1(website_sessions):
    data = website_sessions['utm_source'].fillna('Unknown')
    data = data[data.str.upper() != 'NULL']
    counts = data.value_counts().reset_index()
    counts.columns = ['utm_source', 'sessions']

    fig = px.pie(
        counts,
        names='utm_source',
        values='sessions',
        title='Total Sessions by UTM Source',
        hole=0.3
    )
    st.plotly_chart(fig, use_container_width=True)


def bar_chart_gross_revenue_1(order_data):
    df = order_data[order_data['utm_source'].notna()]
    df = df[df['utm_source'].str.upper() != 'NULL']
    revenue = df.groupby('utm_source')['price_usd'].sum().reset_index()
    revenue = revenue.sort_values(by='price_usd', ascending=False)

    fig = px.bar(
        revenue,
        x='utm_source',
        y='price_usd',
        text='price_usd',
        title='Gross Revenue by UTM Source',
        labels={'utm_source': 'UTM Source', 'price_usd_item': 'Gross Revenue (USD)'},
        color='utm_source'
    )
    fig.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
    fig.update_layout(xaxis_tickangle=45, showlegend=False)

    st.plotly_chart(fig, use_container_width=True)


def channel_kpi_heatmap(order_data, website_sessions, website_pageviews):
    # -- Bounce Rate --
    pageviews_per_session = website_pageviews.groupby("website_session_id").size().reset_index(name="pageview_count")
    bounced = pageviews_per_session[pageviews_per_session["pageview_count"] == 1]["website_session_id"]

    session_info = website_sessions.copy()
    session_info["is_bounce"] = session_info["website_session_id"].isin(bounced).astype(int)

    channel_kpis = session_info.groupby("utm_source").agg(
        total_sessions=('website_session_id', 'nunique'),
        total_users=('user_id', 'nunique'),
        bounce_sessions=('is_bounce', 'sum')
    ).reset_index()

    channel_kpis["bounce_rate_pct"] = (channel_kpis["bounce_sessions"] / channel_kpis["total_sessions"]) * 100
    channel_kpis["sessions_per_user"] = channel_kpis["total_sessions"] / channel_kpis["total_users"]

    # -- Order Metrics --
    orders_summary = order_data.groupby("utm_source").agg(
        orders=('order_id', 'nunique'),
        revenue=('price_usd_item', 'sum'),
        cogs=('cogs_usd_item', 'sum'),
        buyers=('user_id', 'nunique')
    ).reset_index()

    orders_summary["aov"] = orders_summary["revenue"] / orders_summary["orders"]
    orders_summary["gross_profit_pct"] = ((orders_summary["revenue"] - orders_summary["cogs"]) / orders_summary["revenue"]) * 100
    orders_summary["conversion_rate_pct"] = (orders_summary["orders"] / channel_kpis["total_sessions"]) * 100

    # -- Combine --
    matrix = channel_kpis.merge(orders_summary, on="utm_source", how="left")

    # -- Normalize KPIs (standardized heatmap)
    metric_cols = ['total_sessions', 'bounce_rate_pct', 'aov', 'conversion_rate_pct', 'gross_profit_pct', 'sessions_per_user']
    matrix_indexed = matrix.set_index('utm_source')[metric_cols]

    scaler = StandardScaler()
    normalized = scaler.fit_transform(matrix_indexed)
    normalized_df = pd.DataFrame(normalized, index=matrix_indexed.index, columns=matrix_indexed.columns)

    # -- Heatmap Plot
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.heatmap(
        normalized_df,
        cmap="coolwarm",
        annot=True,
        fmt=".2f",
        cbar_kws={'label': 'Z-Score (Standardized)'},
        ax=ax
    )
    ax.set_title("Channel vs KPIs (Normalized per KPI)", fontsize=14)
    plt.tight_layout()

    st.subheader("📊 Channel Matrix Heatmap")
    st.pyplot(fig)
    plt.clf()

    return matrix  # optional: return raw data table


def channel_kpi_heatmap_plotly(order_data, website_sessions, website_pageviews):
    # Bounce rate setup
    pageviews_per_session = website_pageviews.groupby("website_session_id").size().reset_index(name="pageview_count")
    bounced = pageviews_per_session[pageviews_per_session["pageview_count"] == 1]["website_session_id"]

    session_info = website_sessions.copy()
    session_info["is_bounce"] = session_info["website_session_id"].isin(bounced).astype(int)

    # Channel-based KPIs from session data
    channel_kpis = session_info.groupby("utm_source").agg(
        total_sessions=('website_session_id', 'nunique'),
        total_users=('user_id', 'nunique'),
        bounce_sessions=('is_bounce', 'sum')
    ).reset_index()

    channel_kpis["bounce_rate_pct"] = (channel_kpis["bounce_sessions"] / channel_kpis["total_sessions"]) * 100
    channel_kpis["sessions_per_user"] = channel_kpis["total_sessions"] / channel_kpis["total_users"]

    # Order metrics
    orders_summary = order_data.groupby("utm_source").agg(
        orders=('order_id', 'nunique'),
        revenue=('price_usd', 'sum'),
        cogs=('cogs_usd', 'sum'),
        buyers=('user_id', 'nunique')
    ).reset_index()

    orders_summary["aov"] = orders_summary["revenue"] / orders_summary["orders"]
    orders_summary["gross_profit_pct"] = ((orders_summary["revenue"] - orders_summary["cogs"]) / orders_summary["revenue"]) * 100
    orders_summary["conversion_rate_pct"] = (orders_summary["orders"] / channel_kpis["total_sessions"]) * 100

    # Merge
    matrix = channel_kpis.merge(orders_summary, on="utm_source", how="left")

    # Select and normalize
    metric_cols = ['total_sessions', 'bounce_rate_pct', 'aov', 'conversion_rate_pct', 'gross_profit_pct', 'sessions_per_user']
    matrix_indexed = matrix.set_index('utm_source')[metric_cols]

    scaler = StandardScaler()
    normalized = scaler.fit_transform(matrix_indexed)
    normalized_df = pd.DataFrame(normalized, index=matrix_indexed.index, columns=matrix_indexed.columns)

    # Melt for plotly heatmap
    heatmap_df = normalized_df.reset_index().melt(id_vars='utm_source', var_name='KPI', value_name='Z-Score')

    fig = px.imshow(
        normalized_df.T,
        text_auto=".2f",
        color_continuous_scale='RdBu_r',
        aspect='auto',
        labels=dict(color='Z-Score'),
        title="Channel vs KPIs (Standardized - Plotly)"
    )

    fig.update_layout(
        xaxis_title="UTM Source",
        yaxis_title="KPI",
        xaxis_tickangle=45,
        height=500
    )

    st.subheader("📊 Channel Matrix Heatmap (Plotly)")
    st.plotly_chart(fig, use_container_width=True)

    # Optional: show raw matrix below
    with st.expander("📄 View Raw KPI Table"):
        st.dataframe(matrix.round(2))

    return matrix, normalized_df


def line_column_avg_time_by_session_path(combined):
    # Aggregate by path
    summary = (
        combined.groupby('pageview_url')
        .agg(avg_duration=('session_duration_min', 'mean'),
             session_count=('website_session_id', 'count'))
        .sort_values(by='avg_duration', ascending=False)
        .reset_index()
        # .head(20) 
    )

    # Plotly combo chart
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=summary['pageview_url'],
        y=summary['avg_duration'],
        name='Avg Duration (min)',
        marker_color='indianred',
        yaxis='y1'
    ))

    fig.add_trace(go.Scatter(
        x=summary['pageview_url'],
        y=summary['session_count'],
        name='Session Count',
        mode='lines+markers',
        marker=dict(color='steelblue'),
        yaxis='y2'
    ))

    fig.update_layout(
        title='📊 Avg Session Duration & Count by Session Path',
        xaxis=dict(title='Session Path', tickangle=90),
        yaxis=dict(title='Avg Session Duration (min)', side='left'),
        yaxis2=dict(title='Session Count', overlaying='y', side='right'),
        legend=dict(x=0.5, xanchor='center', y=1.1, orientation='h'),
        margin=dict(t=60, b=200),
        height=600,
        template='plotly_white'
    )

    return fig

def bounce_rate_stacked_column(website_sessions, bounced):
    
#    pageviews_per_session = website_pageviews.groupby("website_session_id").size().reset_index(name="pageview_count")
#   bounced = pageviews_per_session[pageviews_per_session["pageview_count"] == 1]["website_session_id"]

    
    # --- 1. Flag bounce sessions
    website_sessions = website_sessions.copy()
    website_sessions['is_bounce'] = website_sessions['website_session_id'].isin(bounced).astype(int)

    # --- 2. Group by utm_source and utm_campaign
    grouped = website_sessions.groupby(['utm_source', 'utm_campaign']).agg(
        total_sessions=('website_session_id', 'nunique'),
        bounce_sessions=('is_bounce', 'sum')
    ).reset_index()

    # --- 3. Calculate bounce rate
    grouped["bounce_rate_pct"] = (grouped["bounce_sessions"] / grouped["total_sessions"]) * 100

    # --- 4. Pivot for stacked chart
    pivot_df = grouped.pivot(index='utm_source', columns='utm_campaign', values='bounce_rate_pct').fillna(0)

    # --- 5. Build Plotly Figure
    fig = go.Figure()

    for campaign in pivot_df.columns:
        fig.add_trace(go.Bar(
            x=pivot_df.index,
            y=pivot_df[campaign],
            name=campaign
        ))

    # --- 6. Layout
    fig.update_layout(
        barmode='stack',
        title='📊 Bounce Rate % by UTM Source and Campaign',
        xaxis_title='UTM Source',
        yaxis_title='Bounce Rate (%)',
        legend_title='UTM Campaign',
        xaxis_tickangle=45,
        height=600,
        template='plotly_white'
    )

    return fig

def bounce_rate_stacked_column_by_content(website_sessions, bounced):
    # --- Copy and flag bounce sessions ---
    website_sessions = website_sessions.copy()
    website_sessions['is_bounce'] = website_sessions['website_session_id'].isin(bounced).astype(int)

    # --- Group by utm_source and utm_content ---
    grouped = website_sessions.groupby(['utm_source', 'utm_content']).agg(
        total_sessions=('website_session_id', 'nunique'),
        bounce_sessions=('is_bounce', 'sum')
    ).reset_index()

    # --- Bounce Rate Calculation ---
    grouped["bounce_rate_pct"] = (grouped["bounce_sessions"] / grouped["total_sessions"]) * 100

    # --- Pivot to wide format ---
    pivot_df = grouped.pivot(index='utm_source', columns='utm_content', values='bounce_rate_pct').fillna(0)

    # --- Create Stacked Column Chart ---
    fig = go.Figure()

    for content in pivot_df.columns:
        fig.add_trace(go.Bar(
            x=pivot_df.index,
            y=pivot_df[content],
            name=str(content)  # Ensure content is str
        ))

    fig.update_layout(
        barmode='stack',
        title='📊 Bounce Rate % by UTM Source and Content',
        xaxis_title='UTM Source',
        yaxis_title='Bounce Rate (%)',
        xaxis_tickangle=45,
        legend_title='UTM Content',
        height=600,
        template='plotly_white'
    )

    return fig

# --- 1. Line Chart: Total Sessions by Year and Month ---
def line_chart_total_sessions_over_time(website_sessions):
    website_sessions = website_sessions.copy()
    website_sessions['year_month'] = pd.to_datetime(website_sessions['session_created_at']).dt.to_period('M')
    sessions_by_month = website_sessions.groupby('year_month')['website_session_id'].nunique().reset_index()
    sessions_by_month['year_month'] = sessions_by_month['year_month'].astype(str)

    fig = px.line(
        sessions_by_month,
        x='year_month',
        y='website_session_id',
        title='📆 Total Sessions by Year and Month',
        markers=True,
        labels={'website_session_id': 'Total Sessions', 'year_month': 'Year-Month'}
    )
    fig.update_layout(xaxis_tickangle=45, template='plotly_white')
    return fig

# --- 2. Clustered Bar: Total Sessions by utm_source and device_type ---
def clustered_bar_sessions_by_source_device(website_sessions):
    grouped = website_sessions.groupby(['utm_source', 'device_type'])['website_session_id'].nunique().reset_index()
    fig = px.bar(
        grouped,
        x='utm_source',
        y='website_session_id',
        color='device_type',
        barmode='group',
        title='📊 Total Sessions by UTM Source and Device Type',
        labels={'website_session_id': 'Total Sessions', 'utm_source': 'UTM Source'}
    )
    fig.update_layout(xaxis_tickangle=45, template='plotly_white')
    return fig

# --- 3. Stacked Bar: Sessions by utm_source and utm_campaign ---
def stacked_bar_sessions_by_source_campaign(website_sessions):
    grouped = website_sessions.groupby(['utm_source', 'utm_campaign'])['website_session_id'].nunique().reset_index()
    pivot_df = grouped.pivot(index='utm_source', columns='utm_campaign', values='website_session_id').fillna(0)

    fig = go.Figure()
    for campaign in pivot_df.columns:
        fig.add_trace(go.Bar(
            x=pivot_df.index,
            y=pivot_df[campaign],
            name=campaign
        ))
    fig.update_layout(
        barmode='stack',
        title='📊 Sessions by UTM Source and Campaign',
        xaxis_title='UTM Source',
        yaxis_title='Sessions',
        xaxis_tickangle=45,
        template='plotly_white'
    )
    return fig

# --- 4. Stacked Bar: Sessions by utm_source and utm_content ---
def stacked_bar_sessions_by_source_content(website_sessions):
    grouped = website_sessions.groupby(['utm_source', 'utm_content'])['website_session_id'].nunique().reset_index()
    pivot_df = grouped.pivot(index='utm_source', columns='utm_content', values='website_session_id').fillna(0)

    fig = go.Figure()
    for content in pivot_df.columns:
        fig.add_trace(go.Bar(
            x=pivot_df.index,
            y=pivot_df[content],
            name=content
        ))
    fig.update_layout(
        barmode='stack',
        title='📊 Sessions by UTM Source and Content',
        xaxis_title='UTM Source',
        yaxis_title='Sessions',
        xaxis_tickangle=45,
        template='plotly_white'
    )
    return fig

# === 1. Line Chart: Total Orders by Year and Month ===
def line_chart_total_orders_over_time(order_data):
    order_data['year_month'] = pd.to_datetime(order_data['order_date']).dt.to_period('M').astype(str)
    orders_by_month = (
        order_data.groupby('year_month')['order_id']
        .nunique()
        .reset_index(name='total_orders')
    )

    fig = px.line(
        orders_by_month,
        x='year_month',
        y='total_orders',
        title='📈 Total Orders by Year and Month',
        markers=True
    )
    fig.update_layout(xaxis_title='Year-Month', yaxis_title='Total Orders', template='plotly_white')
    return fig

# === 2. Stacked Bar Chart: Conversion Rate by utm_source + utm_campaign ===
def stacked_bar_conversion_by_source_campaign(order_data, website_sessions):
    total_sessions = website_sessions.groupby(['utm_source', 'utm_campaign'])['website_session_id'].nunique().reset_index(name='total_sessions')
    total_orders = order_data.groupby(['utm_source', 'utm_campaign'])['order_id'].nunique().reset_index(name='total_orders')

    df = pd.merge(total_sessions, total_orders, on=['utm_source', 'utm_campaign'], how='left').fillna(0)
    df['conversion_rate_pct'] = (df['total_orders'] / df['total_sessions']) * 100

    fig = px.bar(
        df,
        x='utm_source',
        y='conversion_rate_pct',
        color='utm_campaign',
        title='📊 Conversion Rate % by UTM Source and Campaign',
        barmode='stack'
    )
    fig.update_layout(xaxis_title='UTM Source', yaxis_title='Conversion Rate (%)', template='plotly_white')
    return fig

# === 3. Stacked Bar Chart: Conversion Rate by utm_source + utm_content ===
def stacked_bar_conversion_by_source_content(order_data, website_sessions):
    total_sessions = website_sessions.groupby(['utm_source', 'utm_content'])['website_session_id'].nunique().reset_index(name='total_sessions')
    total_orders = order_data.groupby(['utm_source', 'utm_content'])['order_id'].nunique().reset_index(name='total_orders')

    df = pd.merge(total_sessions, total_orders, on=['utm_source', 'utm_content'], how='left').fillna(0)
    df['conversion_rate_pct'] = (df['total_orders'] / df['total_sessions']) * 100

    fig = px.bar(
        df,
        x='utm_source',
        y='conversion_rate_pct',
        color='utm_content',
        title='📊 Conversion Rate % by UTM Source and Content',
        barmode='stack'
    )
    fig.update_layout(xaxis_title='UTM Source', yaxis_title='Conversion Rate (%)', template='plotly_white')
    return fig

# === 4. Column Chart – Total Orders by session_path ===
def column_chart_orders_by_session_path(order_data, session_path_data, top_n=20):
    """
    Column chart: Total Orders by session path.
    """
    # Merge order data with session path data
    merged = order_data.merge(session_path_data, on="website_session_id", how="inner")

    # Clean/shorten long paths
    merged['path_short'] = merged['pageview_url'].apply(lambda x: x[:60] + '...' if len(x) > 60 else x)

    # Count total orders by path
    orders_by_path = (
        merged.groupby('path_short')['order_id']
        .nunique()
        .reset_index(name='total_orders')
        .sort_values(by='total_orders', ascending=False)
        .head(top_n)
    )

    # Plot
    fig = px.bar(
        orders_by_path,
        x='path_short',
        y='total_orders',
        text='total_orders',
        title='🛒 Total Orders by Session Path',
        labels={'path_short': 'Session Path', 'total_orders': 'Total Orders'}
    )

    fig.update_traces(marker_color='lightslategray', textposition='outside')
    fig.update_layout(
        xaxis_tickangle=45,
        margin=dict(t=60, b=200),
        height=500,
        template='plotly_white'
    )

    return fig

# 1. 📊 Gross Revenue & Orders Over Time by Product
def line_column_revenue_orders_by_product(order_data):
    df = order_data.copy()
    df['year_month'] = pd.to_datetime(df['order_date']).dt.to_period('M').astype(str)

    grouped = df.groupby(['year_month', 'product_name']).agg(
        gross_revenue=('price_usd', 'sum'),
        total_orders=('order_id', 'nunique')
    ).reset_index()

    fig = px.bar(
        grouped, x='year_month', y='gross_revenue', color='product_name',
        title='💰 Gross Revenue Over Time by Product',
        labels={'gross_revenue': 'Gross Revenue', 'year_month': 'Year-Month'},
    )

    fig2 = px.line(
        grouped, x='year_month', y='total_orders', color='product_name',
        labels={'total_orders': 'Total Orders'},
    )

    for trace in fig2.data:
        fig.add_trace(trace)

    fig.update_layout(barmode='stack', height=600, template='plotly_white')
    return fig

# 2. 🍩 Donut Chart – Total Units Sold
def donut_units_sold_by_product(order_data):
    df = order_data.groupby('product_name')['items_purchased'].sum().reset_index(name='units_sold')
    fig = px.pie(
        df,
        values='units_sold',
        names='product_name',
        hole=0.4,
        title='🧸 Units Sold by Product'
    )
    fig.update_traces(textinfo='percent+label')
    fig.update_layout(template='plotly_white')
    return fig

# 3. 🔁 Cross-Selling Matrix

'''
def matrix_cross_selling(order_data):
    if order_data.empty or 'order_id' not in order_data or 'product_name' not in order_data:
        st.warning("❗ Data is missing required columns or is empty.")
        return None

    # Step 1: Group by order_id and get all product_names in each order
    pairs_df = (
        order_data.groupby('order_id')['product_name']
        .apply(lambda x: list(set(x.dropna())))
        .reset_index()
    )

    pair_counts = {}

    # Step 2: Count combinations per order
    for products in pairs_df['product_name']:
        if len(products) > 1:
            for combo in combinations(sorted(products), 2):
                pair_counts[combo] = pair_counts.get(combo, 0) + 1

    # Step 3: Convert to DataFrame
    if not pair_counts:
        st.warning("No product pairs found for cross-selling.")
        return None

    matrix_df = pd.DataFrame([
        {'product_1': p1, 'product_2': p2, 'order_count': count}
        for (p1, p2), count in pair_counts.items()
    ])

    # Step 4: Pivot to matrix
    pivot = matrix_df.pivot(index='product_1', columns='product_2', values='order_count').fillna(0)

    # Step 5: Plot
    fig = px.imshow(
        pivot,
        labels=dict(color="Order Pair Count"),
        x=pivot.columns,
        y=pivot.index,
        color_continuous_scale='Blues',
        title='🔗 Cross-Selling Matrix (Product Pairs)'
    )
    fig.update_layout(height=600, template='plotly_white')
    return fig
'''

# 4. 📉 Total Refunds by Product
def bar_refunds_by_product(order_data):
    df = order_data[order_data['refund_amount_usd'].notna()]
    df = df.groupby('product_name')['refund_amount_usd'].sum().reset_index()

    fig = px.bar(
        df,
        x='product_name',
        y='refund_amount_usd',
        text='refund_amount_usd',
        title='🔁 Total Refunds by Product',
        labels={'refund_amount_usd': 'Refund Amount (USD)', 'product_name': 'Product'}
    )

    fig.update_traces(marker_color='lightcoral', textposition='outside')
    fig.update_layout(xaxis_tickangle=45, template='plotly_white')
    return fig

