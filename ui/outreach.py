import streamlit as st

from ai.outreach import (
    generate_follow_up,
    generate_outreach,
)
from data.database import (
    get_leads,
    update_lead,
)


def show_outreach():
    st.title("Outreach")

    st.caption(
        "Generate personalized messages for your highest-value opportunities."
    )

    target_business = st.text_input(
        "Your business",
        placeholder="Example: Apex Commercial Roofing",
    )

    leads = get_leads()

    if not leads:
        st.info(
            "Add leads before generating outreach."
        )
        return

    for lead in leads:
        with st.container(border=True):
            st.subheader(
                lead["company"]
            )

            if lead.get("score") is not None:
                st.caption(
                    f"AI Score: {lead['score']}/100"
                )

            if st.button(
                "Generate Outreach",
                key=f"outreach_{lead['id']}",
            ):
                if not target_business:
                    st.warning(
                        "Enter your business first."
                    )
                else:
                    with st.spinner(
                        "Generating personalized outreach..."
                    ):
                        message = generate_outreach(
                            target_business,
                            lead,
                        )

                    update_lead(
                        lead["id"],
                        outreach_message=message,
                        status="Contacted",
                    )

                    st.text_area(
                        "First message",
                        value=message,
                        height=150,
                        key=f"message_{lead['id']}",
                    )

            if lead.get("outreach_message"):
                st.text_area(
                    "Current outreach",
                    value=lead["outreach_message"],
                    height=150,
                    key=f"saved_message_{lead['id']}",
                )

                if st.button(
                    "Generate Follow-Up",
                    key=f"followup_{lead['id']}",
                ):
                    with st.spinner(
                        "Generating follow-up..."
                    ):
                        follow_up = generate_follow_up(
                            target_business,
                            lead,
                        )

                    update_lead(
                        lead["id"],
                        follow_up_message=follow_up,
                    )

                    st.rerun()

            if lead.get("follow_up_message"):
                st.text_area(
                    "Follow-up",
                    value=lead["follow_up_message"],
                    height=120,
                    key=f"followup_text_{lead['id']}",
                )