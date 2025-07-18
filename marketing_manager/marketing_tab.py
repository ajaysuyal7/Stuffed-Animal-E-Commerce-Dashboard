import streamlit as st
import pandas as pd
from ceo.filter import apply_filter
from ceo.base_kpi import calculate_kpis
from data_loader import preprocess_session_path_data
from .visuals import (
    line_chart_conversion_rate_1,
    pie_chart_total_sessions_1,
    bar_chart_gross_revenue_1,
    channel_kpi_heatmap_plotly,
    line_column_avg_time_by_session_path,
    bounce_rate_stacked_column,
    bounce_rate_stacked_column_by_content,
    line_chart_total_sessions_over_time,
    clustered_bar_sessions_by_source_device,
    stacked_bar_sessions_by_source_campaign,
    stacked_bar_sessions_by_source_content,
    line_chart_total_orders_over_time,
    stacked_bar_conversion_by_source_campaign,
    stacked_bar_conversion_by_source_content,
    column_chart_orders_by_session_path,
    line_column_revenue_orders_by_product,
    donut_units_sold_by_product,
    bar_refunds_by_product
)

def render_marketing_dashboard(order_data,website_sessions,website_pageviews):
    st.title("📢 Marketing Director Dashboard")

    # Filters
    filters = apply_filter(order_data, website_pageviews, website_sessions)

    filtered_order_data = filters["order_data"]
    filtered_sessions = filters["sessions"]
    filtered_pageviews = filters["pageviews"]

    # KPIs
    kpis = calculate_kpis(filtered_order_data, filtered_sessions, filtered_pageviews)

    # Tabs
    tab1, tab2, tab3, tab4, tab5  = st.tabs([ "📈 Marketing Channel Performance", "📊 User Engagement", 
                                             "Traffic Source & Segment Trends",
                                             "Attribution & Conversion Journey",
                                             "Product Analysis"])

    with tab1:

        col1, col2, col3 = st.columns(3)
        col1.metric("🧾 Total Orders", f"{kpis['total_orders']:,}")
        col2.metric("💰 Gross Revenue", f"${kpis['gross_revenue']:,.0f}")
        col3.metric("📈 Gross Profit %", f"{kpis['gross_profit_pct']:.2f}%")
        
        st.subheader("Conversion Rate Over Time")
        line_chart_conversion_rate_1(filtered_order_data, filtered_sessions)

        col1,col2=st.columns(2)
        with col1:
            st.subheader("Total Sessions by UTM Source")
            pie_chart_total_sessions_1(filtered_sessions)

        with col2:
            st.subheader("Gross Revenue by UTM Source")
            bar_chart_gross_revenue_1(filtered_order_data)

        # chart 4    
        st.markdown("## 📈 Channel Sources Vs KPIs")
        channel_kpi_heatmap_plotly(filtered_order_data, filtered_sessions, filtered_pageviews)

    with tab2:
        col4, col5, col6 = st.columns(3)
        col4.metric("🎯 Conversion Rate", f"{kpis['conversion_rate_pct']:.2f}%")
        col5.metric("🕒 Avg. Session Duration (min)", f"{kpis['avg_user_session_duration_min']:.2f}")
        col6.metric("❌ Bounce Rate", f"{kpis['bounce_rate_pct']:.2f}%")
        
        # Precomputed once at app start
        st.markdown("## 📈 Line + Column Chart – Avg Session Time & Count of sessions by session_path")
        combined_paths_data = preprocess_session_path_data(filtered_pageviews)
        # Visual in page
        fig = line_column_avg_time_by_session_path(combined_paths_data)
        st.plotly_chart(fig, use_container_width=True)
        
    
        col1,col2=st.columns(2)
        with col1:
        # Chart 2
            st.markdown("## 📈 Stacked Column Chart – Bounce Rate % by utm_source and utm_campaign")
            pageviews_per_session = filtered_pageviews.groupby("website_session_id").size().reset_index(name="pageview_count")
            bounced = pageviews_per_session[pageviews_per_session["pageview_count"] == 1]["website_session_id"]
            fig1 = bounce_rate_stacked_column(filtered_sessions, bounced)
            st.plotly_chart(fig1, use_container_width=True)

        with col2:
            #chart 3
            st.markdown("## 📈 Stacked Column Chart – Bounce Rate % by utm_source and utm_content")
            pageviews_per_session = filtered_pageviews.groupby("website_session_id").size().reset_index(name="pageview_count")
            bounced = pageviews_per_session[pageviews_per_session["pageview_count"] == 1]["website_session_id"]
            fig2 = bounce_rate_stacked_column_by_content(filtered_sessions, bounced)
            st.plotly_chart(fig2, use_container_width=True)

    with tab3:
        st.title("📊 Traffic Source & Segment Trends")
        # Line Chart – Total Sessions by Year and Month

        col1,col2=st.columns(2)
        with col1:
            st.plotly_chart(line_chart_total_sessions_over_time(filtered_sessions), use_container_width=True)
        with col2:
            # Clustered Bar – Total Sessions by utm_source and device_type
            st.plotly_chart(clustered_bar_sessions_by_source_device(filtered_sessions), use_container_width=True)

        col3,col4=st.columns(2)
            # Stacked Bar – Sessions by utm_source and utm_campaign
        with col3:
            st.plotly_chart(stacked_bar_sessions_by_source_campaign(filtered_sessions), use_container_width=True)
        with col4:
            # Stacked Bar – Sessions by utm_source and utm_content
            st.plotly_chart(stacked_bar_sessions_by_source_content(filtered_sessions), use_container_width=True)

    with tab4:
        st.title("📊 Attribution & Conversion Journey")
        col1,col2=st.columns(2)
        with col1:
            fig1 = line_chart_total_orders_over_time(filtered_order_data)
            st.plotly_chart(fig1, use_container_width=True)
        with col2:
            fig2 = stacked_bar_conversion_by_source_campaign(filtered_order_data, filtered_sessions)
            st.plotly_chart(fig2, use_container_width=True)

        col3,col4=st.columns(2)
        with col3:
            fig3 = stacked_bar_conversion_by_source_content(filtered_order_data, filtered_sessions)
            st.plotly_chart(fig3, use_container_width=True)
        with col4:
            session_path_data = preprocess_session_path_data(website_pageviews)
            # Visual: Total Orders by Session Path
            fig4 = column_chart_orders_by_session_path(filtered_order_data, session_path_data)
            st.plotly_chart(fig4, use_container_width=True)

    with tab5:
        st.title("📦 Product Performance Dashboard")
        # Assume filtered_order_data is passed or available
        fig1 = line_column_revenue_orders_by_product(filtered_order_data)
        st.plotly_chart(fig1, use_container_width=True)

        fig2 = donut_units_sold_by_product(filtered_order_data)
        st.plotly_chart(fig2, use_container_width=True)

       
        fig3 = bar_refunds_by_product(filtered_order_data)
        st.plotly_chart(fig3, use_container_width=True)