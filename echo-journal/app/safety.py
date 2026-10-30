"""
Safety and Crisis Detection Layer for Echo Journal.
Non-Negotiable Rule 1: Echo Journal is a self-reflection tool, NOT a medical or diagnostic system.
If an entry or question indicates self-harm or acute psychological crisis,
the system suppresses generative inference and surfaces supportive helpline resources.
"""

import re
from typing import Tuple, Optional, Dict, List, Any

# High-sensitivity keyword patterns indicating acute crisis or self-harm ideation
CRISIS_PATTERNS = [
    re.compile(r"\b(suicid(e|al)|kill myself|end my life|want to die|ending it all)\b", re.IGNORECASE),
    re.compile(r"\b(self[\s-]?harm|cutting myself|take my own life|slit my wrist)\b", re.IGNORECASE),
    re.compile(r"\b(better off dead|no reason to live|don'?t want to wake up)\b", re.IGNORECASE),
]

HELPLINE_RESOURCES: Dict[str, Dict[str, str]] = {
    "US_Canada": {
        "service": "Suicide & Crisis Lifeline",
        "contact": "Call or Text 988",
        "website": "https://988lifeline.org",
        "availability": "24/7, Free and Confidential"
    },
    "UK": {
        "service": "Samaritans",
        "contact": "Call 116 123",
        "website": "https://www.samaritans.org",
        "availability": "24/7, Free"
    },
    "International": {
        "service": "International Association for Suicide Prevention (IASP)",
        "contact": "Find a local helpline",
        "website": "https://www.iasp.info/resources/Crisis_Centres/",
        "availability": "Global directories and crisis centres"
    },
    "India": {
        "service": "Tele-MANAS / Vandrevala Foundation",
        "contact": "Call 14416 or +91 9999 666 555",
        "website": "https://telemanas.mohfw.gov.in",
        "availability": "24/7, Toll-Free"
    }
}


def check_safety(text: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Scans text for acute crisis or self-harm indicators.
    Returns (is_crisis_detected, helpline_data_or_none).
    """
    if not text:
        return False, None

    for pattern in CRISIS_PATTERNS:
        if pattern.search(text):
            return True, {
                "message": (
                    "It sounds like you are going through a very painful time. "
                    "Echo Journal cannot replace real human care. "
                    "Please consider connecting immediately with someone who can support you:"
                ),
                "helplines": HELPLINE_RESOURCES,
                "disclaimer": "Echo Journal is a reflective tool, not a medical or emergency provider."
            }

    return False, None
