import streamlit as st
from datetime import datetime, timedelta
from functions.query import query_results
import pandas as pd

def date_filter(destination="BigQuery"):
    dest = destination

    data = query_results(destination=dest)

    # Extract the minimum and maximum date from your data
    min_created_at = data['created_at'].min()
    max_created_at = data['created_at'].max()

    # Compute start of the two-week period (last year from max created_at)
    start_of_year = max_created_at - timedelta(days=365)

    # Compute end of the week for the max created_at
    end_of_week = max_created_at - timedelta(days=(max_created_at.weekday() - 6))

    # Check if the dates are already in session state, otherwise set them
    if 'start_date' not in st.session_state:
        st.session_state.start_date = start_of_year
    if 'end_date' not in st.session_state:
        st.session_state.end_date = end_of_week

    # Use slider to select dates within the range
    date_range = st.slider(
        "(Required) Select your date range",
        min_value=min_created_at,
        max_value=max_created_at,
        value=(st.session_state.start_date, st.session_state.end_date),
        format="MM/DD/YYYY"  # Customize format as needed
    )

    # Update the session state with the selected dates
    st.session_state.start_date, st.session_state.end_date = date_range

    return data, date_range

def filter_data(start, end, data_ref):
    data_date_filtered = data_ref.query("`created_at` >= @start and `created_at` <= @end")

    return data_date_filtered
