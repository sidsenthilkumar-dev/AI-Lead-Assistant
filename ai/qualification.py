import json

from ai.provider import generate


def qualify_lead(
    business,
    target_business,
    business_goal,
):
    prompt = f"""
You are an AI sales qualification system.

A business is trying to find potential customers.

SELLING BUSINESS:
{target_business}

BUSINESS GOAL:
{business_goal}

POTENTIAL CUSTOMER:
Company: {business.get("company", "")}
Industry: {business.get("industry", "")}
Website: {business.get("website", "")}
Phone: {business.get("phone", "")}
Address: {business.get("address", "")}

Evaluate whether this potential customer could be relevant.

Return ONLY valid JSON:

{{
    "score": 0,
    "qualification": "",
    "problem": "",
    "next_action": ""
}}

Scoring guidelines:

90-100 = very strong potential fit
75-89 = strong potential fit
60-74 = possible fit
40-59 = weak fit
0-39 = unlikely fit

Do not invent facts.

If information is unknown, say that it is unknown.
"""

    response = generate(prompt)

    try:
        return json.loads(response)
    except json.JSONDecodeError:
        return {
            "score": 0,
            "qualification": response,
            "problem": "",
            "next_action": "Review this lead manually.",
        }