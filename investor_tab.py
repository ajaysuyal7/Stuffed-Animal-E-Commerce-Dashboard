import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def human_format(num):
    if num >= 1_000_000:
        return f"{num/1_000_000:.2f}M"
    elif num >= 1_000:
        return f"{num/1_000:.2f}K"
    else:
        return str(num)

def render_investor_dashboard(website_sessions, orders, pageviews):
    st.title("📈 Investor Dashboard")

    # Preprocessing
    orders["order_date"] = pd.to_datetime(orders["order_date"])
    orders["year_month"] = orders["order_date"].dt.to_period("M").astype(str)
    orders["year_quarter"] = orders["order_date"].dt.to_period("Q").astype(str)
    sessions = website_sessions.copy()
    sessions["session_date"] = pd.to_datetime(sessions["session_created_at"])
    sessions["year_month"] = sessions["session_date"].dt.to_period("M").astype(str)
    avg_order_value = orders.groupby("user_id")["price_usd"].mean().mean()

    tab1, tab2, tab3 = st.tabs(["📊 Business Growth", "💰 Revenue Insights", "🌐 Traffic & Engagement"])

    # ---------------------- TAB 1 ----------------------
    with tab1:
        st.subheader("📌 Key Business KPIs")
        col1, col2, col3 = st.columns(3)
        col1.metric("🧾 Total Orders", human_format(orders['order_id'].nunique()))
        col2.metric("👥 Unique Customers", human_format(orders['user_id'].nunique()))
        col3.metric("📈 Active Months", human_format(orders['year_month'].nunique()))

        st.markdown("### 📊 Orders Trend Over Time")
        monthly_orders = orders.groupby("year_month")["order_id"].nunique().reset_index()
        fig1 = px.line(monthly_orders, x="year_month", y="order_id", title="Monthly Orders")
        st.plotly_chart(fig1, use_container_width=True)


        col4, col5 ,col6= st.columns(3)
        with col4:
            st.markdown("### 🔄 First vs Repeat Orders")
            first_orders = orders.groupby("user_id")["order_date"].min().reset_index()
            first_orders.rename(columns={"order_date": "first_order_date"}, inplace=True)
            orders = orders.merge(first_orders, on="user_id", how="left")
            orders["order_flag"] = orders.apply(
                lambda x: "First Order" if x["order_date"] == x["first_order_date"] else "Repeat Order", axis=1)
            flag_counts = orders["order_flag"].value_counts().reset_index()
            flag_counts.columns = ["Order Type", "Count"]
            fig2 = px.pie(flag_counts, names="Order Type", values="Count")
            st.plotly_chart(fig2, use_container_width=True)

        with col5:
            st.markdown("### 📱 Users by Device")
            device_users = sessions.groupby("device_type")["user_id"].nunique().reset_index()
            fig3 = px.pie(device_users, names="device_type", values="user_id", hole=0.4)
            st.plotly_chart(fig3, use_container_width=True)

        with col6:
            st.markdown("### 🔗 Orders by UTM Source")
            utm_orders = orders[orders["utm_source"].notna()].groupby("utm_source")["order_id"].nunique().reset_index()
            fig4 = px.bar(utm_orders, x="utm_source", y="order_id")
            st.plotly_chart(fig4, use_container_width=True)

    # ---------------------- TAB 2 ----------------------
    with tab2:
        st.subheader("📌 Revenue KPIs")
        col1, col2, col3,col4 = st.columns(4)
        col1.metric("💰 Gross Revenue", f"${human_format(orders['price_usd'].sum())}")
        col2.metric("💸 Net Revenue", f"${human_format((orders['price_usd'] - orders['cogs_usd']).sum())}")
        col3.metric("📊 Total COGS", f"${human_format(orders['cogs_usd'].sum())}")  
        col4.metric("Average Order Value", f"${avg_order_value:.2f}")

        st.markdown("### 📈 Gross Revenue Over Time")
        monthly_rev = orders.groupby("year_month")["price_usd"].sum().reset_index()
        fig5 = px.area(monthly_rev, x="year_month", y="price_usd")
        st.plotly_chart(fig5, use_container_width=True)


        col5, col6 = st.columns(2)
        with col5:
            st.markdown("### 💹 Net Revenue by Quarter")
            revenue_quarter = orders.groupby("year_quarter")["price_usd"].sum().reset_index()
            fig7 = px.bar(revenue_quarter, x="year_quarter", y="price_usd")
            st.plotly_chart(fig7, use_container_width=True)

        with col6:          
            st.markdown("### 📉 Gross Revenue vs COGS")
            rev_cogs = orders.groupby("year_month")[["price_usd", "cogs_usd"]].sum().reset_index()
            rev_cogs_melt = rev_cogs.melt(id_vars="year_month", value_vars=["price_usd", "cogs_usd"],
                                        var_name="Metric", value_name="Amount")
            fig6 = px.line(rev_cogs_melt, x="year_month", y="Amount", color="Metric", markers=True)
            st.plotly_chart(fig6, use_container_width=True)
            

    # ---------------------- TAB 3 ----------------------
    with tab3:
        st.subheader("📌 Traffic KPIs")
        col1, col2, col3 = st.columns(3)
        col1.metric("🌐 Total Sessions", human_format(sessions['website_session_id'].nunique()))
        col2.metric("📉 Bounce Sessions", human_format((pageviews.groupby('website_session_id').size() == 1).sum()))
        conversion_rate = (orders["user_id"].nunique() / sessions["user_id"].nunique()) * 100
        col3.metric("🔁 Conversion Rate", f"{conversion_rate:.2f}%")

        col4,col5=st.columns(2)

        with col4:
            st.markdown("### 📊 Sessions by UTM Source")
            utm_sessions = sessions[sessions["utm_source"].notna()].groupby("utm_source")["website_session_id"].nunique().reset_index()
            fig8 = px.bar(utm_sessions, x="utm_source", y="website_session_id")
            st.plotly_chart(fig8, use_container_width=True)

        with col5:
            st.markdown("### 📉 Funnel Stage Breakdown")
            stage_counts = sessions.groupby("funnel_stage")["user_id"].nunique().reset_index()
            stage_order = [
                "Landing Bounce", "Dropped at Product", "Dropped at Checkout", 
                "Dropped at Cart", "Converted Session"
            ]
            stage_counts["funnel_stage"] = pd.Categorical(stage_counts["funnel_stage"], categories=stage_order, ordered=True)
            stage_counts = stage_counts.sort_values("funnel_stage")
            fig9 = go.Figure(go.Funnel(
                y=stage_counts["funnel_stage"],
                x=stage_counts["user_id"],
                textinfo="value+percent initial"
            ))
            st.plotly_chart(fig9, use_container_width=True)

        st.markdown("### 📊 Sessions Over Time")
        monthly_sessions = sessions.groupby("year_month")["website_session_id"].nunique().reset_index()
        fig10 = px.line(monthly_sessions, x="year_month", y="website_session_id")
        st.plotly_chart(fig10, use_container_width=True)