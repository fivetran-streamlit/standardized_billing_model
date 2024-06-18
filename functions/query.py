import streamlit as st
import pandas as pd
from google.oauth2 import service_account
from google.cloud import bigquery

data_columns = ['header_id',
                'line_item_id',
                'line_item_index',
                'record_type',
                'created_at',
                'currency',
                'header_status',
                'product_id',
                'product_name',
                'transaction_type',
                'billing_type',
                'product_type',
                'quantity',
                'unit_amount',
                'discount_amount',
                'tax_amount',
                'total_amount',
                'payment_id',
                'payment_method_id',
                'payment_method',
                'payment_at',
                'fee_amount',
                'refund_amount',
                'subscription_id',
                'subscription_period_started_at',
                'subscription_period_ended_at',
                'subscription_status',
                'customer_id',
                'customer_level',
                'customer_name',
                'customer_company',
                'customer_email',
                'customer_city',
                'customer_country'
                ]

columns_str = ', '.join(data_columns)
quoted_columns = [f'{col}' for col in data_columns]

schema = 'add_schema_here'
platform = 'add_platform_here'

# Perform query.
# Uses st.cache_data to only rerun when the query changes or after 10 min.
# Only used for local testing. Once deployed this will not be used and instead will use the fake data.
@st.cache_data(ttl=600)
def run_query(query):
    # Create API client.
    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"]
    )
    client = bigquery.Client(credentials=credentials)
    query_job = client.query(query)
    rows_raw = query_job.result()
    # Convert to list of dicts. Required for st.cache_data to hash the return value.
    rows = [dict(row) for row in rows_raw]
    return rows

def query_results(destination):
    ## Commented out as this will only be used for local testing at the moment.
    # query = run_query(
    #     f"""select {columns_str}
    #     from {schema}.{platform}__line_item_enhanced
    #     """
    # )

    query = pd.read_csv('data/dunder_mifflin__line_item_enhanced.csv', parse_dates=['created_at', 'payment_at', 'subscription_period_started_at', 'subscription_period_ended_at'])
    data = pd.DataFrame(query, columns=data_columns)

    # Ensure 'created_at' column is datetime if loaded from CSV
    if 'created_at' in data.columns and not pd.api.types.is_datetime64_any_dtype(data['created_at']):
        data['created_at'] = pd.to_datetime(data['created_at'])
        
    # Get the data into the app and specify any datatypes if needed.
    data_load_state = st.text('Loading data...')
    data['created_at'] = data['created_at'].dt.date
    data_load_state.text("Done! (using st.cache_data)")

    return data