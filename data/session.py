import streamlit as st


def initialize_session():
    if "leads" not in st.session_state:
        st.session_state.leads = []

    if "outreach" not in st.session_state:
        st.session_state.outreach = []

    if "activity" not in st.session_state:
        st.session_state.activity = []


def add_lead(lead):
    st.session_state.leads.append(lead)


def get_leads():
    return st.session_state.leads


def add_activity(message):
    st.session_state.activity.insert(0, message)


def get_activity():
    return st.session_state.activity