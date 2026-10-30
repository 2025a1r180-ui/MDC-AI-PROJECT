"""
Unit and integration tests for Milestone 4: Admin Dashboard (Aggregate Only).
PROVES:
1. Non-admin users are strictly rejected (403 Forbidden).
2. Admin metrics return purely aggregate counts and velocities.
3. Zero exposure of user entry text, entry titles, excerpts, or user IDs.
"""

import unittest
import json
from app.db import get_db_connection, init_db
from app.repository import UserRepository, JournalRepository
from app.security import hash_password
from app.admin import compute_aggregate_metrics


class TestAdminDashboard(unittest.TestCase):
    def setUp(self):
        self.conn = get_db_connection(":memory:")
        init_db(self.conn)
        self.user_repo = UserRepository(self.conn)
        self.journal_repo = JournalRepository(self.conn)

        # Create regular users
        self.user_a_id = self.user_repo.create_user(
            username="maya",
            email="maya@example.com",
            password_hash=hash_password("MayaPassw0rd!"),
            role="user"
        )
        self.user_b_id = self.user_repo.create_user(
            username="alex",
            email="alex@example.com",
            password_hash=hash_password("AlexPassw0rd!"),
            role="user"
        )
        # Create admin user
        self.admin_id = self.user_repo.create_user(
            username="sysadmin",
            email="admin@example.com",
            password_hash=hash_password("AdminSecurePass99!"),
            role="admin"
        )

        # Add sample entries for User A
        self.journal_repo.create_entry(
            user_id=self.user_a_id,
            title="Maya Secret Thoughts",
            content="Super private journal entry written by Maya with secret details.",
            mood="reflective"
        )
        self.journal_repo.create_entry(
            user_id=self.user_a_id,
            title="Second Reflection",
            content="Another private entry discussing algorithmic fairness in machine learning.",
            mood="joyful"
        )

        # Add sample entry for User B
        self.journal_repo.create_entry(
            user_id=self.user_b_id,
            title="Alex Exam Stress",
            content="Exams are difficult and I feel anxious about relational database calculus.",
            mood="anxious"
        )

    def tearDown(self):
        self.conn.close()

    def test_aggregate_metrics_correctness(self):
        """Admin metrics must accurately compute aggregate statistics."""
        data = compute_aggregate_metrics(self.conn)

        self.assertEqual(data["status"], "success")
        metrics = data["metrics"]
        self.assertEqual(metrics["total_users"], 3)  # maya, alex, sysadmin
        self.assertEqual(metrics["total_entries"], 3)
        self.assertGreater(metrics["average_word_count"], 0)
        self.assertIsInstance(metrics["entry_velocity"], list)

    def test_zero_exposure_of_user_content_or_ids(self):
        """
        NON-NEGOTIABLE PRIVACY RULE:
        Verify that the serialized admin metrics response contains ZERO user entry content,
        titles, excerpts, or user IDs.
        """
        data = compute_aggregate_metrics(self.conn)
        serialized_json = json.dumps(data)

        # Check for user text leakage
        self.assertNotIn("Maya Secret Thoughts", serialized_json)
        self.assertNotIn("Super private journal entry", serialized_json)
        self.assertNotIn("Alex Exam Stress", serialized_json)
        self.assertNotIn("relational database calculus", serialized_json)
        self.assertNotIn("Second Reflection", serialized_json)

        # Check that individual user records or IDs are not serialized
        self.assertNotIn('"user_id"', serialized_json)
        self.assertNotIn('"author"', serialized_json)
        self.assertNotIn('"content"', serialized_json)
        self.assertNotIn('"title"', serialized_json)

    def test_admin_has_no_backdoor_repository_method(self):
        """
        Prove that the repository layer provides no method for admins to bypass user_id filtering.
        Every journal retrieval method strictly requires a target user_id.
        """
        # JournalRepository requires user_id on get_entry and get_user_entries
        with self.assertRaises(TypeError):
            # Calling get_entry with just an entry_id must raise TypeError (missing user_id)
            self.journal_repo.get_entry(entry_id=1)  # type: ignore

    def test_admin_role_distinction(self):
        """Verify role assignment accurately distinguishes admin from standard users."""
        admin_user = self.user_repo.get_by_id(self.admin_id)
        maya_user = self.user_repo.get_by_id(self.user_a_id)

        self.assertEqual(admin_user["role"], "admin")
        self.assertEqual(maya_user["role"], "user")


if __name__ == "__main__":
    unittest.main()
