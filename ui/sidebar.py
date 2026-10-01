import streamlit as st


def show_sidebar():
    st.sidebar.title("AI Lead Assistant")

    st.sidebar.caption(
        "AI-powered customer acquisition"
    )

    return st.sidebar.radio(
        "Navigation",
        [
            "Dashboard",
            "Find Leads",
            "Leads",
            "Outreach",
            "Pipeline",
        ],
    )