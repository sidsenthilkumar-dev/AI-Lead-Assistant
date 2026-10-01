import streamlit as st

from ai.qualification import qualify_lead
from data.database import add_lead
from data.models import Lead
from Services.discovery import search_businesses


def show_discovery():

    st.title("Find Leads")
    st.caption("Find potential customers based on business type and location.")

    if "discovery_results" not in st.session_state:
        st.session_state.discovery_results = []

    if "lead_analysis" not in st.session_state:
        st.session_state.lead_analysis = {}

    target_business = st.text_input(
        "Business type",
        placeholder="Example: restaurant, roofing company, dentist",
    )

    location = st.text_input(
        "Location",
        placeholder="Example: Apex, NC",
    )

    goal = st.text_input(
        "Goal",
        placeholder="Example: Find 20 new customers",
    )

    if st.button(
        "Find Potential Customers",
        type="primary",
        use_container_width=True,
    ):

        if not target_business or not location:
            st.warning("Enter a business type and location first.")

        else:

            with st.spinner("Finding potential customers..."):

                try:

                    businesses = search_businesses(
                        target_business,
                        location,
                    )

                    st.session_state.discovery_results = businesses
                    st.session_state.lead_analysis = {}

                except Exception as e:

                    st.error(
                        f"Business search failed: {e}"
                    )

    businesses = st.session_state.discovery_results

    if not businesses:
        return

    st.success(
        f"Found {len(businesses)} potential customers."
    )

    for index, business in enumerate(businesses):

        company = business.get(
            "company",
            "Unknown Business",
        )

        industry = business.get(
            "industry",
            target_business,
        )

        website = business.get(
            "website",
            "",
        )

        phone = business.get(
            "phone",
            "",
        )

        address = business.get(
            "address",
            "",
        )

        lead_key = f"{company}_{index}"

        with st.container(border=True):

            st.subheader(company)

            if industry:
                st.write(
                    f"Industry: {industry}"
                )

            if address:
                st.write(
                    f"Address: {address}"
                )

            if phone:
                st.write(
                    f"Phone: {phone}"
                )

            if website:
                st.write(
                    f"Website: {website}"
                )

            col1, col2 = st.columns(2)

            with col1:

                if st.button(
                    "Analyze Lead",
                    key=f"analyze_{lead_key}",
                    use_container_width=True,
                ):

                    try:

                        lead_data = {
                            "company": company,
                            "industry": industry,
                            "website": website,
                            "phone": phone,
                            "address": address,
                            "problem": goal,
                        }

                        with st.spinner(
                            "Analyzing lead..."
                        ):

                            analysis = qualify_lead(
                                lead_data,
                                target_business,
                                goal,
                            )

                        st.session_state.lead_analysis[
                            lead_key
                        ] = analysis

                    except Exception as e:

                        st.error(
                            f"AI analysis failed: {e}"
                        )

            with col2:

                if st.button(
                    "Save Lead",
                    key=f"save_{lead_key}",
                    use_container_width=True,
                ):

                    try:

                        lead = Lead(
                            name=company,
                            company=company,
                            problem=goal,
                            website=website,
                            phone=phone,
                            address=address,
                            industry=industry,
                            source="OpenStreetMap",
                        )

                        add_lead(lead)

                        st.success(
                            f"{company} saved as a lead."
                        )

                    except Exception as e:

                        st.error(
                            f"Could not save lead: {e}"
                        )

            if lead_key in st.session_state.lead_analysis:

                analysis = st.session_state.lead_analysis[
                    lead_key
                ]

                st.divider()

                st.write("### AI Analysis")

                if isinstance(analysis, dict):

                    score = analysis.get(
                        "score",
                        analysis.get(
                            "qualification_score",
                            "N/A",
                        ),
                    )

                    qualification = analysis.get(
                        "qualification",
                        "",
                    )

                    next_action = analysis.get(
                        "next_action",
                        "",
                    )

                    st.metric(
                        "Lead Score",
                        score,
                    )

                    if qualification:
                        st.write(
                            f"**Qualification:** {qualification}"
                        )

                    if next_action:
                        st.write(
                            f"**Next Action:** {next_action}"
                        )

                    for key, value in analysis.items():

                        if key in {
                            "score",
                            "qualification_score",
                            "qualification",
                            "next_action",
                        }:
                            continue

                        if value:

                            label = key.replace(
                                "_",
                                " ",
                            ).title()

                            st.write(
                                f"**{label}:** {value}"
                            )

                else:

                    st.write(analysis)