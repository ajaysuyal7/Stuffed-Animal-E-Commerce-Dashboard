import streamlit as st
from ceo.filter import apply_filters
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


def render_ceo_dashboard(orders, order_items, refunds, products, pageviews, website_session):
    st.title("📊 CEO Dashboard")

    # ✅ Drop 'user_id' from sessions to avoid conflict
    sessions_clean = website_session.drop(columns=["user_id"], errors="ignore")
    # Merge relevant data
    df = orders.merge(sessions_clean, on="website_session_id", how="left") 
    # Filtered Data
    df = apply_filters(orders)

    # ----- Core Metrics ----- #
    gross_rev = df["price_usd"].sum()
    cogs = df["cogs_usd"].sum()
    refund_amt = refunds["refund_amount_usd"].sum()
    
    net_rev = gross_rev - refund_amt
    gross_profit = gross_rev - cogs
    net_profit = gross_profit - refund_amt

    total_orders = df["order_id"].nunique()
    total_sessions = website_session["website_session_id"].nunique()
    total_customers = df["user_id"].nunique()

    # ----- Session Metrics ----- #
    repeat_sessions = df[df["is_repeat_session"] == 1]["website_session_id"].nunique()
    repeat_session_rate = (repeat_sessions / total_sessions) * 100 if total_sessions else 0

    bounce_sessions = website_session[website_session["is_bounce"] == 1]["website_session_id"].nunique()
    total_web_sessions = website_session["website_session_id"].nunique()
    bounce_rate = (bounce_sessions / total_web_sessions) * 100 if total_web_sessions else 0

    conversion_rate = (total_orders / total_sessions) * 100 if total_sessions else 0

    # ----- Refund Metrics ----- #
    refunds_total = refunds["order_item_refund_id"].nunique()
    refund_amount = refunds["refund_amount_usd"].sum()

    # ----- Order Value ----- #
    avg_order_value = gross_rev / total_orders if total_orders else 0
   

    tab1, tab2, tab3 = st.tabs(["📊 Business Overview", "💰 Revenue & Profit", "📉 Engagement & Refunds"])

    with tab1:
        st.subheader("📊 Business Overview")
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("🧑‍🤝‍🧑 Total Customers", f"{total_customers:,}")
        k2.metric("🛒 Total Orders", f"{total_orders:,}")
        k3.metric("💵 Gross Revenue", f"${gross_rev:,.2f}")
        k4.metric("🌐 Total Sessions", f"{total_sessions:,}")

        col1,col2=st.columns(2)
        with col1:
        # CHART 1: Total Revenue by UTM Source
            st.subheader("📊 Total Revenue by UTM Source")
            utm_rev = df.groupby("utm_source")["price_usd"].sum().reset_index()
            fig1 = px.bar(utm_rev, x="utm_source", y="price_usd", text_auto=True)
            fig1.update_layout(yaxis_title="Revenue (USD)", xaxis_title="UTM Source")
            st.plotly_chart(fig1, use_container_width=True)

        # CHART 2: Total Users by Device Type
        with col2:
            st.subheader("📊 Total Users by Device Type")
            device_users = df.groupby("device_type")["user_id"].nunique().reset_index()
            fig2 = px.pie(device_users, names="device_type", values="user_id", hole=0.5)
            fig2.update_traces(textinfo="percent+label+value")
            st.plotly_chart(fig2, use_container_width=True)

        col3,col4=st.columns(2)

        with col3:
        # CHART 3: Orders by First vs Repeat
            st.subheader("📊 Orders by First vs Repeat")
            df["order_date"] = pd.to_datetime(df["order_date"], dayfirst=True, errors='coerce')
            first_orders = df.groupby("user_id")["order_date"].min().reset_index()
            first_orders.rename(columns={"order_date": "first_order_date"}, inplace=True)
            df = df.merge(first_orders, on="user_id", how="left")
            df["order_flag"] = df.apply(
                lambda row: "First Order" if row["order_date"] == row["first_order_date"] else "Repeat Order", axis=1
            )
            flag_counts = df["order_flag"].value_counts().reset_index()
            flag_counts.columns = ["Order Type", "Count"]
            fig3 = px.bar(flag_counts, x="Order Type", y="Count", text_auto=True)
            st.plotly_chart(fig3, use_container_width=True)

        with col4:
             # CHART 5: Sessions by UTM Source
            st.subheader("📊 Sessions by UTM Source")
            utm_sessions = df[df["utm_source"].notna()].groupby("utm_source")["website_session_id"].nunique().reset_index()
            fig4 = px.bar(utm_sessions, x="utm_source", y="website_session_id", text_auto=True)
            st.plotly_chart(fig4, use_container_width=True)


#Revenue & Profit Tab
    with tab2:
        st.subheader("💰 Revenue & Profitability")
        k5, k6, k7, k8 = st.columns(4)
        k5.metric("📈 Net Revenue", f"${net_rev:,.2f}")
        k6.metric("💰 Gross Profit", f"${gross_profit:,.2f}")
        k7.metric("💹 Net Profit", f"${net_profit:,.2f}")
        k8.metric("🧾 Average Order Value (AOV)", f"${avg_order_value:,.2f}")

        col5, col6 =st.columns(2)
        with col5:
            #Chart 6: Gross Revenue by Year & Month
            st.subheader("📈 Gross Revenue by Year & Month")
            df["year_month"] = pd.to_datetime(df["order_date"]).dt.to_period("M").astype(str)
            monthly_rev = df.groupby("year_month")["price_usd"].sum().reset_index()
            fig5 = px.area(monthly_rev, x="year_month", y="price_usd")
            fig5.update_traces(mode="lines+markers")
            st.plotly_chart(fig5, use_container_width=True)

        with col6:
            #Chart 6: Gross Revenue vs COGS by Year & Month
            st.subheader("📊 Gross Revenue vs COGS by Year & Month")
            # Group by Year-Month and calculate totals
            rev_cogs = df.groupby("year_month")[["price_usd", "cogs_usd"]].sum().reset_index()
            # Melt the data for easier plotting with labels
            rev_cogs_melted = rev_cogs.melt(id_vars="year_month", value_vars=["price_usd", "cogs_usd"],
                                            var_name="Metric", value_name="Amount")
            fig6 = px.line(rev_cogs_melted, x="year_month", y="Amount", color="Metric", markers=True)
            st.plotly_chart(fig6, use_container_width=True)

        #chart 7: Net revenue by Quater
        st.subheader("📈 Net Revenue by Quarter")
        df["year_quarter"] = pd.to_datetime(df["order_date"]).dt.to_period("Q").astype(str)
        revenue_quarter = df.groupby("year_quarter")["price_usd"].sum().reset_index()
        fig7 = px.area(revenue_quarter, x="year_quarter", y="price_usd", text="price_usd")
        fig7.update_traces(mode="lines+markers+text", textposition="top center")
        st.plotly_chart(fig7, use_container_width=True)

    # Engagement & refunds Tab
    with tab3:
        st.subheader("📉 Engagement & Refunds")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🔁 Total Refunds", f"{refunds_total:,}")
        c2.metric("🔁 Total Refunds", f"{refunds_total:,}")
        c3.metric("📥 Conversion Rate", f"{conversion_rate:.2f}%")
        c4.metric("📉 Bounce Rate", f"{bounce_rate:.2f}%")

        col9,col10=st.columns(2)
        with col9:
        # CHART 8: Bounce Count by UTM Source
            st.subheader("📉 Bounce Count by UTM Source")
            pv_count = pageviews.groupby("website_session_id").size().reset_index(name="pv_count")
            bounced_sessions = pv_count[pv_count["pv_count"] == 1]
            bounced_df = bounced_sessions.merge(website_session, on="website_session_id", how="left")
            bounce_group = bounced_df.groupby("utm_source")["website_session_id"].nunique().reset_index()
            fig9 = px.pie(bounce_group, names="utm_source", values="website_session_id", hole=0.5)
            fig9.update_traces(textinfo="percent+label+value")
            st.plotly_chart(fig9, use_container_width=True)

        with col10:
            # CHART 10: Total Refunds by Product Name
            st.subheader("📉 Total Refunds by Product Name")
            refund_details = refunds.merge(order_items, on="order_item_id", how="left") \
                                .merge(products, on="product_id", how="left")
            refund_prod = refund_details["product_name"].value_counts().reset_index()
            refund_prod.columns = ["product_name", "refund_count"]
            fig10 = px.area(refund_prod, x="product_name", y="refund_count", text="refund_count")
            fig10.update_traces(mode="lines+markers+text", textposition="top center")
            st.plotly_chart(fig10, use_container_width=True)


        # CHART 4: Funnel Stage Users
        stage_counts = website_session.groupby("funnel_stage")["user_id"].nunique().reset_index()

        # ✅ Sort funnel stages logically if needed (optional)
        stage_order = [
        "Landing Bounce", 
        "Dropped at Product", 
        "Dropped at Checkout", 
        "Dropped at Cart", 
        "Converted Session"
        ]
        stage_counts["funnel_stage"] = pd.Categorical(stage_counts["funnel_stage"], categories=stage_order, ordered=True)
        stage_counts = stage_counts.sort_values("funnel_stage")

        # ✅ Funnel chart with % and value
        st.subheader("📊 Distinct Users by Funnel Stage")
        fig11 = go.Figure(go.Funnel(
        y=stage_counts["funnel_stage"],
        x=stage_counts["user_id"],
        textinfo="value+percent initial"
        ))
        st.plotly_chart(fig11, use_container_width=True)

    st.balloons()

