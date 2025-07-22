
from data_loader import load_all_data
from ceo.ceo_tab import render_ceo_dashboard
from website_manager_tab import render_website_manager_dashboard
from investor_tab import render_investor_dashboard
from marketing_manager.marketing_tab import render_marketing_dashboard
from Login import login
from Home import show_home
import streamlit as st


# 💡 GLOBAL BACKGROUND IMAGE
st.markdown(
    """
    <style>
    .stApp {
        background-image: url("Data\background.png");  /* replace with your image URL */
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# laod Data
orders, order_items, refunds, products, web_pageview, website_session, customers = load_all_data()

# Store data with original names (no renaming in session_state)
st.session_state.website_sessions = website_session
st.session_state.web_pageview = web_pageview
st.session_state.orders = orders
st.session_state.order_items = order_items
st.session_state.products = products
st.session_state.customers = customers
st.session_state.refunds = refunds


# Set up the Streamlit page configuration

def rerun_app():
     raise st.script_runner.RerunException(st.script_request_queue.RerunData(None))

def main():
    #st.set_page_config(page_title="Analytics Dashboard", layout="wide")
    
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        login()
        st.stop()  # avoid rerun errors 

    else:
        with st.sidebar:
            st.markdown(f"👤 Logged in as: **{st.session_state.get('username', 'User')}**")
            if st.button("Logout"):
                st.session_state.clear()
                st.success("Logged out. Please reload to log in again.")
                st.stop()

        #Navigation
        menu = st.sidebar.selectbox("Go to", ["Home", "CEO Dashboard", "Marketing Director", "Website Manager", "Investor Dashboard"])
        if menu == "Home":
            show_home()
        elif menu == "CEO Dashboard":
            render_ceo_dashboard(orders,order_items,refunds,products,web_pageview,website_session)
        elif menu=="Marketing Director":
            render_marketing_dashboard(orders,website_session,web_pageview)
        elif menu == "Website Manager":
            render_website_manager_dashboard(website_session,web_pageview,orders)
        elif menu == "Investor Dashboard":
            render_investor_dashboard(website_session,orders,web_pageview)
            

if __name__ == "__main__":
    main()