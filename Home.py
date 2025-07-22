import streamlit as st

def show_home():
    st.title("🧸 Stuffed Animal E-Commerce Dashboard")
    st.markdown("## 📊 Business Overview")

    # === Business Context ===
    st.markdown("""
    <div style="font-size: 18px; line-height: 1.6">
    🚀 <b>Business Context</b>:<br>
    An <b>e-commerce startup</b> specializing in <i>stuffed animal toys</i>. Operating for <b>3 years</b>, the company is now preparing for the next round of funding.<br><br>
    <b>Cindy Sharp (CEO)</b> seeks <b>data-driven insights</b> for her investor pitch. The analytics team is tasked with developing dashboards tailored for different stakeholders:
    <ul>
    <li><b>CEO:</b> Strategic growth & revenue</li>
    <li><b>Website Manager:</b> Conversion paths & session behavior</li>
    <li><b>Marketing Director:</b> Campaign & UTM performance</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)

    # === Stakeholders ===
    st.markdown("### 👥 Stakeholders")
    st.markdown("""
    - 👩‍💼 **Cindy Sharp** – CEO  
    - 👨‍💻 **Morgan Rockwell** – Website Manager  
    - 📣 **Tom Parmesan** – Marketing Director  
    """)
    st.markdown("----")
    st.markdown("""
    **Team Members:**
    - Ramya P
    - Ajay Suyal
    - Agasteen
    - Deepika

    **Sections Covered:**
    - CEO Dashboard
    - Website Manager Dashboard
    - Marketing Director
    - Investor Dashboard
    """)
