"""
Tests for Non-Negotiable Rule 4: Strict Account Isolation.
PROVES that User A cannot read, edit, delete, search, or export User B's journal entries.
"""

import unittest
import json
from app.db import get_db_connection, init_db
from app.repository import UserRepository, JournalRepository
from app.security import hash_password


class TestAccountIsolation(unittest.TestCase):
    def setUp(self):
        # Fresh in-memory database for isolation testing
        self.conn = get_db_connection(":memory:")
        init_db(self.conn)
        self.user_repo = UserRepository(self.conn)
        self.journal_repo = JournalRepository(self.conn)

        # Create two distinct test users: User A (Maya) and User B (Alex)
        self.user_a_id = self.user_repo.create_user(
            username="maya",
            email="maya@example.com",
            password_hash=hash_password("MayaPassw0rd!")
        )
        self.user_b_id = self.user_repo.create_user(
            username="alex",
            email="alex@example.com",
            password_hash=hash_password("AlexPassw0rd!")
        )

        # User A writes private entries
        self.entry_a1_id = self.journal_repo.create_entry(
            user_id=self.user_a_id,
            title="Maya's Secret Discovery",
            content="This is private research notes only Maya should ever see.",
            mood="reflective",
            tags=["biology", "private"]
        )

        # User B writes private entries
        self.entry_b1_id = self.journal_repo.create_entry(
            user_id=self.user_b_id,
            title="Alex's Personal Reflection",
            content="Thoughts about upcoming college exams and stress management.",
            mood="anxious",
            tags=["exam", "thoughts"]
        )

    def tearDown(self):
        self.conn.close()

    def test_user_b_cannot_read_user_a_entry(self):
        """User B attempts to fetch User A's entry by its ID: MUST return None."""
        stolen_attempt = self.journal_repo.get_entry(entry_id=self.entry_a1_id, user_id=self.user_b_id)
        self.assertIsNone(
            stolen_attempt,
            "CRITICAL SECURITY VIOLATION: User B was able to read User A's private entry!"
        )

        # Legitimate owner can read their own entry
        legit_read = self.journal_repo.get_entry(entry_id=self.entry_a1_id, user_id=self.user_a_id)
        self.assertIsNotNone(legit_read)
        self.assertEqual(legit_read["title"], "Maya's Secret Discovery")

    def test_user_b_cannot_edit_user_a_entry(self):
        """User B attempts to modify User A's entry: MUST fail and leave data intact."""
        tamper_success = self.journal_repo.update_entry(
            entry_id=self.entry_a1_id,
            user_id=self.user_b_id,
            title="Hacked By Alex",
            content="Tampered content",
            mood="joyful"
        )
        self.assertFalse(
            tamper_success,
            "CRITICAL SECURITY VIOLATION: User B was able to modify User A's entry!"
        )

        # Verify entry content was untouched
        original_entry = self.journal_repo.get_entry(entry_id=self.entry_a1_id, user_id=self.user_a_id)
        self.assertEqual(original_entry["title"], "Maya's Secret Discovery")
        self.assertEqual(original_entry["content"], "This is private research notes only Maya should ever see.")

    def test_user_b_cannot_delete_user_a_entry(self):
        """User B attempts to delete User A's entry: MUST fail and leave entry in database."""
        delete_attempt = self.journal_repo.delete_entry(entry_id=self.entry_a1_id, user_id=self.user_b_id)
        self.assertFalse(
            delete_attempt,
            "CRITICAL SECURITY VIOLATION: User B was able to delete User A's entry!"
        )

        # Verify entry still exists for User A
        entry_still_exists = self.journal_repo.get_entry(entry_id=self.entry_a1_id, user_id=self.user_a_id)
        self.assertIsNotNone(entry_still_exists)

    def test_search_results_are_strictly_isolated(self):
        """Search query matching terms in User A's entries returns ZERO results for User B."""
        # Both write entries mentioning the word 'college'
        self.journal_repo.create_entry(
            user_id=self.user_a_id,
            title="College Project Proposal",
            content="Working on AI research at college campus."
        )

        # User B searches for 'college'
        alex_search = self.journal_repo.search_entries(user_id=self.user_b_id, search_term="college")
        
        # User B should only see their own entry, NOT User A's
        for entry in alex_search:
            self.assertEqual(
                entry["user_id"],
                self.user_b_id,
                "CRITICAL SECURITY VIOLATION: Cross-user search leak detected!"
            )
            self.assertNotEqual(entry["title"], "College Project Proposal")

    def test_export_archives_contain_zero_cross_user_records(self):
        """Data export for User A must strictly contain only User A's data."""
        json_export = self.journal_repo.export_entries_json(user_id=self.user_a_id)
        data = json.loads(json_export)

        self.assertEqual(data["user_id"], self.user_a_id)
        self.assertEqual(data["total_entries"], 1)
        self.assertEqual(data["entries"][0]["title"], "Maya's Secret Discovery")
        
        # Ensure User B's content is nowhere in the export string
        self.assertNotIn("Alex's Personal Reflection", json_export)
        self.assertNotIn("exams and stress", json_export)


if __name__ == "__main__":
    unittest.main()
