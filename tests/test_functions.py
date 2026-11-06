import json
import os
import unittest
from datetime import datetime, timedelta
from tests import TEST_DIR
import functions
from database import init_database, now

def past(**kwargs):
    # A saved date some time ago, in the same format as the database
    return (datetime.now() - timedelta(**kwargs)).strftime("%Y-%m-%d %H:%M:%S")

class ValidationTests(unittest.TestCase):
    def test_email(self):
        self.assertTrue(functions.is_valid_email("john@example.com"))
        self.assertFalse(functions.is_valid_email("john@example"))

    def test_username_chars(self):
        self.assertTrue(functions.is_valid_chars("john_doe-1"))
        self.assertFalse(functions.is_valid_chars("john doe"))

    def test_strong_password(self):
        self.assertTrue(functions.is_strong_password("abcdefg1"))
        self.assertFalse(functions.is_strong_password("abcdefgh"))

    def test_password_hash(self):
        stored = functions.hash_password("secret123")
        self.assertTrue(functions.verify_password("secret123", stored))
        self.assertFalse(functions.verify_password("wrong123", stored))

    def test_country(self):
        self.assertTrue(functions.validate_country("Latvia"))
        self.assertFalse(functions.validate_country("Atlantis"))

class ProfileHelperTests(unittest.TestCase):
    def test_time_ago(self):
        self.assertEqual(functions.time_ago(None), "Never")
        self.assertEqual(functions.time_ago(now()), "Just now")
        self.assertEqual(functions.time_ago(past(hours=3)), "3 hours ago")
        self.assertEqual(functions.time_ago(past(days=1, minutes=5)), "1 day ago")

    def test_days_since(self):
        self.assertEqual(functions.days_since(past(days=10, minutes=1)), 10)
        self.assertEqual(functions.days_since("not a date"), 0)

    def test_greeting(self):
        self.assertEqual(functions.get_greeting(8), "Good morning")
        self.assertEqual(functions.get_greeting(14), "Good afternoon")
        self.assertEqual(functions.get_greeting(21), "Good evening")

    def test_initials(self):
        self.assertEqual(functions.get_initials({"first_name": "John", "last_name": "Smith"}), "JS")
        self.assertEqual(functions.get_initials({}, "bob"), "B")

    def test_gravatar_cache(self):
        # A saved picture is returned without downloading it again, the email is matched case-insensitively
        functions.gravatar_cache["cached@example.com"] = b"picture"
        self.assertEqual(functions.get_gravatar(" Cached@Example.com "), b"picture")
        self.assertIsNone(functions.get_gravatar(""))

    def test_profile_completion(self):
        user = {"first_name": "John", "last_name": "Smith", "country": "Latvia", "email": "j@example.com", "bio": "Hi",
                "password_set": 1, "security_question": "Where were you born?"}
        self.assertEqual(functions.profile_completion(user)[0], 100)
        user["bio"] = ""
        self.assertEqual(functions.profile_completion(user)[0], 83)

    def test_security_score(self):
        self.assertEqual(functions.security_score({"password_set": 1, "security_question": "Q", "email": "e"}), (85, "Strong"))
        self.assertEqual(functions.security_score({"password_set": 0, "oauth_provider": "google", "email": "e"}), (30, "Weak"))

class DatabaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_database()
        functions.register_user("Test", "User", "Latvia", "tester", "tester@example.com", "secret123",
                                "Where were you born?", "Riga")

    def test_login_counts(self):
        before = functions.get_user_data("tester")["login_count"] or 0
        self.assertEqual(functions.check_login("tester", "secret123"), ("ok", "tester"))
        self.assertEqual(functions.check_login("TESTER@example.com", "secret123"), ("ok", "tester"))
        self.assertEqual(functions.get_user_data("tester")["login_count"], before + 2)
        self.assertEqual(functions.check_login("tester", "wrong")[0], "invalid")

    def test_bio_and_export(self):
        self.assertTrue(functions.update_bio("tester", "  Python developer  "))
        self.assertEqual(functions.get_user_data("tester")["bio"], "Python developer")
        path = os.path.join(TEST_DIR, "export.json")
        self.assertTrue(functions.export_user_data("tester", path))
        with open(path, encoding="utf-8") as export_file:
            data = json.load(export_file)
        self.assertEqual(data["username"], "tester")
        self.assertNotIn("password", data)

    def test_security_answer(self):
        self.assertTrue(functions.check_security_answer("tester@example.com", "  riga "))
        self.assertFalse(functions.check_security_answer("tester@example.com", "Paris"))

if __name__ == "__main__":
    unittest.main()
