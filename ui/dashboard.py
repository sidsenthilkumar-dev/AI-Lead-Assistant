import streamlit as st

from data.database import get_leads


def show_dashboard():
    st.title("Dashboard")

    st.caption(
        "Turn potential customers into actual customers."
    )

    leads = get_leads()

    total = len(leads)

    high_priority = sum(
        1
        for lead in leads
        if (lead.get("score") or 0) >= 75
    )

    interested = sum(
        1
        for lead in leads
        if lead.get("status") == "Interested"
    )

    won = sum(
        1
        for lead in leads
        if lead.get("status") == "Won"
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Potential Customers", total)
    col2.metric("High Priority", high_priority)
    col3.metric("Interested", interested)
    col4.metric("Won", won)

    st.divider()

    st.subheader("Recent Opportunities")

    if not leads:
        st.info(
            "No leads yet. Start by finding potential customers."
        )
        return

    for lead in leads[:8]:
        with st.container(border=True):
            col1, col2 = st.columns([4, 1])

            with col1:
                st.write(f"**{lead['company']}**")

                if lead.get("industry"):
                    st.caption(lead["industry"])

                if lead.get("problem"):
                    st.write(lead["problem"])

            with col2:
                score = lead.get("score")

                if score is not None:
                    st.metric("Score", score)