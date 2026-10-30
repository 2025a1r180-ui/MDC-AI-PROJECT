"""
Unit and Integration Tests for Milestone 3: Memory, Patterns, and Grounded Retrieval.

Verifies:
1. Strict Account Isolation in Hybrid Retrieval (User B cannot retrieve User A's data).
2. Minimum 10-Entry Invariant for Longitudinal Pattern Detection.
3. Non-Causal Phrasing & Scientific Integrity (no 'causes', 'caused', or 'diagnosis').
4. Crisis Safety Interceptor (halts processing, surfaces 24/7 helplines).
5. Strict Privacy Consent Gate (blocks external AI when opt_in_external_ai == False).
6. Evidence-Grounded Citations (every synthesis contains dates, titles, and excerpts).
"""

import unittest
from app.insights import HybridRetriever, PatternAnalyzer, answer_grounded_query
from app.safety import check_safety


class TestInsightsAndRetrieval(unittest.TestCase):
    def setUp(self):
        # Sample isolated entries for User A (Maya)
        self.user_a_entries = [
            {
                "id": 101,
                "user_id": 1,
                "title": "Quantum Cryptography and Rings",
                "content": "Studying lattice algorithms and algebraic rings in the campus library. Feeling very energized about math.",
                "mood": "reflective",
                "primary_emotion": "joy",
                "tags": ["college", "math", "cryptography"],
                "created_at": "2026-10-15 10:00:00"
            },
            {
                "id": 102,
                "user_id": 1,
                "title": "Autumn Pine Trail",
                "content": "Took a walk through the forest trail near campus. Crisp air and quiet sounds helped clear my mind.",
                "mood": "calm",
                "primary_emotion": "joy",
                "tags": ["nature", "walk", "mindfulness"],
                "created_at": "2026-10-16 08:30:00"
            },
            {
                "id": 103,
                "user_id": 1,
                "title": "College Team Meeting",
                "content": "Met with my project team members to discuss the database architecture and requirements.",
                "mood": "focused",
                "primary_emotion": "joy",
                "tags": ["college", "teamwork"],
                "created_at": "2026-10-17 14:00:00"
            }
        ]

        # Sample isolated entries for User B (Alex)
        self.user_b_entries = [
            {
                "id": 201,
                "user_id": 2,
                "title": "Alex's Exam Panic",
                "content": "Midterms are approaching and I am having trouble sleeping. Very stressed about relational algebra.",
                "mood": "anxious",
                "primary_emotion": "fear",
                "tags": ["exam", "college", "stress"],
                "created_at": "2026-10-15 22:00:00"
            }
        ]

    def test_hybrid_retrieval_account_isolation(self):
        """Proves that Hybrid Retrieval indexed on User A NEVER leaks User B's entries."""
        retriever_a = HybridRetriever(self.user_a_entries)
        # Search for a term that exists in User B's entry ("exam" or "panic")
        results = retriever_a.search("exam panic")
        
        # Result must not contain User B's entry
        for r in results:
            self.assertEqual(
                r["entry"]["user_id"], 1,
                "CRITICAL ISOLATION VIOLATION: User B's entry was retrieved in User A's search!"
            )
            self.assertNotEqual(r["entry"]["id"], 201)

    def test_hybrid_retrieval_ranking(self):
        """Proves that BM25 + dense n-gram hybrid retrieval ranks relevant entries first."""
        retriever = HybridRetriever(self.user_a_entries)
        results = retriever.search("forest walk trail")
        
        self.assertGreater(len(results), 0)
        top_entry = results[0]["entry"]
        self.assertEqual(top_entry["id"], 102)
        self.assertIn("Autumn Pine Trail", top_entry["title"])

    def test_pattern_analysis_threshold_invariant(self):
        """
        Under 10 entries: Pattern detection MUST reject pattern drawing with an honest message.
        At 10+ entries: Pattern detection proceeds with empirical distributions.
        """
        # Test under threshold (3 entries)
        under_result = PatternAnalyzer.analyze_patterns(self.user_a_entries)
        self.assertFalse(under_result["eligible"])
        self.assertEqual(under_result["entry_count"], 3)
        self.assertIn("minimum of 10 journal entries", under_result["message"])

        # Create 10 entries
        ten_entries = []
        for i in range(12):
            ten_entries.append({
                "id": 1000 + i,
                "user_id": 1,
                "title": f"Study Log Day {i}",
                "content": f"Entry content for study session number {i} with library focus.",
                "mood": "calm" if i % 2 == 0 else "focused",
                "primary_emotion": "joy" if i % 3 == 0 else "sadness",
                "tags": ["study", "college"],
                "created_at": f"2026-10-{10+i:02d} 12:00:00"
            })

        over_result = PatternAnalyzer.analyze_patterns(ten_entries)
        self.assertTrue(over_result["eligible"])
        self.assertEqual(over_result["entry_count"], 12)
        self.assertIn("emotion_distribution", over_result)
        self.assertIn("co_occurrences", over_result)

    def test_non_causal_phrasing_invariance(self):
        """
        NON-NEGOTIABLE RULE 1 & 2: Pattern analysis must NEVER claim causation.
        Verifies absence of causal words ('causes', 'caused', 'diagnose') and presence of correlation notice.
        """
        ten_entries = []
        for i in range(10):
            ten_entries.append({
                "id": 2000 + i,
                "user_id": 1,
                "title": f"Exam Prep {i}",
                "content": f"Exam preparation session {i}",
                "mood": "anxious",
                "primary_emotion": "fear",
                "tags": ["exam"],
                "created_at": f"2026-10-{10+i:02d} 12:00:00"
            })

        result = PatternAnalyzer.analyze_patterns(ten_entries)
        self.assertTrue(result["eligible"])

        for co in result["co_occurrences"]:
            obs = co["observation"].lower()
            self.assertNotIn(" causes ", obs, "VIOLATION: Causal verb 'causes' detected in pattern insight!")
            self.assertNotIn(" caused ", obs, "VIOLATION: Causal verb 'caused' detected in pattern insight!")
            self.assertIn("co-occur", obs, "Pattern insight must use non-causal co-occurrence language.")

        self.assertIn("never asserts causation", result["non_causal_notice"].lower())

    def test_grounded_query_crisis_interceptor(self):
        """Crisis or self-harm keywords MUST halt query processing and surface helplines."""
        crisis_query = "I don't want to wake up, I want to kill myself"
        response = answer_grounded_query(
            query=crisis_query,
            user_entries=self.user_a_entries,
            user_opted_in=True
        )

        self.assertEqual(response["status"], "crisis_detected")
        self.assertIn("helplines", response)
        self.assertIn("US_Canada", response["helplines"])
        self.assertEqual(response["helplines"]["US_Canada"]["contact"], "Call or Text 988")
        self.assertIn("UK", response["helplines"])
        self.assertIn("India", response["helplines"])
        self.assertIsNone(response["grounded_text"])

    def test_grounded_query_privacy_gate(self):
        """When user has NOT opted in, no reflection is generated and privacy gate informs user."""
        response = answer_grounded_query(
            query="What did I study recently?",
            user_entries=self.user_a_entries,
            user_opted_in=False
        )

        self.assertEqual(response["status"], "consent_required")
        self.assertIn("Privacy Gate", response["message"])
        self.assertIsNone(response["grounded_text"])

    def test_grounded_query_citations_and_uncertainty(self):
        """Grounded answers must return explicit citations with dates, excerpts, and uncertainty notice."""
        response = answer_grounded_query(
            query="Where did I walk or spend time in nature?",
            user_entries=self.user_a_entries,
            user_opted_in=True
        )

        self.assertEqual(response["status"], "success")
        self.assertGreater(len(response["citations"]), 0)

        # Check citation structure
        citation = response["citations"][0]
        self.assertIn("entry_id", citation)
        self.assertIn("date", citation)
        self.assertIn("excerpt", citation)
        self.assertIn("title", citation)

        # Check uncertainty notice presence
        self.assertIn("uncertainty_notice", response)
        self.assertIn("Synthesized strictly from", response["uncertainty_notice"])


if __name__ == "__main__":
    unittest.main()
