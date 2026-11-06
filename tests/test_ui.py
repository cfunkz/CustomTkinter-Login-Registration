import io
import os
import tkinter
from PIL import Image
import frames
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

        # Calendar popup sets the time of the new task
        popup = frames.CalendarPopup(dashboard, dashboard.set_due_time)
        self.draw()
        popup.change_month(1)
        popup.select_day(15)
        popup.pick()
        self.assertRegex(dashboard.due_at, r"^\d{4}-\d{2}-15 \d{2}:00$")
        self.assertEqual(dashboard.due_button.cget("text"), dashboard.due_at)
        dashboard.handle_add_todo()
        self.draw()
        self.assertEqual(dashboard.todo_status.cget("text"), "")
        self.assertEqual(dashboard.due_at, "")
        dashboard.save_archive_days("3")
        self.draw()
        dashboard.show_page("profile")
        self.draw()

        # Fake Gravatar picture replaces the initials in the sidebar and on the profile page
        picture = io.BytesIO()
        Image.new("RGB", (40, 40), "#6366F1").save(picture, "PNG")
        dashboard.show_gravatar(picture.getvalue(), None)
        self.draw()
        self.assertEqual(dashboard.avatar.cget("text"), "")
        self.assertEqual(dashboard.profile_avatar.cget("text"), "")
        self.app.open_main_frame()

if __name__ == "__main__":
    unittest.main()
