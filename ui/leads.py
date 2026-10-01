import streamlit as st

from data.database import get_leads, update_lead


STATUSES = [
    "New",
    "Contacted",
    "Interested",
    "Meeting",
    "Won",
    "Lost",
]


def show_leads():
    st.title("Leads")

    leads = get_leads()

    if not leads:
        st.info(
            "No leads yet. Use Find Leads to discover potential customers."
        )
        return

    for lead in leads:
        with st.container(border=True):
            col1, col2 = st.columns([4, 2])

            with col1:
                st.subheader(
                    lead["company"]
                )

                if lead.get("industry"):
                    st.caption(
                        lead["industry"]
                    )

                if lead.get("address"):
                    st.write(
                        lead["address"]
                    )

                if lead.get("qualification"):
                    st.write(
                        lead["qualification"]
                    )

                if lead.get("problem"):
                    st.write(
                        f"Opportunity: {lead['problem']}"
                    )

            with col2:
                score = lead.get("score")

                if score is not None:
                    st.metric(
                        "AI Score",
                        f"{score}/100",
                    )

                current_status = lead.get(
                    "status",
                    "New",
                )

                new_status = st.selectbox(
                    "Status",
                    STATUSES,
                    index=STATUSES.index(
                        current_status
                    )
                    if current_status in STATUSES
                    else 0,
                    key=f"status_{lead['id']}",
                )

                if new_status != current_status:
                    update_lead(
                        lead["id"],
                        status=new_status,
                    )
                    st.rerun()