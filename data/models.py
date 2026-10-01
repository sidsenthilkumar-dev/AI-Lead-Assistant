from dataclasses import dataclass
from typing import Optional


@dataclass
class Lead:
    id: Optional[int] = None
    name: str = ""
    company: str = ""
    industry: str = ""
    website: str = ""
    phone: str = ""
    address: str = ""
    source: str = ""

    problem: str = ""
    qualification: str = ""
    score: Optional[int] = None

    status: str = "New"

    outreach_message: str = ""
    follow_up_message: str = ""
    next_action: str = ""