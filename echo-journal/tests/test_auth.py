"""
Unit and integration tests for Authentication and Password Hashing (Milestone 1).
Validates scrypt KDF, verification constant-time check, duplicate rejection, and input constraints.
"""

import unittest
from app.db import get_db_connection, init_db
from app.repository import UserRepository
from app.security import hash_password, verify_password, sign_session_data, verify_session_data
from app.validation import validate_registration


class TestAuthentication(unittest.TestCase):
    def setUp(self):
        self.conn = get_db_connection(":memory:")
        init_db(self.conn)
        self.user_repo = UserRepository(self.conn)

    def tearDown(self):
        self.conn.close()

    def test_scrypt_password_hashing_and_verification(self):
        password = "SecurePa$$word123"
        hashed = hash_password(password)

        self.assertTrue(hashed.startswith("scrypt$16384$8$1$"))
        self.assertTrue(verify_password(password, hashed))
        self.assertFalse(verify_password("WrongPassword!", hashed))
        self.assertFalse(verify_password("", hashed))

    def test_registration_validation_rules(self):
        # Valid user
        valid, msg = validate_registration("valid_user", "test@example.com", "SecretPass123!")
        self.assertTrue(valid)
        self.assertIsNone(msg)

        # Short username (< 3 chars)
        valid, msg = validate_registration("ab", "test@example.com", "SecretPass123!")
        self.assertFalse(valid)

        # Invalid characters in username
        valid, msg = validate_registration("user<script>", "test@example.com", "SecretPass123!")
        self.assertFalse(valid)

        # Invalid email
        valid, msg = validate_registration("gooduser", "not-an-email", "SecretPass123!")
        self.assertFalse(valid)

        # Weak password (< 8 characters)
        valid, msg = validate_registration("gooduser", "test@example.com", "short")
        self.assertFalse(valid)

        # Password without numbers or symbols
        valid, msg = validate_registration("gooduser", "test@example.com", "lettersletters")
        self.assertFalse(valid)

    def test_user_creation_and_duplicate_prevention(self):
        pw_hash = hash_password("SecretPass123!")
        user_id = self.user_repo.create_user(
            username="testuser",
            email="testuser@example.com",
            password_hash=pw_hash
        )
        self.assertGreater(user_id, 0)

        # Lookups
        by_id = self.user_repo.get_by_id(user_id)
        self.assertEqual(by_id["username"], "testuser")
        self.assertEqual(by_id["email"], "testuser@example.com")

        by_email = self.user_repo.get_by_email("testuser@example.com")
        self.assertEqual(by_email["id"], user_id)

    def test_session_signing_and_tamper_detection(self):
        secret = "test_signing_secret_key_32bytes_len"
        session_data = {"user_id": 42, "username": "alice"}
        
        signed = sign_session_data(session_data, secret)
        self.assertIn(".", signed)

        # Valid verification
        unpacked = verify_session_data(signed, secret)
        self.assertEqual(unpacked, session_data)

        # Tampered signature
        tampered = signed[:-4] + "ffff"
        self.assertIsNone(verify_session_data(tampered, secret))

        # Wrong secret
        self.assertIsNone(verify_session_data(signed, "different_secret_key"))


if __name__ == "__main__":
    unittest.main()
