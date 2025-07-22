import streamlit as st
import pandas as pd



def calculate_kpis(order_data, website_sessions, website_pageviews):
    kpis = {}

    # === 1. TRAFFIC & USER BEHAVIOR KPIs ===
    try:
        kpis["total_sessions"] = website_sessions["website_session_id"].nunique()
        kpis["total_users"] = website_sessions["user_id"].nunique()
        kpis["sessions_per_user"] = round(kpis["total_sessions"] / kpis["total_users"], 2)
    except ZeroDivisionError:
        st.warning("⚠️ Cannot calculate sessions per user due to zero users.")
        kpis["sessions_per_user"] = 0

    try:
        kpis["total_buyers"] = order_data["user_id"].nunique()
        kpis["sessions_per_buyer"] =round(kpis["total_sessions"] / kpis["total_buyers"], 2)
    except ZeroDivisionError:
        st.warning("⚠️ Cannot calculate sessions per buyer due to zero buyers.")
        kpis["sessions_per_buyer"] = 0

    try:
        repeat_sessions = website_sessions[website_sessions["is_repeat_session"] == 1]["website_session_id"].nunique()
        kpis["repeat_session_rate_pct"] = round((repeat_sessions / kpis["total_sessions"]) * 100, 2)
    except ZeroDivisionError:
        st.warning("⚠️ Cannot calculate repeat session rate due to zero total sessions.")
        kpis["repeat_session_rate_pct"] = 0

    # === 2. SALES & FINANCIAL KPIs ===
    kpis["total_orders"] = order_data["order_id"].nunique()
    kpis["total_units_sold"] =order_data["items_purchased"].sum()
    kpis["total_refunds"] = (order_data["refund_amount_usd"]!=0).sum()

    gross_revenue = order_data["price_usd"].sum()
    total_cogs = order_data["cogs_usd"].sum()
    total_refund_amt = order_data["refund_amount_usd"].fillna(0).sum()

    net_revenue = gross_revenue - total_refund_amt
    gross_profit = net_revenue - total_cogs

    kpis["gross_revenue"] = round(gross_revenue, 2)
    kpis["total_cogs"] = round(total_cogs, 2)
    kpis["total_refund_amt"] = round(total_refund_amt, 2)
    kpis["net_revenue"] = round(net_revenue, 2)
    kpis["gross_profit"] = round(gross_profit, 2)

    try:
        kpis["gross_profit_pct"] = (round((gross_profit / net_revenue) * 100, 2))
    except ZeroDivisionError:
        st.warning("⚠️ Cannot calculate gross profit % due to zero net revenue.")
        kpis["gross_profit_pct"] = 0

    try:
        kpis["refund_rate_pct"] =(round((kpis["total_refunds"] / gross_revenue) * 100, 2))
    except ZeroDivisionError:
        st.warning("⚠️ Cannot calculate refund rate % due to zero gross revenue.")
        kpis["refund_rate_pct"] = 0

    # === 3. CONVERSION KPIs ===
    try:
        converted_sessions = order_data["website_session_id"].nunique()
        kpis["converted_sessions"] = (converted_sessions)
        kpis["conversion_rate_pct"] =round((converted_sessions / kpis["total_sessions"]) * 100, 2)
    except ZeroDivisionError:
        st.warning("⚠️ Cannot calculate conversion rate due to zero total sessions.")
        kpis["conversion_rate_pct"] = 0

    # Revenue per channel (drop nulls safely)
    try:
        revenue_per_channel = (
            order_data[order_data["utm_source"].notna() & (order_data["utm_source"].str.upper() != 'NULL')]
            .groupby("utm_source")["price_usd"]
            .sum()
            .reset_index()
            .rename(columns={"price_usd": "gross_revenue"})
            .sort_values(by="gross_revenue", ascending=False)
            .reset_index(drop=True)
        )
        kpis["revenue_per_channel"] = (revenue_per_channel)
    except Exception as e:
        st.warning(f"⚠️ Error calculating revenue per channel: {e}")
        kpis["revenue_per_channel"] = pd.DataFrame()

    # === 4. SESSION TIME METRICS ===
    try:
        pageviews = website_pageviews.copy()
        pageviews["created_at"] = pd.to_datetime(pageviews["created_at"])

        session_duration = (
            pageviews.groupby("website_session_id")["created_at"]
            .agg(session_start="min", session_end="max")
            .reset_index()
        )
        session_duration["session_duration_min"] = (
            (session_duration["session_end"] - session_duration["session_start"]).dt.total_seconds() / 60
        )

        kpis["avg_user_session_duration_min"] = (round(session_duration["session_duration_min"].mean(), 2))

        session_with_orders = order_data[["website_session_id"]].drop_duplicates()
        sessions_with_orders_durations = session_duration[
            session_duration["website_session_id"].isin(session_with_orders["website_session_id"])
        ]
        kpis["avg_buyer_session_duration_min"] = (round(
            sessions_with_orders_durations["session_duration_min"].mean(), 2
        ))
    except Exception as e:
        st.warning(f"⚠️ Could not calculate session durations: {e}")
        kpis["avg_user_session_duration_min"] = 0
        kpis["avg_buyer_session_duration_min"] = 0

    # === 5. BOUNCE RATE ===
    try:
        pageviews_per_session = (
            website_pageviews.groupby("website_session_id").size().reset_index(name="pageview_count")
        )
        bounced_sessions = pageviews_per_session[pageviews_per_session["pageview_count"] == 1][
            "website_session_id"
        ].nunique()
        kpis["bounce_rate_pct"] = (round((bounced_sessions / kpis["total_sessions"]) * 100, 2))
    except ZeroDivisionError:
        st.warning("⚠️ Cannot calculate bounce rate due to zero total sessions.")
        kpis["bounce_rate_pct"] = 0
    except Exception as e:
        st.warning(f"⚠️ Error calculating bounce rate: {e}")
        kpis["bounce_rate_pct"] = 0

    return kpis
