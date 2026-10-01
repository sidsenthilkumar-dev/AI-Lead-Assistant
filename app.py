import streamlit as st
from google import genai

# Set up Gemini
client = genai.Client(
    api_key=st.secrets["GEMINI_API_KEY"]
)

# app title
st.title("AI Lead Assistant")
st.write("Generate a lead strategy for your business.")

# Get information from the user
business = st.text_input(
    "Business",
    placeholder="Example: Local roofing company"
)

goal = st.text_input(
    "Goal",
    placeholder="Example: Get 20 new customers this month"
)

# Generate the strategy
if st.button("Generate Lead Strategy"):

    if not business or not goal:
        st.warning("Please enter both fields.")

    else:
        prompt = f"""
You are an AI lead-generation assistant helping small businesses get more customers.

Business: {business}
Goal: {goal}

Create a specific, actionable lead-generation plan.

Include:

1. Ideal Customer
Describe exactly who the business should target.

2. Where to Find Leads
Give specific places, platforms, websites, or types of businesses where potential customers can be found.

3. Personalized First Outreach
Write a short message that could actually be sent to a potential customer.

4. Follow-Up Message
Write a follow-up message to send if they do not respond.

5. Lead Qualification Questions
Give 3 questions that help determine whether a lead is a good potential customer.

6. Action Plan
Give 5 specific actions the business owner should take today to start getting leads.

Make the advice practical and specific to the business.
Avoid generic advice.
"""

        try:
            response = client.models.generate_content(
                model="gemini-3.7-flash",
                contents=prompt
            )

            st.subheader("Your AI Lead Strategy")
            st.write(response.text)

        except Exception:
            st.error(
                "Gemini is temporarily unavailable. "
                "Please try again in a few minutes."
            )
