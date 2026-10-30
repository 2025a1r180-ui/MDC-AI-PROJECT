"""
LLM Client Interface for Echo Journal.
Architecture interface for Milestone 3 'Ask your journal'.

Non-Negotiable Rule 1: Echo Journal is a self-reflection tool, NOT a doctor or therapist. Never diagnose.
Non-Negotiable Rule 2: Never invent journal content. Every insight must cite dates/excerpts. State uncertainty.
Non-Negotiable Rule 5: No journal text leaves the server unless user explicitly opted in.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

SYSTEM_PROMPT_TEMPLATE = """You are Echo Journal's self-reflection assistant.
NON-NEGOTIABLE OPERATIONAL CONSTRAINTS:
1. You are a self-reflection tool, NOT a doctor, therapist, or diagnostic system. NEVER diagnose any medical or psychological condition.
2. NEVER claim causation from journal patterns (use phrasing like 'frequently appears alongside' or 'co-occurs with', NEVER 'causes').
3. Rely SOLELY on the supplied journal excerpts below. NEVER invent, fabricate, or assume details not present in the excerpts.
4. Every single observation or synthesis MUST explicitly cite the specific date or entry excerpt it originated from.
5. If there is insufficient context in the provided entries to address the user's question, state clearly and honestly: 'There is not enough evidence in your recorded entries to reflect on this topic.'

SUPPLIED RELEVANT JOURNAL ENTRIES:
{context_entries}
"""


class BaseLLMClient(ABC):
    """Abstract client interface allowing zero-friction provider swaps."""

    @abstractmethod
    def generate_reflection(
        self,
        query: str,
        context_entries: List[Dict[str, Any]],
        user_opted_in: bool
    ) -> Dict[str, Any]:
        pass


class SwappableLLMClient(BaseLLMClient):
    """
    Default client implementation enforcing strict privacy opt-in gates,
    grounded synthesis, and uncertainty notices.
    """

    def __init__(self, provider: str = "local_grounded_rag"):
        self.provider = provider

    def generate_reflection(
        self,
        query: str,
        context_entries: List[Dict[str, Any]],
        user_opted_in: bool
    ) -> Dict[str, Any]:
        if not user_opted_in:
            return {
                "error": "Privacy Gate: External AI processing is disabled until you explicitly opt in under Account Settings.",
                "status": "blocked_by_consent_gate",
                "citations": []
            }

        if not context_entries:
            return {
                "status": "insufficient_evidence",
                "reflection": "There is not enough evidence in your recorded entries to reflect on this topic.",
                "citations": [],
                "uncertainty_notice": "Reflections require explicit textual evidence."
            }

        # Build citations and synthesis
        citations = []
        dated_excerpts = []
        for entry in context_entries:
            date_str = str(entry.get("created_at", ""))[:10] or "Unknown"
            title = entry.get("title", "Untitled")
            excerpt = entry.get("content", "")[:150]
            citations.append({
                "entry_id": entry.get("id"),
                "date": date_str,
                "title": title,
                "excerpt": excerpt
            })
            dated_excerpts.append(f"• [{date_str} - '{title}'] \"{excerpt}\"")

        body = (
            f"Reviewing your entries in connection with '{query}':\n\n"
            + "\n".join(dated_excerpts) +
            "\n\nObservation: These excerpts reflect recurring thoughts recorded during these moments."
        )

        return {
            "status": "success",
            "provider": self.provider,
            "reflection": body,
            "citations": citations,
            "uncertainty_notice": (
                f"Generated from {len(citations)} retrieved entries. "
                "Co-occurrences in personal writing are observations, not medical diagnoses or causal links."
            )
        }
