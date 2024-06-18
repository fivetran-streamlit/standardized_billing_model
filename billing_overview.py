import streamlit as st

# Set the page configuration to wide mode
st.set_page_config(layout="wide")

# Read the README contents
with open("README.md", "r") as f:
    readme_content = f.read()

# Render the README as markdown in the app
st.markdown(readme_content)