import streamlit as st

from data.database import initialize_database
from ui.dashboard import show_dashboard
from ui.discoveryui import show_discovery
from ui.leads import show_leads
from ui.outreach import show_outreach
from ui.pipeline import show_pipeline
from ui.sidebar import show_sidebar


st.set_page_config(
    page_title="AI Lead Assistant",
    layout="wide",
)

# Initialize the database
initialize_database()

# Navigation
page = show_sidebar()

# Display selected page
if page == "Dashboard":
    show_dashboard()

elif page == "Find Leads":
    show_discovery()

elif page == "Leads":
    show_leads()

elif page == "Outreach":
    show_outreach()

elif page == "Pipeline":
    show_pipeline()