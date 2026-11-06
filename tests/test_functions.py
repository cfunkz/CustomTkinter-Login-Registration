import unittest
from datetime import datetime, timedelta
import functions
from database import init_database

class ValidationTests(unittest.TestCase):
    def test_gravatar_cache(self):
        # A saved picture is returned without downloading it again, the email is matched case-insensitively
        functions.gravatar_cache["cached@example.com"] = b"picture"
        self.assertEqual(functions.get_gravatar(" Cached@Example.com "), b"picture")
        self.assertIsNone(functions.get_gravatar(""))

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

    def test_todo_groups(self):
        today = datetime.now().strftime("%Y-%m-%d")
        todos = [{"text": "Now", "due_at": today + " 23:59:00", "done": False},
                 {"text": "Later", "due_at": "2999-01-01 10:00:00", "done": False},
                 {"text": "No time", "due_at": None, "done": False},
                 {"text": "Old", "due_at": "2000-01-01 10:00:00", "done": False},
                 {"text": "Done", "due_at": None, "done": True}]
        groups = functions.group_todos(todos)
        self.assertEqual([t["text"] for t in groups["Today"]], ["Now"])
        self.assertEqual([t["text"] for t in groups["Upcoming"]], ["Later", "No time"])
        self.assertEqual([t["text"] for t in groups["Archive"]], ["Old", "Done"])

    def test_archive_cleanup(self):
        functions.add_todo("cleaner", "Very old", "2000-01-01 10:00:00")
        functions.add_todo("cleaner", "Yesterday", (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"))
        functions.add_todo("cleaner", "Just done")
        functions.set_todo_done(functions.get_todos("cleaner")[-1]["id"], True)
        functions.delete_old_todos("cleaner", 7)
        self.assertEqual(sorted(t["text"] for t in functions.get_todos("cleaner")), ["Just done", "Yesterday"])
        functions.update_archive_days("tester", 14)
        self.assertEqual(functions.get_user_data("tester")["archive_days"], 14)

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
