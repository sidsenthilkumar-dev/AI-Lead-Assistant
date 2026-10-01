LEAD_QUALIFICATION_PROMPT = """
You are an AI customer acquisition assistant.

Analyze the following potential customer.

Company:
{company}

Industry:
{industry}

Problem or opportunity:
{problem}

Determine:

1. Qualification score from 1-100
2. Why this company could be valuable
3. What the business should do next
4. A personalized outreach angle

Be specific and practical.
"""


OUTREACH_PROMPT = """
Create a short, natural business outreach message.

Company:
{company}

Industry:
{industry}

Potential opportunity:
{problem}

The message should feel personalized,
professional, and human.

Avoid generic marketing language.
"""