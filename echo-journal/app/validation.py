"""
Validation module for Echo Journal.
Enforces strict input constraints and sanitary standards for user accounts and journal entries.
"""

import re
from typing import Tuple, List, Optional

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
ALLOWED_MOODS = {
    "calm",
    "reflective",
    "joyful",
    "grateful",
    "overwhelmed",
    "anxious",
    "sad",
    "neutral"
}


def validate_registration(username: str, email: str, password: str) -> Tuple[bool, Optional[str]]:
    """Validate user registration inputs."""
    username = (username or "").strip()
    email = (email or "").strip().lower()
    
    if len(username) < 3 or len(username) > 30:
        return False, "Username must be between 3 and 30 characters long."
        
    if not re.match(r"^[a-zA-Z0-9_-]+$", username):
        return False, "Username may only contain letters, numbers, underscores, and hyphens."
        
    if not EMAIL_REGEX.match(email):
        return False, "Please provide a valid email address."
        
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
        
    if not any(c.isalpha() for c in password) or not any(c.isdigit() or not c.isalnum() for c in password):
        return False, "Password must contain both letters and at least one number or symbol."
        
    return True, None


def validate_entry(title: str, content: str, mood: Optional[str] = None, tags: Optional[List[str]] = None) -> Tuple[bool, Optional[str]]:
    """Validate journal entry inputs."""
    title = (title or "").strip()
    content = (content or "").strip()
    
    if not title:
        return False, "Entry title cannot be blank."
        
    if len(title) > 200:
        return False, "Entry title cannot exceed 200 characters."
        
    if not content:
        return False, "Journal entry text cannot be blank."
        
    if len(content) > 50000:
        return False, "Journal entry exceeds the 50,000 character limit."
        
    if mood and mood.lower() not in ALLOWED_MOODS:
        return False, f"Invalid mood selected. Allowed options: {', '.join(sorted(ALLOWED_MOODS))}."
        
    if tags:
        if len(tags) > 10:
            return False, "Maximum of 10 tags allowed per entry."
        for tag in tags:
            clean_tag = tag.strip().lower()
            if len(clean_tag) > 30:
                return False, f"Tag '{clean_tag}' exceeds 30 characters."
            if not re.match(r"^[a-zA-Z0-9_\-]+$", clean_tag):
                return False, f"Tag '{clean_tag}' contains invalid characters (use alphanumeric, dash or underscore)."
                
    return True, None
