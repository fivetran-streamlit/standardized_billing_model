import streamlit as st
import plost
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from functions.query import query_results

# Set page configuration
st.set_page_config(
    layout="wide",   # Set the layout to wide
    initial_sidebar_state="expanded",  # Optionally expand the sidebar initially
)

st.title("Standardized Billing Line Item Model Schema Overview")
billing_data = query_results(destination="BigQuery")

# Convert 'created_at' column to datetime if it's not already in datetime format
billing_data['created_at'] = pd.to_datetime(billing_data['created_at'])
# Filter out rows where Column1 and Column2 are not null
filtered_df = billing_data.dropna(subset=['subscription_period_started_at'])

st.subheader("Table Example")
st.table(filtered_df.head(5))

st.markdown('---')
st.subheader("Schema Breakdown")
st.text("Each field within the schema includes the definition and the respective `table.field_name` from the original source.")
# Define your schema with field names and descriptions
schema = {
    "🔑 header_id": "ID of either the invoice or order.",
    "🔑 line_item_id": "ID of either the invoice line or order line item.",
    "line_item_index": "Numerical identifier of the line item within the header object.",
    "record_type": "Either 'header' or 'line_item' to differentiate if the record is originally from the line item table or was created to document information only available at the header level.",
    "created_at": "Date the line item entry was created.",
    "currency": "Determines the currency in which the transaction took place.",
    "header_status": "Indicates the status of the header. Eg. paid, voided, returned.",
    "product_id": "ID of the product associated with the line item.",
    "product_name": "Name of the product associated with the line item.",
    "product_type": "Type of the product (e.g., physical, digital).",
    "product_category": "Category to which the product belongs (e.g., electronics, clothing).",
    "quantity": "Quantity of the product in the line item.",
    "unit_amount": "Unit price of the product.",
    "discount_amount": "Amount of discount applied to the line item.",
    "tax_rate": "Tax rate applied to the line item.",
    "tax_amount": "Amount of tax applied to the line item.",
    "total_amount": "Total amount for the line item (including tax and discounts).",
    "payment_id": "ID of the payment associated with the line item.",
    "payment_method": "Method used for payment (e.g., credit card, PayPal).",
    "payment_at": "Date and time of the payment.",
    "fee_amount": "Any additional fees associated with the payment.",
    "refund_amount": "Amount refunded for the line item (if applicable).",
    "subscription_id": "ID of the subscription (if applicable).",
    "subscription_period_started_at": "Start date of the subscription period (if applicable).",
    "subscription_period_ended_at": "End date of the subscription period (if applicable).",
    "subscription_status": "Status of the subscription (if applicable).",
    "customer_id": "ID of the customer associated with the line item.",
    "customer_level": "Identifies if the customer is reported at the account or customer level.",
    "customer_name": "Name of the customer.",
    "customer_company": "Company name of the customer (if applicable).",
    "customer_email": "Email address of the customer.",
    "customer_city": "City of the customer's address.",
    "customer_country": "Country of the customer's address."
}

# Supported platforms and their field names
platform_fields = {
    "Stripe": {
        "🔑 header_id": "invoice_line_item.invoice_id",
        "🔑 line_item_id": "invoice_line_item.line_item_id",
        "line_item_index": "Created with row number using invoice_id partition, ordered by amount",
        "record_type": "'line_item'",
        "created_at": "invoice.created_at",
        "currency": "invoice_line_item.currency",
        "header_status": "invoice.status",
        "product_id": "price_plan.product_id",
        "product_name": "product.name",
        "transaction_type": "balance_transaction.type",
        "billing_type": "invoice_line_item.type",
        "product_type": "product.type",
        "quantity": "invoice_line_item.quantity",
        "unit_amount": "Calculated using invoice_line_item, dividing amount by quantity",
        "discount_amount": "discount.amount",
        "tax_amount": "invoice.tax",
        "total_amount": "invoice.total",
        "payment_id": "payment_intent.payment_intent_id",
        "payment_method_id": "payment_method.payment_method_id",
        "payment_method": "payment_method.type",
        "payment_at": "charge.created_at",
        "fee_amount": "balance_transaction.fee",
        "refund_amount": "refund.amount",
        "subscription_id": "invoice.subscription_id",
        "subscription_period_started_at": "subscription.current_period_start",
        "subscription_period_ended_at": "subscription.current_period_end",
        "subscription_status": "subscription.status",
        "customer_id": "invoice.customer_id",
        "customer_level": "'customer'",
        "customer_name": "customer.customer_name",
        "customer_company": "connected_account.company_name",
        "customer_email": "customer.email",
        "customer_city": "customer.customer_address_city",
        "customer_country": "customer.customer_address_country"
    },
    "Zuora": {
        "🔑 header_id": "invoice_item.invoice_id",
        "🔑 line_item_id": "invoice_item.invoice_line_id",
        "line_item_index": "Created from row number with invoice and line item partitioned",
        "record_type": "header or invoice",
        "created_at": "invoice.created_at",
        "currency": "invoice_item.transaction_currency",
        "header_status": "invoice.status",
        "product_id": "invoice_item.product_id",
        "product_name": "product.product_name",
        "transaction_type": "invoice_item.processing_type",
        "billing_type": "invoice.source_type",
        "product_type": "product.category",
        "quantity": "invoice_item.quantity",
        "unit_amount": "invoice_item.unit_price",
        "discount_amount": "invoice_item.charge_amount (when invoice_item.processing_type = '1')",
        "tax_amount": "invoice_item.tax_amount",
        "total_amount": "invoice_item.charge_amount",
        "payment_id": "invoice_payment.payment_id",
        "payment_method_id": "invoice_payment.payment_method_id",
        "payment_method": "payment_method.name",
        "payment_at": "payment.effective_date",
        "fee_amount": "null",
        "refund_amount": "invoice.refund_amount",
        "subscription_id": "invoice_item.subscription_id",
        "subscription_period_started_at": "subscription.subscription_start_date",
        "subscription_period_ended_at": "subscription.subscription_ended_at",
        "subscription_status": "subscription.status",
        "customer_id": "invoice_item.account_id",
        "customer_level": "customer",
        "customer_name": "dbt.concat(['contacts.first_name', '' '', 'contacts.last_name'])",
        "customer_company": "account.name",
        "customer_email": "contact.work_email",
        "customer_city": "contact.city",
        "customer_country": "contact.country"
    },
    "Recurly": {
        "🔑 header_id": "TBD",
        "🔑 line_item_id": "TBD",
        "line_item_index": "TBD",
        "record_type": "TBD",
        "created_at": "TBD",
        "currency": "TBD",
        "line_item_status": "TBD",
        "header_status": "TBD",
        "product_id": "TBD",
        "product_name": "TBD",
        "product_type": "TBD",
        "product_category": "TBD",
        "quantity": "TBD",
        "unit_amount": "TBD",
        "discount_amount": "TBD",
        "tax_amount": "TBD",
        "total_amount": "TBD",
        "payment_id": "TBD",
        "payment_method": "TBD",
        "payment_at": "TBD",
        "fee_amount": "TBD",
        "refund_id": "TBD",
        "refund_amount": "TBD",
        "refunded_at": "TBD",
        "subscription_id": "TBD",
        "subscription_period_started_at": "TBD",
        "subscription_period_ended_at": "TBD",
        "subscription_status": "TBD",
        "customer_id": "TBD",
        "customer_level": "TBD",
        "customer_name": "TBD",
        "customer_company": "TBD",
        "customer_email": "TBD",
        "customer_city": "TBD",
        "customer_country": "TBD"
    },
    "Shopify": {
        "🔑 header_id": "TBD",
        "🔑 line_item_id": "TBD",
        "line_item_index": "TBD",
        "record_type": "TBD",
        "created_at": "TBD",
        "currency": "TBD",
        "line_item_status": "TBD",
        "header_status": "TBD",
        "product_id": "TBD",
        "product_name": "TBD",
        "product_type": "TBD",
        "product_category": "TBD",
        "quantity": "TBD",
        "unit_amount": "TBD",
        "discount_amount": "TBD",
        "tax_amount": "TBD",
        "total_amount": "TBD",
        "payment_id": "TBD",
        "payment_method": "TBD",
        "payment_at": "TBD",
        "fee_amount": "TBD",
        "refund_id": "TBD",
        "refund_amount": "TBD",
        "refunded_at": "TBD",
        "subscription_id": "TBD",
        "subscription_period_started_at": "TBD",
        "subscription_period_ended_at": "TBD",
        "subscription_status": "TBD",
        "customer_id": "TBD",
        "customer_level": "TBD",
        "customer_name": "TBD",
        "customer_company": "TBD",
        "customer_email": "TBD",
        "customer_city": "TBD",
        "customer_country": "TBD"
    },
    "Recharge": {
        "🔑 header_id": "TBD",
        "🔑 line_item_id": "TBD",
        "line_item_index": "TBD",
        "record_type": "TBD",
        "created_at": "TBD",
        "currency": "TBD",
        "line_item_status": "TBD",
        "header_status": "TBD",
        "product_id": "TBD",
        "product_name": "TBD",
        "product_type": "TBD",
        "product_category": "TBD",
        "quantity": "TBD",
        "unit_amount": "TBD",
        "discount_amount": "TBD",
        "tax_amount": "TBD",
        "total_amount": "TBD",
        "payment_id": "TBD",
        "payment_method": "TBD",
        "payment_at": "TBD",
        "fee_amount": "TBD",
        "refund_id": "TBD",
        "refund_amount": "TBD",
        "refunded_at": "TBD",
        "subscription_id": "TBD",
        "subscription_period_started_at": "TBD",
        "subscription_period_ended_at": "TBD",
        "subscription_status": "TBD",
        "customer_id": "TBD",
        "customer_level": "TBD",
        "customer_name": "TBD",
        "customer_company": "TBD",
        "customer_email": "TBD",
        "customer_city": "TBD",
        "customer_country": "TBD"
    }
}

# Iterate over each field in the schema
for field, description in schema.items():
    # Create an expander for each field
    with st.expander(f"**{field}**", expanded=False):
        st.write(description)
        
        # Add dropdowns for each supported platform
        for platform, fields in platform_fields.items():
            if field in fields:
                st.write(f"- **{platform}**: {fields[field]}")
            else:
                st.write(f"- **{platform}**: Currently not available")
