import unittest
from datetime import datetime
import functions
from database import init_database

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

class DeviceTests(unittest.TestCase):
    def test_system_info(self):
        info = functions.get_system_info()
        self.assertTrue(info["Computer name"])
        self.assertTrue(info["OS user"])
        self.assertIn("GB", info["Memory"])

    def test_format_duration(self):
        self.assertEqual(functions.format_duration(65), "1m 5s")
        self.assertEqual(functions.format_duration(3 * 3600 + 120), "3h 2m")
        self.assertEqual(functions.format_duration(90000), "1d 1h 0m")

class DatabaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_database()
        functions.register_user("Test", "User", "Latvia", "tester", "tester@example.com", "secret123",
                                "Where were you born?", "Riga")

    def test_login(self):
        self.assertEqual(functions.check_login("tester", "secret123"), ("ok", "tester"))
        self.assertEqual(functions.check_login("TESTER@example.com", "secret123"), ("ok", "tester"))
        self.assertEqual(functions.check_login("tester", "wrong")[0], "invalid")

    def test_security_answer(self):
        self.assertTrue(functions.check_security_answer("tester@example.com", "  riga "))
        self.assertFalse(functions.check_security_answer("tester@example.com", "Paris"))

    def test_due_time(self):
        self.assertEqual(functions.parse_due_time(""), "")
        self.assertIsNone(functions.parse_due_time("tomorrow"))
        self.assertEqual(functions.parse_due_time("2030-01-31 18:30"), "2030-01-31 18:30:00")
        self.assertGreater(functions.parse_due_time("00:00"), datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def test_todos(self):
        functions.add_todo("tester", "Old task", "2000-01-01 10:00:00")
        functions.add_todo("tester", "Future task", "2999-01-01 10:00:00")
        due = functions.get_due_todos("tester")
        self.assertEqual([todo["text"] for todo in due], ["Old task"])
        functions.mark_todo_notified(due[0]["id"])
        self.assertEqual(functions.get_due_todos("tester"), [])
        todo = functions.get_todos("tester")[0]
        functions.set_todo_done(todo["id"], True)
        self.assertTrue([t for t in functions.get_todos("tester") if t["id"] == todo["id"]][0]["done"])
        functions.delete_todo(todo["id"])
        self.assertEqual(len(functions.get_todos("tester")), 1)

    def test_webhook_url(self):
        functions.update_webhook_url("tester", "https://example.com/hook")
        self.assertEqual(functions.get_user_data("tester")["webhook_url"], "https://example.com/hook")

if __name__ == "__main__":
    unittest.main()
