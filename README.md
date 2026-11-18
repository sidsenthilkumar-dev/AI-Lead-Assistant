# ai lead assistant

a python and streamlit app for finding businesses, reviewing leads, drafting outreach, and keeping track of follow-ups.

## what it does

- searches for businesses by type and location using openstreetmap and the overpass api
- uses gemini to suggest lead scores and explain the reasoning
- drafts first-contact and follow-up messages for review
- stores leads in sqlite and tracks them through the sales pipeline

the workflow goes from finding a business to reviewing its information, writing a draft, and tracking the next step. ai scores are suggestions, so check the business details before using them.

## stack

python, streamlit, sqlite, requests, gemini, and openstreetmap.
