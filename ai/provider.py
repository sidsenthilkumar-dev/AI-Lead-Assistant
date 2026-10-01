import streamlit as st
from google import genai


MODEL_NAMES = [
    "gemini-3.8-flash",
    "gemini-3.5-flash",
]


def get_client():
    return genai.Client(
        api_key=st.secrets["GEMINI_API_KEY"]
    )


def generate(prompt: str) -> str:

    client = get_client()

    last_error = None

    for model_name in MODEL_NAMES:

        try:

            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
            )

            return response.text

        except Exception as e:

            last_error = e

    raise last_error