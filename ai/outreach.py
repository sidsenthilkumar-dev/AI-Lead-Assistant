from ai.provider import generate


def generate_outreach(
    target_business,
    lead,
):
    prompt = f"""
You create professional B2B outreach messages.

SELLING BUSINESS:
{target_business}

POTENTIAL CUSTOMER:
Company: {lead.get("company", "")}
Industry: {lead.get("industry", "")}
Website: {lead.get("website", "")}
Address: {lead.get("address", "")}

KNOWN OPPORTUNITY:
{lead.get("problem", "")}

Write a short first-contact message.

Requirements:

- Natural
- Professional
- Specific
- No fake claims
- No exaggerated promises
- Do not pretend you spoke with the company before
- Do not mention that AI wrote the message
- Keep it concise
"""

    return generate(prompt)


def generate_follow_up(
    target_business,
    lead,
):
    prompt = f"""
Write a short professional follow-up message.

Selling business:
{target_business}

Potential customer:
{lead.get("company", "")}

Previous opportunity:
{lead.get("problem", "")}

The customer has not responded.

Write a helpful follow-up.
Do not sound desperate.
Do not use fake urgency.
Keep it concise.
"""

    return generate(prompt)