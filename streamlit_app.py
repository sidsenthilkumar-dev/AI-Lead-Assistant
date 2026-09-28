import json
import os
import re
import sqlite3
from typing import Any, Dict, List, Optional

import requests
import streamlit as st
from google import genai


# ============================================================
# APPLICATION CONFIGURATION
# ============================================================

APP_NAME = "AI Lead Assistant"
APP_VERSION = "3.1"

DATABASE_PATH = "leads.db"

DEFAULT_MODEL = "gemini-3.5-flash"

PIPELINE_STATUSES = [
    "New",
    "Contacted",
    "Interested",
    "Meeting",
    "Won",
    "Lost",
]

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

USER_AGENT = "AI-Lead-Assistant/3.1"


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title=APP_NAME,
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CUSTOM STYLING
# ============================================================

st.markdown(
    """
    <style>

        .block-container {
            max-width: 1450px;
            padding-top: 2rem;
            padding-bottom: 4rem;
        }

        h1 {
            font-size: 2.25rem !important;
            font-weight: 700 !important;
            letter-spacing: -0.04em;
        }

        h2 {
            font-size: 1.55rem !important;
            font-weight: 650 !important;
            letter-spacing: -0.025em;
        }

        h3 {
            font-size: 1.15rem !important;
            font-weight: 650 !important;
        }

        section[data-testid="stSidebar"] {
            border-right: 1px solid rgba(128, 128, 128, 0.18);
        }

        section[data-testid="stSidebar"] .block-container {
            padding-top: 2rem;
        }

        [data-testid="stMetric"] {
            border: 1px solid rgba(128, 128, 128, 0.22);
            border-radius: 10px;
            padding: 1rem 1.1rem;
            background: rgba(128, 128, 128, 0.025);
        }

        [data-testid="stMetricLabel"] {
            font-size: 0.82rem;
        }

        [data-testid="stMetricValue"] {
            font-size: 1.65rem;
        }

        div.stButton > button {
            border-radius: 7px;
            min-height: 2.4rem;
            font-weight: 500;
        }

        div[data-baseweb="input"] > div,
        div[data-baseweb="textarea"] > div {
            border-radius: 7px;
        }

        .app-card {
            border: 1px solid rgba(128, 128, 128, 0.22);
            border-radius: 10px;
            padding: 1.15rem;
            margin-bottom: 0.8rem;
        }

        .lead-title {
            font-size: 1.12rem;
            font-weight: 650;
            margin-bottom: 0.2rem;
        }

        .muted {
            opacity: 0.68;
            font-size: 0.88rem;
        }

        .eyebrow {
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-size: 0.72rem;
            font-weight: 650;
            opacity: 0.62;
        }

        .score-large {
            font-size: 2rem;
            font-weight: 700;
            line-height: 1;
        }

        div[data-testid="stVerticalBlock"] > div {
            gap: 0.55rem;
        }

        [data-testid="stDataFrame"] {
            border-radius: 8px;
        }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SESSION STATE
# ============================================================

if "page" not in st.session_state:
    st.session_state.page = "Dashboard"

if "qualified_leads" not in st.session_state:
    st.session_state.qualified_leads = []

if "discovered_businesses" not in st.session_state:
    st.session_state.discovered_businesses = []

if "last_search_location" not in st.session_state:
    st.session_state.last_search_location = ""

if "last_search_count" not in st.session_state:
    st.session_state.last_search_count = 0

if "debug_mode" not in st.session_state:
    st.session_state.debug_mode = False


# ============================================================
# API CONFIGURATION
# ============================================================

def get_api_key() -> str:
    """
    Load the Gemini API key from Streamlit secrets or
    the GEMINI_API_KEY environment variable.
    """

    try:
        secret_key = st.secrets.get("GEMINI_API_KEY")

        if secret_key:
            return str(secret_key)

    except Exception:
        pass

    environment_key = os.getenv("GEMINI_API_KEY")

    if environment_key:
        return environment_key

    return ""


def get_model_name() -> str:
    """
    Allow the Gemini model to be changed through Streamlit
    secrets or an environment variable.
    """

    try:
        configured_model = st.secrets.get(
            "GEMINI_MODEL",
            DEFAULT_MODEL,
        )

        if configured_model:
            return str(configured_model)

    except Exception:
        pass

    return os.getenv(
        "GEMINI_MODEL",
        DEFAULT_MODEL,
    )


API_KEY = get_api_key()
MODEL_NAME = get_model_name()

if API_KEY:
    client = genai.Client(api_key=API_KEY)
else:
    client = None


# ============================================================
# GEMINI HELPERS
# ============================================================

def generate_ai_response(
    prompt: str,
) -> Optional[str]:
    """
    Send a prompt to Gemini and return generated text.
    """

    if client is None:
        st.error(
            "Gemini is not configured. Add GEMINI_API_KEY "
            "to Streamlit secrets or the environment."
        )
        return None

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
        )

        if not response or not response.text:
            st.error("The AI returned an empty response.")
            return None

        return response.text.strip()

    except Exception as error:
        st.error(
            "The AI request could not be completed. "
            "Check the Gemini model, API key, or API limits."
        )

        if st.session_state.get("debug_mode", False):
            st.exception(error)

        return None


def clean_json_response(
    response_text: str,
) -> str:
    """
    Remove markdown code fences from AI JSON responses.
    """

    cleaned = response_text.strip()

    cleaned = re.sub(
        r"^```json\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    cleaned = re.sub(
        r"^```\s*",
        "",
        cleaned,
    )

    cleaned = re.sub(
        r"\s*```$",
        "",
        cleaned,
    )

    return cleaned.strip()


def generate_json_response(
    prompt: str,
) -> Optional[Any]:
    """
    Request JSON from Gemini and safely parse the result.
    """

    response_text = generate_ai_response(prompt)

    if not response_text:
        return None

    cleaned = clean_json_response(response_text)

    try:
        return json.loads(cleaned)

    except json.JSONDecodeError:

        object_start = cleaned.find("{")
        object_end = cleaned.rfind("}")

        array_start = cleaned.find("[")
        array_end = cleaned.rfind("]")

        candidates = []

        if object_start >= 0 and object_end > object_start:
            candidates.append(
                cleaned[object_start:object_end + 1]
            )

        if array_start >= 0 and array_end > array_start:
            candidates.append(
                cleaned[array_start:array_end + 1]
            )

        for candidate in candidates:

            try:
                return json.loads(candidate)

            except json.JSONDecodeError:
                continue

        if st.session_state.get("debug_mode", False):
            st.error("Gemini returned invalid JSON.")
            st.code(response_text)

        return None


# ============================================================
# DATABASE
# ============================================================

def get_connection() -> sqlite3.Connection:
    """
    Open a SQLite database connection.
    """

    connection = sqlite3.connect(DATABASE_PATH)

    connection.row_factory = sqlite3.Row

    return connection


def create_database() -> None:
    """
    Create the leads table if it does not exist.
    """

    connection = get_connection()

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            company TEXT NOT NULL,
            problem TEXT DEFAULT '',
            status TEXT DEFAULT 'New',
            qualification TEXT,
            lead_score INTEGER,
            next_action TEXT,
            follow_up TEXT,
            website TEXT DEFAULT '',
            phone TEXT DEFAULT '',
            address TEXT DEFAULT '',
            industry TEXT DEFAULT '',
            source TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    connection.commit()
    connection.close()


def migrate_database() -> None:
    """
    Add missing columns to older database versions.
    """

    connection = get_connection()

    existing_columns = {
        row["name"]
        for row in connection.execute(
            "PRAGMA table_info(leads)"
        ).fetchall()
    }

    migrations = {
        "qualification": "TEXT",
        "lead_score": "INTEGER",
        "next_action": "TEXT",
        "follow_up": "TEXT",
        "website": "TEXT DEFAULT ''",
        "phone": "TEXT DEFAULT ''",
        "address": "TEXT DEFAULT ''",
        "industry": "TEXT DEFAULT ''",
        "source": "TEXT DEFAULT ''",
        "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
    }

    for column, data_type in migrations.items():

        if column not in existing_columns:

            connection.execute(
                f"ALTER TABLE leads ADD COLUMN {column} {data_type}"
            )

    connection.commit()
    connection.close()


def add_lead(
    name: str,
    company: str,
    problem: str = "",
    website: str = "",
    phone: str = "",
    address: str = "",
    industry: str = "",
    source: str = "Manual",
) -> bool:
    """
    Add a lead while preventing duplicate company/address pairs.
    """

    connection = get_connection()

    duplicate = connection.execute(
        """
        SELECT id
        FROM leads
        WHERE LOWER(company) = LOWER(?)
        AND LOWER(COALESCE(address, '')) = LOWER(?)
        LIMIT 1
        """,
        (
            company.strip(),
            address.strip(),
        ),
    ).fetchone()

    if duplicate:
        connection.close()
        return False

    connection.execute(
        """
        INSERT INTO leads (
            name,
            company,
            problem,
            status,
            website,
            phone,
            address,
            industry,
            source
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            name.strip() or "Unknown Contact",
            company.strip(),
            problem.strip(),
            "New",
            website.strip(),
            phone.strip(),
            address.strip(),
            industry.strip(),
            source.strip(),
        ),
    )

    connection.commit()
    connection.close()

    return True


def get_leads() -> List[sqlite3.Row]:
    """
    Return all leads, newest first.
    """

    connection = get_connection()

    leads = connection.execute(
        """
        SELECT
            id,
            name,
            company,
            problem,
            status,
            qualification,
            lead_score,
            next_action,
            follow_up,
            website,
            phone,
            address,
            industry,
            source,
            created_at
        FROM leads
        ORDER BY id DESC
        """
    ).fetchall()

    connection.close()

    return leads


def update_status(
    lead_id: int,
    status: str,
) -> None:
    """
    Update a lead's pipeline status.
    """

    if status not in PIPELINE_STATUSES:
        return

    connection = get_connection()

    connection.execute(
        """
        UPDATE leads
        SET status = ?
        WHERE id = ?
        """,
        (
            status,
            lead_id,
        ),
    )

    connection.commit()
    connection.close()


def save_qualification(
    lead_id: int,
    qualification: str,
    score: Optional[int],
    next_action: str,
) -> None:
    """
    Save AI qualification data.
    """

    connection = get_connection()

    connection.execute(
        """
        UPDATE leads
        SET
            qualification = ?,
            lead_score = ?,
            next_action = ?
        WHERE id = ?
        """,
        (
            qualification,
            score,
            next_action,
            lead_id,
        ),
    )

    connection.commit()
    connection.close()


def save_follow_up(
    lead_id: int,
    follow_up: str,
) -> None:
    """
    Save an AI-generated follow-up plan.
    """

    connection = get_connection()

    connection.execute(
        """
        UPDATE leads
        SET follow_up = ?
        WHERE id = ?
        """,
        (
            follow_up,
            lead_id,
        ),
    )

    connection.commit()
    connection.close()


def delete_lead(
    lead_id: int,
) -> None:
    """
    Delete a lead.
    """

    connection = get_connection()

    connection.execute(
        """
        DELETE FROM leads
        WHERE id = ?
        """,
        (lead_id,),
    )

    connection.commit()
    connection.close()


# ============================================================
# LOCATION SEARCH
# ============================================================

@st.cache_data(ttl=3600)
def geocode_location(
    location: str,
) -> Optional[Dict[str, Any]]:
    """
    Convert a location into coordinates.
    """

    response = requests.get(
        NOMINATIM_URL,
        params={
            "q": location,
            "format": "json",
            "limit": 1,
        },
        headers={
            "User-Agent": USER_AGENT,
        },
        timeout=15,
    )

    response.raise_for_status()

    results = response.json()

    if not results:
        return None

    return {
        "lat": float(results[0]["lat"]),
        "lon": float(results[0]["lon"]),
        "display_name": results[0]["display_name"],
    }


@st.cache_data(ttl=1800)
def search_real_businesses(
    location: str,
    radius: int = 12000,
) -> List[Dict[str, Any]]:
    """
    Search OpenStreetMap/Overpass for named businesses.
    """

    location_data = geocode_location(location)

    if not location_data:
        return []

    latitude = location_data["lat"]
    longitude = location_data["lon"]

    query = f"""
    [out:json][timeout:30];

    (
        nwr["name"](around:{radius},{latitude},{longitude});
    );

    out center tags 100;
    """

    response = requests.post(
        OVERPASS_URL,
        data=query,
        headers={
            "User-Agent": USER_AGENT,
        },
        timeout=45,
    )

    response.raise_for_status()

    data = response.json()

    businesses = []

    for element in data.get("elements", []):

        tags = element.get("tags", {})

        name = tags.get(
            "name",
            "",
        ).strip()

        if len(name) < 2:
            continue

        center = element.get(
            "center",
            {},
        )

        business_lat = element.get(
            "lat",
            center.get("lat"),
        )

        business_lon = element.get(
            "lon",
            center.get("lon"),
        )

        address_parts = []

        for key in [
            "addr:housenumber",
            "addr:street",
            "addr:city",
            "addr:state",
            "addr:postcode",
        ]:

            value = tags.get(key)

            if value:
                address_parts.append(value)

        address = ", ".join(address_parts)

        website = (
            tags.get("website")
            or tags.get("contact:website")
            or ""
        )

        phone = (
            tags.get("phone")
            or tags.get("contact:phone")
            or ""
        )

        industry = (
            tags.get("amenity")
            or tags.get("shop")
            or tags.get("office")
            or tags.get("craft")
            or tags.get("tourism")
            or tags.get("leisure")
            or ""
        )

        businesses.append(
            {
                "name": name,
                "address": address,
                "website": website,
                "phone": phone,
                "industry": industry,
                "lat": business_lat,
                "lon": business_lon,
                "source": "OpenStreetMap",
            }
        )

    unique_businesses = {}

    for business in businesses:

        key = (
            business["name"].lower(),
            business["address"].lower(),
        )

        if key not in unique_businesses:
            unique_businesses[key] = business

    return list(unique_businesses.values())


# ============================================================
# AI LEAD SEARCH
# ============================================================

def qualify_search_results(
    businesses: List[Dict[str, Any]],
    business_type: str,
    customer_type: str,
    location: str,
) -> List[Dict[str, Any]]:
    """
    Use Gemini to score real business records against the
    user's target customer profile.

    Gemini ranks potential fit instead of deciding whether
    a discovered business should be shown at all.
    """

    if not businesses:
        return []

    businesses_for_ai = businesses[:50]

    business_data = []

    for index, business in enumerate(
        businesses_for_ai,
        start=1,
    ):

        business_data.append(
            {
                "lead_number": index,
                "name": business.get("name", ""),
                "industry": business.get("industry", ""),
                "address": business.get("address", ""),
                "website": business.get("website", ""),
                "phone": business.get("phone", ""),
                "source": business.get("source", ""),
            }
        )

    prompt = f"""
You are an AI lead qualification system.

Your job is NOT to decide whether these businesses are real.
They have already been discovered from a real business directory.

Your job is to rank which businesses appear most relevant
to the salesperson's target customer.

SALESPERSON BUSINESS:
{business_type}

TARGET CUSTOMER:
{customer_type}

TARGET LOCATION:
{location}

BUSINESS RECORDS:
{json.dumps(business_data, indent=2)}

Instructions:

1. Evaluate the businesses based ONLY on the information provided.
2. Do not invent owners, employees, revenue, customers, decision-makers,
   company size, or business problems.
3. A potential need must be described as a possibility.
4. Prefer businesses whose industry clearly matches the target.
5. Having a website, phone number, address, or other useful contact
   information can increase practical lead quality.
6. Do not require every field to be present.
7. Return up to 15 of the most relevant businesses.
8. relevance_score must be an integer from 1 to 100.
9. Even if information is limited, include businesses that are
   reasonably relevant rather than returning an empty list.
10. A score represents potential relevance, NOT certainty.
11. Use the exact lead_number from the records.

Return ONLY valid JSON using this exact structure:

{{
    "leads": [
        {{
            "lead_number": 1,
            "relevance_score": 85,
            "reason": "The business appears relevant because its listed industry matches the target market.",
            "potential_need": "Possible business need related to the salesperson's stated offering."
        }}
    ]
}}
"""

    result = generate_json_response(prompt)

    if not isinstance(result, dict):
        return []

    ai_leads = result.get(
        "leads",
        [],
    )

    if not isinstance(ai_leads, list):
        return []

    qualified = []

    for item in ai_leads:

        if not isinstance(item, dict):
            continue

        try:
            lead_number = int(
                item.get(
                    "lead_number",
                    0,
                )
            )

            score = int(
                item.get(
                    "relevance_score",
                    0,
                )
            )

        except (
            ValueError,
            TypeError,
        ):
            continue

        if (
            lead_number < 1
            or lead_number > len(businesses_for_ai)
        ):
            continue

        score = max(
            1,
            min(score, 100),
        )

        business = businesses_for_ai[
            lead_number - 1
        ]

        qualified.append(
            {
                **business,
                "relevance_score": score,
                "reason": str(
                    item.get(
                        "reason",
                        "Potential relevance based on available business information.",
                    )
                ),
                "potential_need": str(
                    item.get(
                        "potential_need",
                        "Potential need should be confirmed through outreach.",
                    )
                ),
            }
        )

    qualified.sort(
        key=lambda lead: lead[
            "relevance_score"
        ],
        reverse=True,
    )

    return qualified


# ============================================================
# AI LEAD QUALIFICATION
# ============================================================

def qualify_lead(
    lead: sqlite3.Row,
) -> Optional[Dict[str, Any]]:
    """
    Generate a structured qualification report.
    """

    prompt = f"""
You are an AI sales qualification assistant.

Analyze the following potential lead.

LEAD NAME:
{lead["name"]}

COMPANY:
{lead["company"]}

INDUSTRY:
{lead["industry"]}

ADDRESS:
{lead["address"]}

WEBSITE:
{lead["website"]}

PHONE:
{lead["phone"]}

POTENTIAL NEED:
{lead["problem"]}

Evaluate ONLY the information provided.

Important rules:

- Never assume the contact is the owner.
- Never assume the contact is a decision-maker.
- Never invent company information.
- Clearly separate facts from assumptions.
- Potential pain points are hypotheses, not facts.
- The score must reflect information quality and potential
  relevance, not certainty.

Return ONLY valid JSON:

{{
    "score": 1,
    "summary": "Short explanation.",
    "known_information": [
        "Fact explicitly provided."
    ],
    "unknown_information": [
        "Important information not provided."
    ],
    "potential_pain_points": [
        "Possible pain point."
    ],
    "qualification_questions": [
        "Question to ask."
    ],
    "next_action": "One practical next step."
}}
"""

    result = generate_json_response(prompt)

    if not isinstance(result, dict):
        return None

    try:

        score = int(
            result.get(
                "score",
                0,
            )
        )

    except (
        ValueError,
        TypeError,
    ):

        score = 0

    score = max(
        1,
        min(score, 100),
    )

    result["score"] = score

    return result


# ============================================================
# AI OUTREACH
# ============================================================

def generate_outreach(
    lead: sqlite3.Row,
) -> Optional[Dict[str, Any]]:
    """
    Generate personalized outreach without inventing
    company information.
    """

    qualification = (
        lead["qualification"]
        if lead["qualification"]
        else "No AI qualification has been completed."
    )

    prompt = f"""
You are an AI sales assistant.

Create professional outreach for this potential lead.

CONTACT:
{lead["name"]}

COMPANY:
{lead["company"]}

INDUSTRY:
{lead["industry"]}

POTENTIAL NEED:
{lead["problem"]}

PREVIOUS AI QUALIFICATION:
{qualification}

Rules:

- Use only known information.
- Do not invent company facts.
- Do not claim the person is the owner or decision-maker.
- Do not use fake personalization.
- Keep the message short and natural.
- Avoid generic AI sales language.

Return ONLY valid JSON:

{{
    "first_message": "Short personalized message.",
    "follow_up": "Short follow-up message.",
    "qualification_questions": [
        "Question 1",
        "Question 2",
        "Question 3"
    ],
    "next_step": "Suggested next step."
}}
"""

    result = generate_json_response(prompt)

    if not isinstance(result, dict):
        return None

    return result


# ============================================================
# AI FOLLOW-UP
# ============================================================

def generate_follow_up(
    lead: sqlite3.Row,
) -> Optional[Dict[str, Any]]:
    """
    Generate a structured follow-up plan.
    """

    prompt = f"""
You are an AI sales assistant.

Create a practical follow-up plan.

LEAD:
{lead["name"]}

COMPANY:
{lead["company"]}

POTENTIAL NEED:
{lead["problem"]}

CURRENT STATUS:
{lead["status"]}

Rules:

- Do not invent company information.
- Do not assume the recipient is the decision-maker.
- Keep the plan realistic and concise.

Return ONLY valid JSON:

{{
    "timing": "Reasonable follow-up timeframe.",
    "message": "Short follow-up message.",
    "purpose": "What the follow-up should accomplish.",
    "next_action": "Next practical action."
}}
"""

    result = generate_json_response(prompt)

    if not isinstance(result, dict):
        return None

    return result


# ============================================================
# BUSINESS STRATEGY
# ============================================================

def generate_business_strategy(
    business: str,
    goal: str,
) -> Optional[Dict[str, Any]]:
    """
    Generate a structured lead-generation strategy.
    """

    prompt = f"""
You are an AI lead-generation strategist.

BUSINESS:
{business}

BUSINESS GOAL:
{goal}

Create a practical lead-generation strategy.

Avoid generic advice.

Return ONLY valid JSON:

{{
    "ideal_customer": "Specific customer profile.",
    "lead_sources": [
        "Specific lead source."
    ],
    "outreach_strategy": "How to approach prospects.",
    "personalized_outreach": "Realistic first message.",
    "follow_up": "Follow-up message.",
    "qualification_questions": [
        "Question 1",
        "Question 2",
        "Question 3"
    ],
    "next_actions": [
        "Action 1",
        "Action 2",
        "Action 3",
        "Action 4",
        "Action 5"
    ]
}}
"""

    result = generate_json_response(prompt)

    if not isinstance(result, dict):
        return None

    return result


# ============================================================
# INITIALIZE DATABASE
# ============================================================

create_database()
migrate_database()


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_status_counts(
    leads: List[sqlite3.Row],
) -> Dict[str, int]:
    """
    Calculate pipeline counts.
    """

    return {
        status: sum(
            lead["status"] == status
            for lead in leads
        )
        for status in PIPELINE_STATUSES
    }


def get_average_score(
    leads: List[sqlite3.Row],
) -> Optional[int]:
    """
    Calculate average AI lead score.
    """

    scores = [
        lead["lead_score"]
        for lead in leads
        if lead["lead_score"] is not None
    ]

    if not scores:
        return None

    return round(
        sum(scores) / len(scores)
    )


def render_connection_status(
    label: str,
    connected: bool,
) -> None:
    """
    Display a simple application connection indicator.
    """

    if connected:

        st.caption(
            f"{label}: Connected"
        )

    else:

        st.caption(
            f"{label}: Not configured"
        )


def render_lead_card(
    lead: sqlite3.Row,
    compact: bool = False,
) -> None:
    """
    Render a reusable lead card.
    """

    lead_id = lead["id"]

    with st.container(
        border=True,
    ):

        top_col, score_col = st.columns(
            [4, 1]
        )

        with top_col:

            st.markdown(
                f'<div class="lead-title">{lead["company"]}</div>',
                unsafe_allow_html=True,
            )

            if lead["name"]:

                st.caption(
                    lead["name"]
                )

            metadata = []

            if lead["industry"]:
                metadata.append(
                    lead["industry"]
                )

            if lead["address"]:
                metadata.append(
                    lead["address"]
                )

            if metadata:

                st.caption(
                    " | ".join(metadata)
                )

        with score_col:

            if lead["lead_score"] is not None:

                st.metric(
                    "AI Score",
                    f'{lead["lead_score"]}/100',
                )

        if not compact:

            if lead["problem"]:

                st.write(
                    f'**Potential Need:** {lead["problem"]}'
                )

            if lead["source"]:

                st.caption(
                    f'Source: {lead["source"]}'
                )

        action_col1, action_col2 = st.columns(
            2
        )

        with action_col1:

            status_index = (
                PIPELINE_STATUSES.index(
                    lead["status"]
                )
                if lead["status"] in PIPELINE_STATUSES
                else 0
            )

            selected_status = st.selectbox(
                "Status",
                PIPELINE_STATUSES,
                index=status_index,
                key=f"card_status_{lead_id}",
            )

            if selected_status != lead["status"]:

                update_status(
                    lead_id,
                    selected_status,
                )

                st.rerun()

        with action_col2:

            if lead["website"]:

                st.link_button(
                    "Open Website",
                    lead["website"],
                    use_container_width=True,
                )


# ============================================================
# SIDEBAR NAVIGATION
# ============================================================

with st.sidebar:

    st.markdown(
        f"## {APP_NAME}"
    )

    st.caption(
        "Lead discovery, qualification, outreach, "
        "and pipeline management."
    )

    st.divider()

    st.markdown(
        '<div class="eyebrow">Workspace</div>',
        unsafe_allow_html=True,
    )

    page = st.radio(
        "Navigation",
        [
            "Dashboard",
            "Find Leads",
            "Pipeline",
            "AI Tools",
            "Strategy",
        ],
        index=[
            "Dashboard",
            "Find Leads",
            "Pipeline",
            "AI Tools",
            "Strategy",
        ].index(
            st.session_state.page
        ),
        label_visibility="collapsed",
    )

    st.session_state.page = page

    st.divider()

    st.markdown(
        '<div class="eyebrow">System</div>',
        unsafe_allow_html=True,
    )

    render_connection_status(
        "Gemini",
        client is not None,
    )

    render_connection_status(
        "Lead database",
        True,
    )

    render_connection_status(
        "Business search",
        True,
    )

    st.divider()

    st.session_state.debug_mode = st.checkbox(
        "Debug mode",
        value=st.session_state.debug_mode,
    )

    st.caption(
        f"Version {APP_VERSION}"
    )


# ============================================================
# LOAD LEADS
# ============================================================

leads = get_leads()

status_counts = get_status_counts(
    leads
)

average_score = get_average_score(
    leads
)


# ============================================================
# DASHBOARD
# ============================================================

if page == "Dashboard":

    st.title("Dashboard")

    st.markdown(
        "### Turn business targets into qualified opportunities."
    )

    st.write(
        "Discover real businesses, evaluate potential opportunities, "
        "generate personalized outreach, and manage the sales pipeline "
        "from one workspace."
    )

    st.divider()

    metric_col1, metric_col2, metric_col3, metric_col4 = (
        st.columns(4)
    )

    with metric_col1:

        st.metric(
            "Total Leads",
            len(leads),
        )

    with metric_col2:

        st.metric(
            "Interested",
            status_counts["Interested"],
        )

    with metric_col3:

        st.metric(
            "Meetings",
            status_counts["Meeting"],
        )

    with metric_col4:

        st.metric(
            "Won",
            status_counts["Won"],
        )

    st.divider()

    left_col, right_col = st.columns(
        [1.4, 1]
    )

    with left_col:

        st.subheader(
            "Pipeline"
        )

        pipeline_col1, pipeline_col2, pipeline_col3 = (
            st.columns(3)
        )

        with pipeline_col1:

            st.metric(
                "New",
                status_counts["New"],
            )

        with pipeline_col2:

            st.metric(
                "Contacted",
                status_counts["Contacted"],
            )

        with pipeline_col3:

            st.metric(
                "Lost",
                status_counts["Lost"],
            )

        if leads:

            st.subheader(
                "Recent Leads"
            )

            for lead in leads[:5]:

                render_lead_card(
                    lead,
                    compact=True,
                )

        else:

            st.info(
                "Your pipeline is empty. "
                "Use Find Leads to discover businesses."
            )

    with right_col:

        st.subheader(
            "AI Performance"
        )

        if average_score is not None:

            st.metric(
                "Average Lead Score",
                f"{average_score}/100",
            )

        else:

            st.metric(
                "Average Lead Score",
                "—",
            )

        st.write(
            "AI scoring is based on the information available "
            "for each lead."
        )

        st.divider()

        st.subheader(
            "Lead Sources"
        )

        source_counts = {}

        for lead in leads:

            source = (
                lead["source"]
                or "Unknown"
            )

            source_counts[source] = (
                source_counts.get(
                    source,
                    0,
                ) + 1
            )

        if source_counts:

            for source, count in sorted(
                source_counts.items(),
                key=lambda item: item[1],
                reverse=True,
            ):

                st.write(
                    f"**{source}** — {count}"
                )

        else:

            st.caption(
                "Lead source data will appear here."
            )

    st.divider()

    st.subheader(
        "Workflow"
    )

    workflow_col1, workflow_col2, workflow_col3, workflow_col4 = (
        st.columns(4)
    )

    with workflow_col1:

        st.markdown(
            "**01 — Discover**"
        )

        st.caption(
            "Search real business records using a target market and location."
        )

    with workflow_col2:

        st.markdown(
            "**02 — Qualify**"
        )

        st.caption(
            "Use AI to evaluate relevance and identify missing information."
        )

    with workflow_col3:

        st.markdown(
            "**03 — Personalize**"
        )

        st.caption(
            "Generate outreach using only known lead information."
        )

    with workflow_col4:

        st.markdown(
            "**04 — Track**"
        )

        st.caption(
            "Move opportunities through a simple sales pipeline."
        )


# ============================================================
# FIND LEADS
# ============================================================

elif page == "Find Leads":

    st.title("Find Leads")

    st.markdown(
        "### Discover real businesses in a target market."
    )

    st.write(
        "Search OpenStreetMap business records, then use Gemini "
        "to rank potential customer fit."
    )

    st.divider()

    search_col1, search_col2 = st.columns(2)

    with search_col1:

        search_business = st.text_input(
            "What does your business sell?",
            placeholder="Example: Roofing services",
            key="search_business_v3",
        )

    with search_col2:

        customer_type = st.text_input(
            "Who are you trying to reach?",
            placeholder="Example: Property managers",
            key="customer_type_v3",
        )

    search_location = st.text_input(
        "Target location",
        placeholder="Example: Raleigh, North Carolina",
        key="search_location_v3",
    )

    radius_col1, radius_col2 = st.columns(
        [2, 1]
    )

    with radius_col1:

        search_radius = st.slider(
            "Search radius",
            min_value=2000,
            max_value=25000,
            value=12000,
            step=1000,
            format="%d meters",
        )

    with radius_col2:

        st.markdown(
            "#### Search source"
        )

        st.caption(
            "OpenStreetMap + Overpass"
        )

    if st.button(
        "Find Real Leads",
        use_container_width=True,
        type="primary",
    ):

        if not all(
            [
                search_business.strip(),
                customer_type.strip(),
                search_location.strip(),
            ]
        ):

            st.warning(
                "Enter your business, target customer, "
                "and target location."
            )

        else:

            with st.spinner(
                "Searching business records..."
            ):

                try:

                    raw_businesses = search_real_businesses(
                        search_location,
                        search_radius,
                    )

                    st.session_state.last_search_location = (
                        search_location
                    )

                    st.session_state.last_search_count = (
                        len(raw_businesses)
                    )

                    st.session_state.discovered_businesses = (
                        raw_businesses
                    )

                except Exception as error:

                    raw_businesses = []

                    st.error(
                        "The business search could not be completed."
                    )

                    if st.session_state.debug_mode:

                        st.exception(
                            error
                        )

            if raw_businesses:

                st.success(
                    f"Found {len(raw_businesses)} business records."
                )

                with st.spinner(
                    "Evaluating potential customer fit..."
                ):

                    qualified_leads = qualify_search_results(
                        raw_businesses,
                        search_business,
                        customer_type,
                        search_location,
                    )

                if qualified_leads:

                    st.session_state.qualified_leads = (
                        qualified_leads
                    )

                else:

                    st.session_state.qualified_leads = []

                    st.warning(
                        "The AI could not confidently rank the businesses. "
                        "The discovered businesses are still available below."
                    )

            else:

                st.session_state.qualified_leads = []

                st.warning(
                    "No named businesses were found. "
                    "Try a larger radius or a nearby city."
                )

    # ========================================================
    # AI-RANKED PROSPECTS
    # ========================================================

    if st.session_state.qualified_leads:

        st.divider()

        st.subheader(
            "AI-Ranked Prospects"
        )

        st.caption(
            f"{len(st.session_state.qualified_leads)} "
            "potential prospects ranked by AI."
        )

        for index, lead in enumerate(
            st.session_state.qualified_leads
        ):

            with st.container(
                border=True,
            ):

                result_col1, result_col2 = st.columns(
                    [4, 1]
                )

                with result_col1:

                    st.markdown(
                        f"### {lead['name']}"
                    )

                    metadata = []

                    if lead["industry"]:

                        metadata.append(
                            lead["industry"]
                        )

                    if lead["address"]:

                        metadata.append(
                            lead["address"]
                        )

                    if metadata:

                        st.caption(
                            " | ".join(metadata)
                        )

                    if lead["reason"]:

                        st.write(
                            "**Why it may be relevant**"
                        )

                        st.write(
                            lead["reason"]
                        )

                    if lead["potential_need"]:

                        st.write(
                            "**Potential opportunity**"
                        )

                        st.write(
                            lead["potential_need"]
                        )

                    contact_info = []

                    if lead["phone"]:

                        contact_info.append(
                            f"Phone: {lead['phone']}"
                        )

                    if lead["website"]:

                        contact_info.append(
                            "Website available"
                        )

                    if contact_info:

                        st.caption(
                            " | ".join(contact_info)
                        )

                    st.caption(
                        f"Source: {lead.get('source', 'Unknown')}"
                    )

                with result_col2:

                    st.metric(
                        "AI Relevance",
                        f"{lead['relevance_score']}/100",
                    )

                button_col1, button_col2 = st.columns(
                    2
                )

                with button_col1:

                    if st.button(
                        "Add to Pipeline",
                        key=f"add_search_{index}",
                        use_container_width=True,
                    ):

                        added = add_lead(
                            name="Unknown Contact",
                            company=lead["name"],
                            problem=lead[
                                "potential_need"
                            ],
                            website=lead[
                                "website"
                            ],
                            phone=lead[
                                "phone"
                            ],
                            address=lead[
                                "address"
                            ],
                            industry=lead[
                                "industry"
                            ],
                            source=lead[
                                "source"
                            ],
                        )

                        if added:

                            st.success(
                                "Added to pipeline."
                            )

                        else:

                            st.info(
                                "This business is already in the pipeline."
                            )

                with button_col2:

                    if lead["website"]:

                        st.link_button(
                            "Open Website",
                            lead["website"],
                            use_container_width=True,
                        )

    # ========================================================
    # DISCOVERED BUSINESSES
    # ========================================================

    if st.session_state.discovered_businesses:

        st.divider()

        st.subheader(
            "Discovered Businesses"
        )

        st.caption(
            "Businesses returned directly from OpenStreetMap. "
            "These have not been filtered out by AI."
        )

        discovered = st.session_state.discovered_businesses

        for index, business in enumerate(
            discovered[:100]
        ):

            with st.container(
                border=True,
            ):

                business_col1, business_col2 = st.columns(
                    [4, 1]
                )

                with business_col1:

                    st.markdown(
                        f"**{business['name']}**"
                    )

                    metadata = []

                    if business["industry"]:

                        metadata.append(
                            business["industry"]
                        )

                    if business["address"]:

                        metadata.append(
                            business["address"]
                        )

                    if metadata:

                        st.caption(
                            " | ".join(metadata)
                        )

                    contact_info = []

                    if business["phone"]:

                        contact_info.append(
                            f"Phone: {business['phone']}"
                        )

                    if business["website"]:

                        contact_info.append(
                            "Website available"
                        )

                    if contact_info:

                        st.caption(
                            " | ".join(contact_info)
                        )

                with business_col2:

                    if business["website"]:

                        st.link_button(
                            "Website",
                            business["website"],
                            use_container_width=True,
                        )


# ============================================================
# PIPELINE
# ============================================================

elif page == "Pipeline":

    st.title("Lead Pipeline")

    st.markdown(
        "### Manage opportunities from first contact to close."
    )

    st.divider()

    pipeline_metrics = st.columns(
        6
    )

    for index, status in enumerate(
        PIPELINE_STATUSES
    ):

        with pipeline_metrics[index]:

            st.metric(
                status,
                status_counts[status],
            )

    st.divider()

    if not leads:

        st.info(
            "No leads in the pipeline yet. "
            "Use Find Leads or add a lead manually."
        )

    else:

        filter_col1, filter_col2 = st.columns(
            2
        )

        with filter_col1:

            selected_status_filter = st.selectbox(
                "Filter by status",
                ["All"] + PIPELINE_STATUSES,
            )

        with filter_col2:

            search_pipeline = st.text_input(
                "Search pipeline",
                placeholder="Company or contact name",
            )

        filtered_leads = leads

        if selected_status_filter != "All":

            filtered_leads = [
                lead
                for lead in filtered_leads
                if lead["status"] == selected_status_filter
            ]

        if search_pipeline.strip():

            query = search_pipeline.lower().strip()

            filtered_leads = [
                lead
                for lead in filtered_leads
                if query in lead["company"].lower()
                or query in lead["name"].lower()
            ]

        st.caption(
            f"Showing {len(filtered_leads)} leads."
        )

        for lead in filtered_leads:

            render_lead_card(
                lead
            )


# ============================================================
# AI TOOLS
# ============================================================

elif page == "AI Tools":

    st.title("AI Tools")

    st.markdown(
        "### Analyze, personalize, and follow up on leads."
    )

    st.divider()

    if not leads:

        st.info(
            "Add a lead before using the AI tools."
        )

    else:

        lead_options = {
            f"{lead['company']} — {lead['name']}": lead["id"]
            for lead in leads
        }

        selected_label = st.selectbox(
            "Select a lead",
            list(lead_options.keys()),
        )

        selected_lead_id = lead_options[
            selected_label
        ]

        selected_lead = next(
            lead
            for lead in leads
            if lead["id"] == selected_lead_id
        )

        st.divider()

        detail_col1, detail_col2 = st.columns(
            [3, 1]
        )

        with detail_col1:

            st.subheader(
                selected_lead["company"]
            )

            st.caption(
                selected_lead["name"]
            )

            if selected_lead["industry"]:

                st.write(
                    f"**Industry:** {selected_lead['industry']}"
                )

            if selected_lead["address"]:

                st.write(
                    f"**Location:** {selected_lead['address']}"
                )

            if selected_lead["problem"]:

                st.write(
                    f"**Potential Need:** "
                    f"{selected_lead['problem']}"
                )

        with detail_col2:

            st.metric(
                "Current Status",
                selected_lead["status"],
            )

            if selected_lead["lead_score"] is not None:

                st.metric(
                    "AI Score",
                    f"{selected_lead['lead_score']}/100",
                )

        st.divider()

        tool_tab1, tool_tab2, tool_tab3 = st.tabs(
            [
                "Qualification",
                "Outreach",
                "Follow-Up",
            ]
        )

        # ----------------------------------------------------
        # QUALIFICATION
        # ----------------------------------------------------

        with tool_tab1:

            st.subheader(
                "AI Qualification"
            )

            if st.button(
                "Analyze Lead",
                use_container_width=True,
                type="primary",
            ):

                with st.spinner(
                    "Analyzing available lead information..."
                ):

                    qualification = qualify_lead(
                        selected_lead
                    )

                if qualification:

                    score = qualification[
                        "score"
                    ]

                    qualification_text = json.dumps(
                        qualification,
                        indent=2,
                    )

                    save_qualification(
                        selected_lead["id"],
                        qualification_text,
                        score,
                        qualification.get(
                            "next_action",
                            "",
                        ),
                    )

                    st.success(
                        "Qualification saved."
                    )

                    st.rerun()

            refreshed_leads = get_leads()

            current_lead = next(
                (
                    lead
                    for lead in refreshed_leads
                    if lead["id"] == selected_lead_id
                ),
                None,
            )

            if current_lead and current_lead["qualification"]:

                try:

                    qualification_data = json.loads(
                        current_lead["qualification"]
                    )

                except (
                    json.JSONDecodeError,
                    TypeError,
                ):

                    qualification_data = None

                if isinstance(
                    qualification_data,
                    dict,
                ):

                    score = qualification_data.get(
                        "score",
                        current_lead["lead_score"],
                    )

                    score_col, summary_col = st.columns(
                        [1, 3]
                    )

                    with score_col:

                        st.metric(
                            "Lead Score",
                            f"{score}/100",
                        )

                    with summary_col:

                        st.write(
                            "**Assessment**"
                        )

                        st.write(
                            qualification_data.get(
                                "summary",
                                "",
                            )
                        )

                    st.divider()

                    info_col1, info_col2 = st.columns(
                        2
                    )

                    with info_col1:

                        st.write(
                            "**Known Information**"
                        )

                        for item in qualification_data.get(
                            "known_information",
                            [],
                        ):

                            st.write(
                                f"- {item}"
                            )

                        st.write(
                            "**Potential Pain Points**"
                        )

                        for item in qualification_data.get(
                            "potential_pain_points",
                            [],
                        ):

                            st.write(
                                f"- {item}"
                            )

                    with info_col2:

                        st.write(
                            "**Unknown Information**"
                        )

                        for item in qualification_data.get(
                            "unknown_information",
                            [],
                        ):

                            st.write(
                                f"- {item}"
                            )

                        st.write(
                            "**Qualification Questions**"
                        )

                        for item in qualification_data.get(
                            "qualification_questions",
                            [],
                        ):

                            st.write(
                                f"- {item}"
                            )

                    st.divider()

                    st.write(
                        "**Recommended Next Action**"
                    )

                    st.info(
                        qualification_data.get(
                            "next_action",
                            "No next action provided.",
                        )
                    )

                else:

                    with st.expander(
                        "View stored qualification"
                    ):

                        st.write(
                            current_lead["qualification"]
                        )

        # ----------------------------------------------------
        # OUTREACH
        # ----------------------------------------------------

        with tool_tab2:

            st.subheader(
                "Personalized Outreach"
            )

            st.write(
                "Generate outreach from the information currently "
                "stored for this lead."
            )

            if st.button(
                "Generate Outreach",
                use_container_width=True,
                type="primary",
            ):

                with st.spinner(
                    "Creating personalized outreach..."
                ):

                    outreach = generate_outreach(
                        selected_lead
                    )

                if outreach:

                    message_col1, message_col2 = st.columns(
                        2
                    )

                    with message_col1:

                        st.write(
                            "**First Message**"
                        )

                        st.text_area(
                            "First message",
                            outreach.get(
                                "first_message",
                                "",
                            ),
                            height=180,
                            label_visibility="collapsed",
                        )

                    with message_col2:

                        st.write(
                            "**Follow-Up**"
                        )

                        st.text_area(
                            "Follow-up",
                            outreach.get(
                                "follow_up",
                                "",
                            ),
                            height=180,
                            label_visibility="collapsed",
                        )

                    st.divider()

                    st.write(
                        "**Qualification Questions**"
                    )

                    for question in outreach.get(
                        "qualification_questions",
                        [],
                    ):

                        st.write(
                            f"- {question}"
                        )

                    st.write(
                        "**Suggested Next Step**"
                    )

                    st.info(
                        outreach.get(
                            "next_step",
                            "",
                        )
                    )

        # ----------------------------------------------------
        # FOLLOW-UP
        # ----------------------------------------------------

        with tool_tab3:

            st.subheader(
                "Follow-Up Plan"
            )

            if st.button(
                "Create Follow-Up Plan",
                use_container_width=True,
                type="primary",
            ):

                with st.spinner(
                    "Creating follow-up plan..."
                ):

                    follow_up = generate_follow_up(
                        selected_lead
                    )

                if follow_up:

                    follow_up_text = json.dumps(
                        follow_up,
                        indent=2,
                    )

                    save_follow_up(
                        selected_lead["id"],
                        follow_up_text,
                    )

                    st.success(
                        "Follow-up plan saved."
                    )

                    st.rerun()

            refreshed_leads = get_leads()

            current_lead = next(
                (
                    lead
                    for lead in refreshed_leads
                    if lead["id"] == selected_lead_id
                ),
                None,
            )

            if current_lead and current_lead["follow_up"]:

                try:

                    follow_up_data = json.loads(
                        current_lead["follow_up"]
                    )

                except (
                    json.JSONDecodeError,
                    TypeError,
                ):

                    follow_up_data = None

                if isinstance(
                    follow_up_data,
                    dict,
                ):

                    st.write(
                        "**Timing**"
                    )

                    st.info(
                        follow_up_data.get(
                            "timing",
                            "",
                        )
                    )

                    st.write(
                        "**Message**"
                    )

                    st.text_area(
                        "Follow-up message",
                        follow_up_data.get(
                            "message",
                            "",
                        ),
                        height=150,
                        label_visibility="collapsed",
                    )

                    st.write(
                        "**Purpose**"
                    )

                    st.write(
                        follow_up_data.get(
                            "purpose",
                            "",
                        )
                    )

                    st.write(
                        "**Next Action**"
                    )

                    st.info(
                        follow_up_data.get(
                            "next_action",
                            "",
                        )
                    )

                else:

                    st.write(
                        current_lead["follow_up"]
                    )


# ============================================================
# BUSINESS STRATEGY
# ============================================================

elif page == "Strategy":

    st.title("Business Strategy")

    st.markdown(
        "### Build a lead-generation plan around a specific business goal."
    )

    st.write(
        "Use Gemini to turn a business type and measurable goal "
        "into a practical customer-acquisition workflow."
    )

    st.divider()

    strategy_col1, strategy_col2 = st.columns(
        2
    )

    with strategy_col1:

        business = st.text_input(
            "Business Type",
            placeholder="Example: Local roofing company",
            key="strategy_business_v3",
        )

    with strategy_col2:

        goal = st.text_input(
            "Business Goal",
            placeholder="Example: Get 20 new customers this month",
            key="strategy_goal_v3",
        )

    if st.button(
        "Generate Lead Strategy",
        use_container_width=True,
        type="primary",
    ):

        if not business.strip() or not goal.strip():

            st.warning(
                "Enter a business type and business goal."
            )

        else:

            with st.spinner(
                "Building lead strategy..."
            ):

                strategy = generate_business_strategy(
                    business,
                    goal,
                )

            if strategy:

                st.divider()

                st.subheader(
                    "Generated Strategy"
                )

                ideal_col, source_col = st.columns(
                    2
                )

                with ideal_col:

                    st.write(
                        "**Ideal Customer**"
                    )

                    st.write(
                        strategy.get(
                            "ideal_customer",
                            "",
                        )
                    )

                with source_col:

                    st.write(
                        "**Lead Sources**"
                    )

                    for source in strategy.get(
                        "lead_sources",
                        [],
                    ):

                        st.write(
                            f"- {source}"
                        )

                st.divider()

                st.write(
                    "**Outreach Strategy**"
                )

                st.write(
                    strategy.get(
                        "outreach_strategy",
                        "",
                    )
                )

                st.divider()

                outreach_col1, outreach_col2 = st.columns(
                    2
                )

                with outreach_col1:

                    st.write(
                        "**Personalized Outreach**"
                    )

                    st.text_area(
                        "Generated outreach",
                        strategy.get(
                            "personalized_outreach",
                            "",
                        ),
                        height=180,
                        label_visibility="collapsed",
                    )

                with outreach_col2:

                    st.write(
                        "**Follow-Up**"
                    )

                    st.text_area(
                        "Generated follow-up",
                        strategy.get(
                            "follow_up",
                            "",
                        ),
                        height=180,
                        label_visibility="collapsed",
                    )

                st.divider()

                qualification_col, actions_col = st.columns(
                    2
                )

                with qualification_col:

                    st.write(
                        "**Qualification Questions**"
                    )

                    for question in strategy.get(
                        "qualification_questions",
                        [],
                    ):

                        st.write(
                            f"- {question}"
                        )

                with actions_col:

                    st.write(
                        "**Next Actions**"
                    )

                    for action in strategy.get(
                        "next_actions",
                        [],
                    ):

                        st.write(
                            f"- {action}"
                        )


# ============================================================
# FOOTER
# ============================================================

st.divider()

footer_col1, footer_col2 = st.columns(
    2
)

with footer_col1:

    st.caption(
        f"{APP_NAME} v{APP_VERSION}"
    )

with footer_col2:

    st.caption(
        "Python | Streamlit | Gemini | "
        "OpenStreetMap | Overpass | SQLite"
    )