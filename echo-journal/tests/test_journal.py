"""
Unit and integration tests for Journal CRUD, search, and export (Milestone 1).
"""

import unittest
import json
from app.db import get_db_connection, init_db
from app.repository import UserRepository, JournalRepository
from app.security import hash_password
from app.validation import validate_entry


class TestJournal(unittest.TestCase):
    def setUp(self):
        self.conn = get_db_connection(":memory:")
        init_db(self.conn)
        self.user_repo = UserRepository(self.conn)
        self.journal_repo = JournalRepository(self.conn)

        self.user_id = self.user_repo.create_user(
            username="writer",
            email="writer@example.com",
            password_hash=hash_password("Passw0rd123!")
        )

    def tearDown(self):
        self.conn.close()

    def test_entry_validation(self):
        # Valid entry
        valid, msg = validate_entry("Morning Reflection", "A calm start to the day.", mood="calm", tags=["morning"])
        self.assertTrue(valid)
        self.assertIsNone(msg)

        # Blank title
        valid, msg = validate_entry("", "Content here")
        self.assertFalse(valid)

        # Blank content
        valid, msg = validate_entry("Title here", "")
        self.assertFalse(valid)

        # Invalid mood
        valid, msg = validate_entry("Title", "Content", mood="ecstatic")
        self.assertFalse(valid)

        # Too many tags (> 10)
        valid, msg = validate_entry("Title", "Content", tags=[f"tag{i}" for i in range(12)])
        self.assertFalse(valid)

    def test_crud_lifecycle(self):
        # 1. Create
        entry_id = self.journal_repo.create_entry(
            user_id=self.user_id,
            title="Autumn Reflections",
            content="Leaves turning golden outside the college library.",
            mood="reflective",
            tags=["autumn", "study"]
        )
        self.assertGreater(entry_id, 0)

        # 2. Read
        entry = self.journal_repo.get_entry(entry_id=entry_id, user_id=self.user_id)
        self.assertIsNotNone(entry)
        self.assertEqual(entry["title"], "Autumn Reflections")
        self.assertEqual(entry["mood"], "reflective")
        self.assertEqual(entry["word_count"], 7)
        self.assertEqual(entry["reading_time_minutes"], 1)

        # 3. Update
        updated = self.journal_repo.update_entry(
            entry_id=entry_id,
            user_id=self.user_id,
            title="Autumn Reflections (Revised)",
            content="Leaves turning golden outside the library, crisp breeze.",
            mood="calm",
            tags=["autumn", "peaceful"]
        )
        self.assertTrue(updated)

        entry_after_edit = self.journal_repo.get_entry(entry_id=entry_id, user_id=self.user_id)
        self.assertEqual(entry_after_edit["title"], "Autumn Reflections (Revised)")
        self.assertEqual(entry_after_edit["mood"], "calm")

        # 4. Delete
        deleted = self.journal_repo.delete_entry(entry_id=entry_id, user_id=self.user_id)
        self.assertTrue(deleted)

        entry_after_del = self.journal_repo.get_entry(entry_id=entry_id, user_id=self.user_id)
        self.assertIsNone(entry_after_del)

    def test_search_and_filtering(self):
        self.journal_repo.create_entry(
            user_id=self.user_id,
            title="Quantum Mechanics Notes",
            content="Fascinating lecture on wave-particle duality.",
            mood="reflective",
            tags=["physics"]
        )
        self.journal_repo.create_entry(
            user_id=self.user_id,
            title="Weekend Forest Hike",
            content="Walked along the pine trail, peaceful and grounding.",
            mood="calm",
            tags=["nature"]
        )

        # Keyword search
        results = self.journal_repo.search_entries(user_id=self.user_id, search_term="quantum")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "Quantum Mechanics Notes")

        # Mood filtering
        calm_results = self.journal_repo.get_user_entries(user_id=self.user_id, mood="calm")
        self.assertEqual(len(calm_results), 1)
        self.assertEqual(calm_results[0]["title"], "Weekend Forest Hike")

    def test_export_formats(self):
        self.journal_repo.create_entry(
            user_id=self.user_id,
            title="Export Milestone Check",
            content="Testing data portability export functions.",
            mood="joyful",
            tags=["college", "project"]
        )

        # JSON Export
        json_str = self.journal_repo.export_entries_json(user_id=self.user_id)
        parsed = json.loads(json_str)
        self.assertEqual(parsed["user_id"], self.user_id)
        self.assertGreaterEqual(parsed["total_entries"], 1)
        self.assertEqual(parsed["entries"][0]["title"], "Export Milestone Check")

        # Markdown Export
        md_str = self.journal_repo.export_entries_markdown(user_id=self.user_id)
        self.assertIn("# Echo Journal Export", md_str)
        self.assertIn("## Export Milestone Check", md_str)
        self.assertIn("**Mood:** joyful", md_str)


if __name__ == "__main__":
    unittest.main()
