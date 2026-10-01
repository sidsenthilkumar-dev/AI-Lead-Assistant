import streamlit as st

from data.database import get_leads


STATUSES = [
    "New",
    "Contacted",
    "Interested",
    "Meeting",
    "Won",
    "Lost",
]


def show_pipeline():
    st.title("Pipeline")

    st.caption(
        "Track potential customers from first discovery to closed business."
    )

    leads = get_leads()

    columns = st.columns(len(STATUSES))

    for column, status in zip(
        columns,
        STATUSES,
    ):
        with column:
            st.subheader(status)

            matching = [
                lead
                for lead in leads
                if lead.get("status") == status
            ]

            st.caption(
                f"{len(matching)} leads"
            )

            for lead in matching:
                with st.container(
                    border=True
                ):
                    st.write(
                        f"**{lead['company']}**"
                    )

                    if lead.get("score") is not None:
                        st.caption(
                            f"Score: {lead['score']}/100"
                        )