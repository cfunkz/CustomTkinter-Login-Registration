import os
import tkinter
import unittest
from tests import TEST_DIR

# Opens the real window, builds every screen and closes it again.
# Needs a display: Windows and macOS have one, on Linux run it with xvfb-run.

class UITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            tkinter.Tk().destroy()
        except tkinter.TclError as e:
            raise unittest.SkipTest(f"No display available: {e}")
        import functions
        from app import MainApp
        cls.app = MainApp()
        functions.register_user("Ui", "Tester", "Latvia", "uitester", "ui@example.com", "secret123", "Where were you born?", "Riga")

    @classmethod
    def tearDownClass(cls):
        cls.app.destroy()

    def draw(self):
        self.app.update_idletasks()
        self.app.update()

    def test_auth_screens(self):
        for open_screen in (self.app.open_main_frame, self.app.open_register_frame, self.app.open_forgot_password_frame,
                            lambda: self.app.open_forgot_password_frame2("ui@example.com"),
                            lambda: self.app.open_change_password_frame("uitester")):
            open_screen()
            self.draw()
        self.app.open_main_frame()

    def test_dashboard(self):
        self.app.open_loggedin_frame("uitester")
        self.draw()
        dashboard = self.app.current_frame
        for page in ("security", "device", "todo"):
            dashboard.show_page(page)
            self.draw()
        dashboard.todo_entry.insert(0, "Buy milk")
        dashboard.due_entry.insert(0, "18:30")
        dashboard.handle_add_todo()
        self.draw()
        self.assertEqual(dashboard.todo_status.cget("text"), "")
        dashboard.show_page("profile")
        self.draw()
        self.app.open_main_frame()

if __name__ == "__main__":
    unittest.main()
