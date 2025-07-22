import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def render_website_manager_dashboard(website_session, webpage_view,orders):
    #set up the Streamlit page configuration
    st.title("Website Manager Dashboard")
    if not website_session.empty:
        # Display the first few rows of the DataFrame
        website_session['utm_source'] = website_session['utm_source'].replace(['NULL', ''], 'Others')
        website_session['utm_source'] = website_session['utm_source'].fillna('Others')
        orders['utm_source']=orders['utm_source'].replace(['NULL',''],'Others')

        #prepare the data eith Dates
        website_session['session_created_at'] = pd.to_datetime(website_session['session_created_at'], errors='coerce')
        website_session['Year'] = website_session['session_created_at'].dt.year
        website_session['Month'] = website_session['session_created_at'].dt.month_name()
        website_session['Day'] = website_session['session_created_at'].dt.day_name()
        website_session['Quarter'] = website_session['session_created_at'].dt.quarter

        # ADD into slidbar Filters

        years= ["All"] + sorted(website_session['Year'].dropna().unique().tolist())  # this is include all the years in the data ans filter
        months= ["All"] + sorted(website_session['Month'].dropna().unique().tolist())
        days= ["All"] + sorted(website_session['Day'].dropna().unique().tolist())
        Device_type=["All"]+ website_session['device_type'].dropna().unique().tolist()
        utm_source= ["All"]+ website_session['utm_source'].dropna().unique().tolist()

        with st.sidebar:
            st.sidebar.subheader("Filters")
            Year= st.sidebar.radio("Year", options=years, index=0 )
            Month= st.sidebar.radio("Month", options=months, index=0)
            Day= st.sidebar.radio("Day", options=days, index=0)
            Device_type= st.sidebar.radio( "Device Type", options=Device_type, index=0)
            utm_source= st.sidebar.radio("Source", options=utm_source, index=0)
        
        # Filter tha Data

        filtered_website_session=website_session.copy()  
        if Year != "All":
            filtered_website_session = filtered_website_session[filtered_website_session['Year'] == Year]
        if Month != "All":
            filtered_website_session = filtered_website_session[filtered_website_session['Month'] == Month]
        if Day != "All":
            filtered_website_session = filtered_website_session[filtered_website_session['Day'] == Day]
        if Device_type != "All":
            filtered_website_session = filtered_website_session[filtered_website_session['device_type'] == Device_type]
        if utm_source != "All":
            filtered_website_session = filtered_website_session[filtered_website_session['utm_source'] == utm_source]
            # this is created to select the data based on the filters
        
        #

        def human_format(num):
            if num >= 1_000_000:
                return f"{num/1_000_000:.2f}M"
            elif num >= 1_000:
                return f"{num/1_000:.2f}K"
            else:
                return str(num)
    
       
# tabs are used to separate different visualizations
        tab1, tab2, tab3 = st.tabs(["website performance ", "Page Views Analysis", "Traffic Analysis"])
        # Tab 1: Website Performance Analysis
        with tab1:
            if filtered_website_session.empty:
                st.warning("No data matches your selected filters")
                st.stop()
            else:
                st.title("Website Performance Metrics")

                total_sessions = filtered_website_session['website_session_id'].nunique()
                total_users = filtered_website_session['user_id'].nunique()
                avg_duration = filtered_website_session['session_duration_MIN'].mean()
                bounce_rate = (filtered_website_session['total_pageviews']==1).mean() * 100 # % of sessions without an order(bounce rate)
                avg_page_views = filtered_website_session['total_pageviews'].mean()
                conversion_rate= (filtered_website_session['orders_in_session']>=1).mean() * 100 # % of session with order 

                # Prepare the Data for Visualization
                
                #chart 1 : bounce rate by quarter
                bounce_by_q=filtered_website_session.groupby('Quarter')['is_bounce'].mean().reset_index()
                bounce_by_q['bounce'] = bounce_by_q['is_bounce'] * 100  # Convert to percentage

                #chart2 : Device type duraction
                device_duration = filtered_website_session.groupby('device_type')['session_duration_MIN'].mean().reset_index()
                device_duration['session_duration_MIN'] = device_duration['session_duration_MIN'].round(1)

                #chart3: Returing Users vs unique Users
                
                user_visit = filtered_website_session.groupby('user_id')['website_session_id'].nunique()
                repeat_user= human_format(user_visit[user_visit > 1].size)
                unique_visitor=human_format(user_visit[user_visit == 1].size)
                
                #Visitor Count by Quarter and Repeat Session
                visitor_count=filtered_website_session.groupby(['Quarter','is_repeat_session'])['user_id'].nunique().reset_index(name='visitor_count')
                visitor_count['visitor_type'] = visitor_count['is_repeat_session'].map({0: 'Unique Visitor', 1: 'Returning Visitor'})

                # Analyze the Data
                col1, col2, col3, col4, col5 = st.columns(5)

                
                col1.metric("Total Users", human_format(total_users)if pd.notnull(total_users) else "N/A")
                col2.metric("Avg. Session Duration (min)", round(avg_duration) if pd.notnull(avg_duration) else "N/A")
                col3.metric("Bounce Rate (%)", f"{round(bounce_rate, 2)}%"if pd.notnull(bounce_rate) else "N/A")
                col4.metric("Unique Visitor", unique_visitor if pd.notnull(unique_visitor) else "N/A")
                col5.metric("Returning Visitor ", repeat_user if pd.notnull(repeat_user) else "N/A")

                col8, col9 = st.columns(2)

                # Bounce Rate by Quarter
                with col8:
                    #st.markdown("### Bounce Rate by Quarter")
                    fig=px.line(bounce_by_q,x='Quarter', y='is_bounce', title='Bounce Rate by Quarter'
                                , labels={'is_bounce': 'Bounce Rate (%)', 'Quarter': 'Quarter'},
                                markers=True,text='bounce')
                    fig.update_traces(texttemplate='%{text:.2f}%', textposition='top center')
                    fig.update_layout(yaxis_title='Bounce Rate (%)')
                    st.plotly_chart(fig, use_container_width=True)

                # Device Type Session Duration   
                with col9:
                    fig2 = px.pie(device_duration, names='device_type', values='session_duration_MIN',
                                    title='Average Session Duration by Device',hole=0.5)
                    fig2.update_traces(textinfo='percent+label')
                    st.plotly_chart(fig2, use_container_width=True)
                                    

                col10,col11 = st.columns(2)

                # Returning Users vs Unique Users
                with col10:

                    fig3 = px.line(visitor_count, x='Quarter', y='visitor_count', color='visitor_type',
                                    markers=True, title='Visitor Count by Quarter and Repeat Session')
                    fig3.update_layout(yaxis_title='Visitor Count', xaxis_title='Quarter')
                    st.plotly_chart(fig3, use_container_width=True)

                # Session Count by Quarter and Source
                with col11:
                    source_by_quarter = filtered_website_session.groupby(['Quarter', 'utm_source'])['website_session_id'].nunique().reset_index(name='session_count')
                    fig4 = px.bar(source_by_quarter, x='Quarter', y='session_count', color='utm_source',
                                    title='Session Count by Quarter and Source', barmode='group')
                    fig4.update_layout(yaxis_title='Session Count', xaxis_title='Quarter',legend_title='Traffic Source')
                    st.plotly_chart(fig4, use_container_width=True)
                    
            # Tab 2: Page Views Analysis
        with tab2:
            if filtered_website_session.empty:
                st.warning("No data matches your selected filters")
                st.stop()
            else:

                st.subheader("Page Views Analysis")
                
                # Convert 'viewed_at' to datetime
                webpage_view['created_at'] = pd.to_datetime(webpage_view['created_at'], errors='coerce')

                # Filter the webpage_view DataFrame based on the filtered_website_session
                filtered_pageview= webpage_view[
                    webpage_view['website_session_id'].isin(filtered_website_session['website_session_id'])
                ]


                col1,col2,col3,col4 = st.columns(4)

                col1.metric("Total Page Views", human_format(filtered_pageview['website_pageview_id'].nunique()))
                col2.metric("Unique Page Views", human_format(filtered_pageview['website_session_id'].nunique()))
                #col3.metric("conversion")
                col3.metric("conversion Rate (%)", f"{round(conversion_rate,2)}%")
                col4.metric("Avg. page views ", round(avg_page_views)if pd.notnull(avg_page_views) else "N/A")

                col7,col8 = st.columns(2)

                #first page visit ("bar chart")

                first_page_visit = (filtered_pageview.sort_values(by=['website_session_id', 'created_at'])
                .groupby('website_session_id').first().reset_index())

                top_first_page= first_page_visit['pageview_url'].value_counts().reset_index()
                top_first_page.columns = ['pageview_url', 'visit_count']
                
                # Top First Page Visits
                with col7:
                    fig5 = px.bar(top_first_page.sort_values('visit_count',ascending=True), y='pageview_url', x='visit_count',
                                    orientation='h',title='Top First Page Visits', text='visit_count')
                    fig5.update_layout(xaxis_title='Page URL', yaxis_title='Visit Count')
                    fig5.update_traces(texttemplate='%{text}', textposition='outside')
                    st.plotly_chart(fig5, use_container_width=True)

                with col8:
                        # Bounce Rate by pageview
                    merged_data = filtered_pageview.merge(filtered_website_session[['website_session_id', 'is_bounce']],
                                                        on='website_session_id', how='left')
                    bounce_by_page= merged_data.groupby('pageview_url')['is_bounce'].mean().reset_index()
                    bounce_by_page['is_bounce'] = bounce_by_page['is_bounce'] * 100
                    bounce_by_page = bounce_by_page[bounce_by_page['is_bounce'] != 0]  # Filter out zero bounce rates
                    bounce_by_page = bounce_by_page.sort_values('is_bounce', ascending=True)
                    # Create a horizontal bar chart for bounce rate by page view
                    fig6 = px.bar(bounce_by_page, y='pageview_url', x='is_bounce',
                                    orientation='h', title='Bounce Rate by Page View', text='is_bounce')
                    fig6.update_layout(xaxis_title='Page URL', yaxis_title='Bounce Rate (%)')
                    fig6.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
                    st.plotly_chart(fig6, use_container_width=True)

                col9, col10 = st.columns(2)

                with col9:
                    #Bounce rate by utm_source
                    bounce_by_source = round(filtered_website_session.groupby('utm_source')['is_bounce'].mean(),4).reset_index()
                    bounce_by_source['is_bounce'] = round(bounce_by_source['is_bounce'] * 100,2)
                    bounce_by_source = bounce_by_source[bounce_by_source['is_bounce'] != 0]

                    #plotting the bounce rate by source
                    fig7 = px.pie(bounce_by_source, names='utm_source', values='is_bounce',title='Bounce Rate by Source',
                                    labels={'is_bounce': 'Bounce Rate (%)', 'utm_source': 'Source'},
                                    color_discrete_sequence=px.colors.qualitative.Pastel)
                    fig7.update_traces(textinfo='percent+label')
                    st.plotly_chart(fig7, use_container_width=True)
                
                with col10:
                    # Total website session by pageview URL
                    total_sessions_by_page = filtered_pageview.groupby('pageview_url')['website_session_id'].nunique().reset_index()
                    total_sessions_by_page.columns = ['pageview_url', 'total_sessions']
                    total_sessions_by_page = total_sessions_by_page.sort_values('total_sessions', ascending=True)
                    # Create a horizontal bar chart for total sessions by page view
                    fig8 = px.bar(total_sessions_by_page, y='pageview_url', x='total_sessions',
                                    orientation='h', title='Total Sessions by Page View', text='total_sessions')
                    fig8.update_layout(xaxis_title='Page URL', yaxis_title='Total Sessions')
                    fig8.update_traces(texttemplate='%{text}', textposition='outside')
                    st.plotly_chart(fig8, use_container_width=True)

        with tab3:
            if filtered_website_session.empty:
                st.warning("No data matches your selected filters")
                st.stop()
            else:
                st.title("Traffic Dashboard")

                filtered_orders = orders[orders['website_session_id'].isin(filtered_website_session['website_session_id'])]


                col1,col2,col3,col4,col5=st.columns(5)

                col1.metric("Total Session",human_format(total_sessions))
                col2.metric("Gsearch Session", human_format(filtered_website_session[filtered_website_session['utm_source']=='gsearch']['website_session_id'].nunique()))
                col3.metric("Bsearch Sessions", human_format(filtered_website_session[filtered_website_session['utm_source']=='bsearch']['website_session_id'].nunique()))
                col4.metric("Gsearch Orders", human_format(filtered_orders[filtered_orders['utm_source']=='gsearch']['order_id'].nunique()))
                col5.metric("Bsearch Orders", f"{filtered_orders[filtered_orders['utm_source']=='bsearch']['order_id'].nunique():,}")

                # charts
                sd=filtered_website_session.groupby(['utm_source','device_type'])['website_session_id'].nunique().reset_index()
                
                ch1,ch2=st.columns(2)
                
                with ch1:
                    fi1=px.bar(sd, x='utm_source', y='website_session_id', color='device_type', barmode='group', title="Sessions by Source & Device")
                    st.plotly_chart(fi1, use_container_width=True)

                with ch2:

                    crs = filtered_orders.groupby('utm_source')['order_id'].nunique() / filtered_website_session.groupby('utm_source')['website_session_id'].nunique()
                    crs_df=crs.reset_index(name='conversion_rate')
                    fi2 = px.bar(crs_df, x='utm_source', y='conversion_rate', text='conversion_rate', title="Conversion Rate by Source")
                    fi2.update_traces(texttemplate='%{text:.1%}', textposition='outside')
                    fi2.update_yaxes(tickformat='%')
                    st.plotly_chart(fi2, use_container_width=True)

                ch3,ch4=st.columns(2)

                with ch3:
                    sess_ct = filtered_website_session['utm_source'].value_counts()
                    ord_ct = filtered_orders.groupby('utm_source')['order_id'].nunique()
                    compare = pd.DataFrame({'Sessions': sess_ct, 'Orders': ord_ct}).reset_index().rename(columns={'index':'utm_source'})
                    compare = compare.sort_values(by='Sessions', ascending=False)
                    fi3 = px.bar(compare, x='utm_source', y=['Sessions','Orders'], barmode='group', title="Sessions vs Orders by Source")
                    st.plotly_chart(fi3, use_container_width=True)

                with ch4:
                    st.subheader("📊 Distinct Users by Funnel Stage")
                    stage_order = [
                    "Landing Bounce", 
                    "Dropped at Product", 
                    "Dropped at Checkout", 
                    "Dropped at Cart", 
                    "Converted Session"]

                    stage_counts = filtered_website_session.groupby("funnel_stage")["user_id"].nunique().reset_index()
                    stage_counts["funnel_stage"] = pd.Categorical(stage_counts["funnel_stage"], categories=stage_order, ordered=True)
                    stage_counts = stage_counts.sort_values("funnel_stage")

                    fi4 = go.Figure(go.Funnel(
                    y=stage_counts["funnel_stage"],
                    x=stage_counts["user_id"],
                    textinfo="value+percent initial"
                    ))
                    st.plotly_chart(fi4, use_container_width=True)

    else:
        st.warning("No data found")
        st.stop()