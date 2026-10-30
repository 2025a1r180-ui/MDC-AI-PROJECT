"""
Unit and integration tests for Security, CSRF, XSS Sanitization, and Cascade Account Deletion.
"""

import unittest
from app.db import get_db_connection, init_db
from app.repository import UserRepository, JournalRepository
from app.security import (
    generate_csrf_token,
    verify_csrf_token,
    sanitize_text,
    hash_password
)
from app.safety import check_safety


class TestSecurity(unittest.TestCase):
    def setUp(self):
        self.conn = get_db_connection(":memory:")
        init_db(self.conn)
        self.user_repo = UserRepository(self.conn)
        self.journal_repo = JournalRepository(self.conn)

    def tearDown(self):
        self.conn.close()

    def test_csrf_token_lifecycle(self):
        token1 = generate_csrf_token()
        token2 = generate_csrf_token()

        self.assertNotEqual(token1, token2)
        self.assertEqual(len(token1), 64)  # 32 bytes hex

        # Valid comparison
        self.assertTrue(verify_csrf_token(token1, token1))
        # Tampered comparison
        self.assertFalse(verify_csrf_token(token1, token2))
        self.assertFalse(verify_csrf_token(token1, ""))

    def test_html_sanitization_defense(self):
        xss_payload = '<script>alert("hacked")</script>'
        safe_output = sanitize_text(xss_payload)

        self.assertNotIn("<script>", safe_output)
        self.assertIn("&lt;script&gt;", safe_output)
        self.assertIn("&quot;hacked&quot;", safe_output)

    def test_cascade_account_deletion(self):
        """Proves that deleting an account cascades to erase all entries and prevents orphaned data."""
        user_id = self.user_repo.create_user(
            username="tempuser",
            email="temp@example.com",
            password_hash=hash_password("Pass12345!")
        )
        self.journal_repo.create_entry(user_id, "Entry 1", "Content 1")
        self.journal_repo.create_entry(user_id, "Entry 2", "Content 2")

        # Verify 2 entries exist
        self.assertEqual(self.journal_repo.get_entry_count(user_id), 2)

        # Delete account
        deleted = self.user_repo.delete_account(user_id)
        self.assertTrue(deleted)

        # User is gone
        self.assertIsNone(self.user_repo.get_by_id(user_id))
        # All entries are completely gone
        self.assertEqual(self.journal_repo.get_entry_count(user_id), 0)

    def test_crisis_safety_layer(self):
        """Ensures acute crisis keywords trigger supportive helpline resources and halt inference."""
        crisis_text = "I feel completely hopeless and want to end my life."
        is_crisis, payload = check_safety(crisis_text)
        self.assertTrue(is_crisis)
        self.assertIsNotNone(payload)
        self.assertIn("helplines", payload)
        self.assertIn("988", payload["helplines"]["US_Canada"]["contact"])

        # Non-crisis text
        normal_text = "I had a busy and exhausting day studying at the campus library."
        is_crisis_normal, payload_normal = check_safety(normal_text)
        self.assertFalse(is_crisis_normal)
        self.assertIsNone(payload_normal)

    def test_sliding_window_rate_limiter(self):
        """Validates that sliding window rate limiter blocks excessive requests."""
        from app.rate_limit import SlidingWindowRateLimiter
        
        limiter = SlidingWindowRateLimiter(max_requests=3, window_seconds=60)
        client_key = "192.168.1.100"
        
        # First 3 attempts must succeed
        self.assertTrue(limiter.record_attempt(client_key)[0])
        self.assertTrue(limiter.record_attempt(client_key)[0])
        self.assertTrue(limiter.record_attempt(client_key)[0])
        
        # 4th attempt must be blocked
        allowed, retry_after = limiter.record_attempt(client_key)
        self.assertFalse(allowed)
        self.assertGreater(retry_after, 0)
        
        # Different client key must not be blocked
        self.assertTrue(limiter.record_attempt("192.168.1.101")[0])
        
        # Reset allows access again
        limiter.reset(client_key)
        self.assertTrue(limiter.record_attempt(client_key)[0])


if __name__ == "__main__":
    unittest.main()

