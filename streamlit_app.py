import streamlit as st

from ui.dashboard import show_dashboard
from ui.discoveryui import show_discovery
from ui.pipeline import show_pipeline
from ui.outreach import show_outreach


st.set_page_config(
    page_title="AI Lead Assistant",
    page_icon="",
    layout="wide",
)


if "page" not in st.session_state:
    st.session_state.page = "Dashboard"


with st.sidebar:
    st.markdown("## AI Lead Assistant")
    st.caption("Customer discovery and lead management")
    st.divider()

    pages = [
        "Dashboard",
        "Find Leads",
        "Pipeline",
        "AI Tools",
    ]

    for page in pages:
        if st.button(
            page,
            key=f"nav_{page}",
            use_container_width=True,
        ):
            st.session_state.page = page
            st.rerun()


if st.session_state.page == "Dashboard":
    show_dashboard()

elif st.session_state.page == "Find Leads":
    show_discovery()

elif st.session_state.page == "Pipeline":
    show_pipeline()

elif st.session_state.page == "AI Tools":
    show_outreach()

else:
    show_dashboard()