import streamlit as st
import plost
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from functions.filters import date_filter, filter_data
from functions.query import query_results

# Set page configuration
st.set_page_config(
    layout="wide",   # Set the layout to wide
    initial_sidebar_state="expanded",  # Optionally expand the sidebar initially
)

st.title('Account Overview Report')
billing_data, d = date_filter(destination="BigQuery")

## Only generate the tiles if date range is populated
if d is not None and len(d) == 2:
    start_date, end_date = d
    if start_date is not None:

        ## Filter data based on filters applied
        data_date_filtered = filter_data(start=start_date, end=end_date, data_ref=billing_data)

        # Convert 'created_at' column to datetime if it's not already in datetime format
        data_date_filtered['created_at'] = pd.to_datetime(data_date_filtered['created_at'])

        #####################################################################################
        # Group by month and calculate total revenue

        data_date_filtered['month'] = data_date_filtered['created_at'].dt.strftime('%Y-%m')
        revenue_by_month = data_date_filtered.groupby('month')['total_amount'].sum().reset_index()

        # Ensure all months are represented
        all_months = pd.date_range(start=revenue_by_month['month'].min(), end=revenue_by_month['month'].max(), freq='MS').strftime('%Y-%m')
        revenue_by_month = revenue_by_month.set_index('month').reindex(all_months, fill_value=0).reset_index()

        # Calculate average total revenue
        average_revenue = revenue_by_month['total_amount'].mean()

        # Rename columns and format total revenue as currency
        revenue_by_month = revenue_by_month.rename(columns={'index': 'period', 'total_amount': 'total revenue'})

        #####################################################################################
        # Calculate total revenue, monthly average revenue, and daily average revenue
        total_revenue = data_date_filtered['total_amount'].sum()
        monthly_avg_revenue = revenue_by_month['total revenue'].mean()
        daily_avg_revenue = total_revenue / ((end_date - start_date).days + 1)

        # Filter only recurring subscription revenue and handle NaT values
        subscription_data = data_date_filtered[data_date_filtered['subscription_id'].notnull()]
        subscription_data['month'] = subscription_data['created_at'].dt.strftime('%Y-%m')
        subscription_data = subscription_data.dropna(subset=['created_at'])  # Drop rows with NaT in created_at

        # Ensure there are valid dates to calculate start and end
        if subscription_data.empty:
            st.error("No valid data available.")
        else:
            # Generate a complete range of months
            all_months = pd.date_range(start=subscription_data['created_at'].min(), end=subscription_data['created_at'].max(), freq='MS').strftime('%Y-%m')

            # Group by month and sum the total_amount
            subscription_data['month'] = subscription_data['created_at'].dt.strftime('%Y-%m')
            monthly_rev = subscription_data.groupby('month')['total_amount'].sum().reindex(all_months, fill_value=0).reset_index()
            monthly_rev = monthly_rev.rename(columns={'index': 'period', 'total_amount': 'MRR'})

        st.subheader('Current Period Revenue Metrics')
        # Display KPI tiles next to each other
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(label="Total Revenue", value=f"${total_revenue:,.0f}")

        with col2:
            st.metric(label="Monthly Average Revenue", value=f"${monthly_avg_revenue:,.0f}")

        with col3:
            st.metric(label="Daily Average Revenue", value=f"${daily_avg_revenue:,.0f}")

        with col4:
            # # Display current MRR (last month in the dataset)
            # Check if data is available
            if len(monthly_rev) > 0:
                # Get current MRR if data is available
                current_mrr = monthly_rev['MRR'].iloc[0]
                st.metric(label="Current MRR", value=f"${current_mrr:,.0f}")
            else:
                # Handle case where no data is available
                st.metric(label="Current MRR", value=f"${0:,.0f}")

        col5, col6, col7, col8 = st.columns(4)
        data_date_filtered['discount_amount'].fillna(0, inplace=True)
        data_date_filtered['refund_amount'].fillna(0, inplace=True)
        data_date_filtered['subscription_id'].fillna(0, inplace=True)
        # Calculate KPI metrics
        discounts_total = data_date_filtered['discount_amount'].sum()

        discounts_average = data_date_filtered['discount_amount'].mean()

        refunds_total = data_date_filtered['refund_amount'].sum()
        refunds_average = data_date_filtered['refund_amount'].mean()

        with col5:
            st.metric(label="Total Discounts", value=f"${discounts_total:,.0f}")
        with col6:
            st.metric(label="Average Discount", value=f"${discounts_average:,.0f}")
        with col7:
            st.metric(label="Total Refunds", value=f"${refunds_total:,.0f}")
        with col8:
            st.metric(label="Average Refund", value=f"${refunds_average:,.0f}")

        #####################################################################################

        col1, col2 = st.columns(2)

        # Plot revenue by month as a bar chart
        fig = px.bar(
            revenue_by_month,
            x="period",
            y="total revenue",
            color_discrete_sequence=["#1f77b4"],
            text="total revenue",  # Display the total revenue value on each bar
        )

        # Adjust layout to display each month on the x-axis
        fig.update_xaxes(type='category')

        # Update hover mode and text formatting
        fig.update_traces(
            hovertemplate='<b>%{x}</b><br>Total Revenue: $%{y:,.0f}',
            texttemplate='%{y:,.0f}',
            textposition='outside'
        )
        
        monthly_revenue = fig.update_layout(
            xaxis_title="Month",
            yaxis_title="Total Revenue ($)",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            title='Monthly Revenue',
            showlegend=False,  # Hide legend if not needed
        )
        #####################################################################################

        # Plot MRR trend over time as an area chart
        fig = px.area(
            monthly_rev,
            x='period',
            y='MRR',
            labels={'period': 'Month', 'MRR': 'MRR ($)'},
            template='plotly_white'
        )

        # Customize the appearance of the graph
        fig.update_traces(
            line=dict(width=2.5),
            hovertemplate='<b>%{x}</b><br>MRR: $%{y:,.0f}',
            mode='lines',
            fillcolor=px.colors.sequential.Blues[2],  # Change fill color based on MRR values
            marker=dict(color=monthly_rev['MRR'], coloraxis='coloraxis')
        )

        # Add annotations (text labels) to show MRR values on the chart
        for i, row in monthly_rev.iterrows():
            fig.add_annotation(
                x=row['period'],
                y=row['MRR'],
                text=f"${row['MRR']:,.0f}",
                font=dict(color='black', size=10),
                showarrow=True,
                arrowhead=0,
                ax=0,
                ay=-40
            )

        # Define color scale for MRR values
        color_scale = px.colors.sequential.Blues[::-1]  # Reverse color scale for better visibility

        # Update layout with color axis for better color representation
        mrr_report = fig.update_layout(
            coloraxis=dict(
                cmin=monthly_rev['MRR'].min(),
                cmax=monthly_rev['MRR'].max(),
                colorscale=color_scale,
                colorbar=dict(title='MRR ($)')
            ),
            title='Monthly Recurring Revenue (MRR) Trend'
        )

        with col1:
            st.plotly_chart(monthly_revenue,use_container_width=True)
        with col2: 
            st.plotly_chart(mrr_report, use_container_width=True)

        #####################################################################################
        st.divider()
        st.subheader('Subscription Metrics')
        col9, col10, col11, col12 = st.columns(4)
        # Calculate KPI metrics
        subscriptions_total = data_date_filtered['subscription_id'].nunique()

        # Filter the DataFrame for 'paid' header_status
        paid_payments = data_date_filtered[data_date_filtered['header_status'].isin(['paid', 'completed'])]

        # Count unique header_id values for paid payments
        payments_total = paid_payments['total_amount'].mean()  # Calculate average subscription amount

        # Convert date columns to datetime format
        data_date_filtered['subscription_period_ended_at'] = pd.to_datetime(data_date_filtered['subscription_period_ended_at'], utc=True)
        data_date_filtered['created_at'] = pd.to_datetime(data_date_filtered['created_at'], utc=True)

        # Step 1: Get the maximum created_at date in data_date_filtered
        max_created_at = data_date_filtered['created_at'].max()

        # Step 2: Filter active subscriptions
        active_subscriptions = data_date_filtered[data_date_filtered['subscription_period_ended_at'] > max_created_at]

        # Step 3: Count unique subscription_id for active subscriptions
        active_subscriptions_count = active_subscriptions['subscription_id'].nunique()

        # Step 4: Filter canceled subscriptions
        canceled_subscriptions = data_date_filtered[(data_date_filtered['subscription_period_ended_at'].notnull()) & 
                                                    (data_date_filtered['subscription_period_ended_at'] <= max_created_at)]

        # Step 5: Count unique subscription_id for canceled subscriptions
        canceled_subscriptions_count = canceled_subscriptions['subscription_id'].nunique()

        # Display KPI metrics using Streamlit columns
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(label="Total Subscriptions", value=f"{subscriptions_total:,.0f}")

        with col2:
            st.metric(label="Current Active Subscriptions", value=f"{active_subscriptions_count:,.0f}")

        with col3:
            st.metric(label="Canceled/Expired Subscriptions", value=f"{canceled_subscriptions_count:,.0f}")

        with col4:
            st.metric(label="Average Subscription Amount", value=f"${payments_total:,.2f}")


        # Convert date columns to datetime format and ensure they are timezone-naive
        data_date_filtered['subscription_period_started_at'] = pd.to_datetime(data_date_filtered['subscription_period_started_at']).dt.tz_localize(None)
        data_date_filtered['subscription_period_ended_at'] = pd.to_datetime(data_date_filtered['subscription_period_ended_at']).dt.tz_localize(None)
        data_date_filtered['created_at'] = pd.to_datetime(data_date_filtered['created_at']).dt.tz_localize(None)

        # Step 1: Extract month from created_at to use as date_month and convert to string
        data_date_filtered['date_month'] = data_date_filtered['created_at'].dt.to_period('M').astype(str)

        # Step 2: Calculate active subscriptions over time
        def calculate_active_subscriptions(row):
            start_of_month = row['created_at'].replace(day=1)
            end_of_month = start_of_month + pd.offsets.MonthEnd(0)
            
            # Check if subscription started before end of month and ended after start of month
            if pd.isnull(row['subscription_period_ended_at']):
                return True  # Active if no end date (open-ended)
            else:
                return (row['subscription_period_started_at'] <= end_of_month) & (row['subscription_period_ended_at'] >= start_of_month)

        data_date_filtered['active_subscription'] = data_date_filtered.apply(calculate_active_subscriptions, axis=1)
        data_date_filtered['active_subscription'] = data_date_filtered['active_subscription'].astype(int)

        # Step 3: Group by month and count active subscriptions (unique subscriptions)
        monthly_active_subscriptions = data_date_filtered.groupby('date_month')['subscription_id'].nunique().reset_index()
        monthly_active_subscriptions.rename(columns={'date_month': 'Month', 'subscription_id': 'Active Subscriptions'}, inplace=True)

        # Step 4: Create a complete date range from min to max date
        min_date = data_date_filtered['created_at'].min().to_period('M')
        max_date = data_date_filtered['created_at'].max().to_period('M')
        date_range = pd.period_range(start=min_date, end=max_date, freq='M').astype(str)

        # Step 5: Merge with the monthly counts to ensure all months are included
        monthly_active_subscriptions = pd.merge(pd.DataFrame(date_range, columns=['Month']), monthly_active_subscriptions, how='left', on='Month')
        monthly_active_subscriptions['Active Subscriptions'].fillna(0, inplace=True)

        # Plotting the time series
        fig = px.line(
            monthly_active_subscriptions,
            x='Month',
            y='Active Subscriptions',
            title='Active Subscriptions Over Time',
            labels={'Month': 'Month', 'Active Subscriptions': 'Active Subscriptions'},
            template='plotly_white'
        )

        # Customize the appearance of the graph
        fig.update_traces(line=dict(width=2.5))

        # Add annotations for each data point
        for i, row in monthly_active_subscriptions.iterrows():
            fig.add_annotation(
                x=row['Month'],
                y=row['Active Subscriptions'],
                text=f"{row['Active Subscriptions']}",
                font=dict(color='black', size=10),
                showarrow=True,
                arrowhead=0,
                ax=0,
                ay=-40
            )

        # Display the line chart in Streamlit
        st.plotly_chart(fig, use_container_width=True)

        #####################################################################################
        st.divider()
        st.subheader('Revenue Analysis by Product')

        # Function to create bar chart showing total revenue by product type or product name
        def plot_total_revenue_by_category(data, category):
            # Group by category (product_type or product_name) and sum total revenue
            revenue_by_category = data.groupby(category)['total_amount'].sum().reset_index()

            # Sort by total_amount in descending order
            revenue_by_category = revenue_by_category.sort_values(by='total_amount', ascending=False)

            # Plot bar chart
            fig = px.bar(
                revenue_by_category,
                x=category,
                y='total_amount',
                title=f'Total Revenue by {category.capitalize()}',
                labels={category: category.capitalize(), 'total_amount': 'Total Revenue ($)'},
                template='plotly_white'
            )

            # Customize layout
            fig.update_layout(
                xaxis_title=category.capitalize(),
                yaxis_title='Total Revenue ($)',
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
            )

            return fig

        # Function to create monthly revenue trend by selected product type or product name
        def plot_monthly_revenue(data, category, selected_item):
            # Filter data for the selected category and item
            data_filtered = data[data[category] == selected_item]

            # Group by month and sum total revenue
            monthly_revenue = data_filtered.groupby(data_filtered['created_at'].dt.to_period('M').astype(str))['total_amount'].sum().reset_index()

            # Plot bar chart
            fig = px.bar(
                monthly_revenue,
                x='created_at',
                y='total_amount',
                title=f'Monthly Revenue for {selected_item}',
                labels={'created_at': 'Month', 'total_amount': 'Total Revenue ($)'},
                template='plotly_white'
            )

            # Customize layout
            fig.update_layout(
                xaxis_title='Month',
                yaxis_title='Total Revenue ($)',
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
            )

            return fig

        # Radio button to select between product_type and product_name for total revenue
        selected_category = st.radio('Select Category for Total Revenue', ['Product Type', 'Product Name'])

        if selected_category == 'Product Type':
            # Show total revenue by product type
            fig_category = plot_total_revenue_by_category(data_date_filtered, 'product_type')
            st.plotly_chart(fig_category, use_container_width=True)
        elif selected_category == 'Product Name':
            # Show total revenue by product name
            fig_category = plot_total_revenue_by_category(data_date_filtered, 'product_name')
            st.plotly_chart(fig_category, use_container_width=True)

        # Dropdown to select product type or product name for monthly revenue
        selected_dropdown = st.radio('Select Category for Monthly Revenue', ['Product Type', 'Product Name'])

        if selected_dropdown == 'Product Type':
            product_types = data_date_filtered['product_type'].unique().tolist()
            selected_product = st.selectbox('Select Product Type', product_types)

            # Show monthly revenue trend for selected product type
            fig_product = plot_monthly_revenue(data_date_filtered, 'product_type', selected_product)
            st.plotly_chart(fig_product, use_container_width=True)
        elif selected_dropdown == 'Product Name':
            product_names = data_date_filtered['product_name'].unique().tolist()
            selected_product = st.selectbox('Select Product Name', product_names)

            # Show monthly revenue trend for selected product name
            fig_product = plot_monthly_revenue(data_date_filtered, 'product_name', selected_product)
            st.plotly_chart(fig_product, use_container_width=True)

        #####################################################################################
        st.divider()
        st.subheader('Customer Analysis')

        # Convert necessary columns to datetime
        data_date_filtered['created_at'] = pd.to_datetime(data_date_filtered['created_at'], utc=True)

        # Convert necessary columns to datetime
        data_date_filtered['created_at'] = pd.to_datetime(data_date_filtered['created_at'], utc=True)

        # Calculate CLV
        clv = data_date_filtered.groupby('customer_name')['total_amount'].sum().reset_index()
        clv.rename(columns={'total_amount': 'CLV'}, inplace=True)

        # Calculate average revenue per customer
        avg_revenue_per_customer = clv['CLV'].mean()

        # Calculate churn rate
        current_date = pd.to_datetime('today', utc=True)
        last_transaction_date = data_date_filtered.groupby('customer_id')['created_at'].max()
        churned_customers = last_transaction_date[last_transaction_date < (current_date - pd.DateOffset(months=3))]
        churn_rate = len(churned_customers) / len(last_transaction_date)

        # Calculate the max date in data_date_filtered
        max_date = data_date_filtered['created_at'].max()

        # Calculate current active customers (since max date in data_date_filtered)
        current_active_customers = data_date_filtered[data_date_filtered['created_at'] >= max_date - pd.DateOffset(months=1)]
        current_active_customer_count = current_active_customers['customer_id'].nunique()

        # Display metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label="Average Revenue per Customer", value=f"${avg_revenue_per_customer:,.2f}")
        with col2:
            st.metric(label="Churn Rate", value=f"{churn_rate:.2%}")
        with col3:
            st.metric(label="Current Active Customers (Last Month)", value=current_active_customer_count)

        # Plot CLV distribution
        fig_clv_distribution = px.histogram(
            clv,
            x='CLV',
            title='Customer Lifetime Value (CLV) Distribution',
            labels={'CLV': 'Customer Lifetime Value ($)', 'count': 'Number of Customers'},
            template='plotly_white'
        )
        fig_clv_distribution.update_layout(
            xaxis_title='Customer Lifetime Value ($)',
            yaxis_title='Number of Customers',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )
        fig_clv_distribution.update_traces(texttemplate='%{y}', textposition='inside')
        st.plotly_chart(fig_clv_distribution, use_container_width=True)

        col13, col14 = st.columns(2)

        with col13:
            # Plot revenue over time
            data_date_filtered['created_at_month'] = data_date_filtered['created_at'].dt.to_period('M').dt.to_timestamp()
            revenue_over_time = data_date_filtered.groupby('created_at_month')['total_amount'].sum().reset_index()
            fig_revenue_over_time = px.line(
                revenue_over_time,
                x='created_at_month',
                y='total_amount',
                title='Revenue Over Time',
                labels={'created_at_month': 'Month', 'total_amount': 'Total Revenue ($)'},
                template='plotly_white'
            )
            fig_revenue_over_time.update_layout(
                xaxis_title='Month',
                yaxis_title='Total Revenue ($)',
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
            )
            st.plotly_chart(fig_revenue_over_time, use_container_width=True)
        with col14:
            # Plot active customers over time
            active_customers = data_date_filtered.groupby('created_at_month')['customer_id'].nunique().reset_index()
            fig_active_customers_over_time = px.line(
                active_customers,
                x='created_at_month',
                y='customer_id',
                title='Active Customers Over Time',
                labels={'created_at_month': 'Month', 'customer_id': 'Number of Active Customers'},
                template='plotly_white'
            )
            fig_active_customers_over_time.update_layout(
                xaxis_title='Month',
                yaxis_title='Number of Active Customers',
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
            )
            st.plotly_chart(fig_active_customers_over_time, use_container_width=True)

        # Segment customers based on CLV
        bins = [0, 50, 100, 500, 1000, clv['CLV'].max()]
        labels = ['0-50', '50-100', '100-500', '500-1000', '1000+']

        # Identify top customers by CLV
        top_customers_list = clv.sort_values(by='CLV', ascending=False).head(10).reset_index(drop=True)
        st.caption("Top Customer List")
        st.dataframe(top_customers_list, use_container_width=True)