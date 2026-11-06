import customtkinter
import config
from frames import MainFrame, RegisterFrame, LoggedInFrame, ForgotPasswordFrame, ForgotPasswordFrame2, ChangePasswordFrame, BACKGROUND_COLOR
from functions import init_database

# Appearance settings from config.py / .env
customtkinter.set_appearance_mode(config.appearance_mode)
customtkinter.set_default_color_theme(config.color_theme)
customtkinter.set_widget_scaling(config.ui_scaling)

class MainApp(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        # Create the database table once when the app starts
        init_database()

        self.configure(fg_color=BACKGROUND_COLOR)
        self.resizable(config.window_resizable, config.window_resizable)
        self.current_frame = None  # Only one frame is shown at a time
        self.current_user = None  # Username of the logged in user
        self.window_size = None  # Current "widthxheight" from config.py
        # Create the Main frame
        self.open_main_frame()

    def change_geometry(self, new_geometry):
        # Change the window size and keep the window centered (only when the size changes)
        new_geometry = new_geometry.replace(" ", "")
        if new_geometry != self.window_size:
            self.window_size = new_geometry
            self.center_window()

    def change_title(self, new_title):
        # Change the window title
        self.title(new_title)

    def center_window(self):
        # Move the window to the middle of the screen
        # Uses the size from config.py instead of reading it back, because Windows reports the old size until the window is drawn
        width, height = (int(value) for value in self.window_size.split("x"))
        # customtkinter scales sizes and positions for high DPI screens, the screen size is in real pixels
        scaling = self._get_window_scaling()
        x = int((self.winfo_screenwidth() / scaling - width) / 2)
        y = int((self.winfo_screenheight() / scaling - height) / 3)
        self.geometry(f"{width}x{height}+{max(x, 0)}+{max(y, 0)}")

    def switch_frame(self, frame_class, *args):
        # Destroy the current frame and show a new one in its place
        if self.current_frame is not None:
            self.current_frame.destroy()
        self.current_frame = frame_class(self, *args)
        self.current_frame.pack(expand=True, fill="both")  # Expand to fill the main app window
        return self.current_frame

    def open_main_frame(self, message=None, kind="success"):
        # Log out and go back to the login screen, optionally with a message
        self.current_user = None
        self.main_frame = self.switch_frame(MainFrame, message, kind)

    def open_loggedin_frame(self, username):
        # Start logged in frame
        self.current_user = username
        self.loggedin_frame = self.switch_frame(LoggedInFrame, username)

    def open_register_frame(self):
        # Start registration frame
        self.register_frame = self.switch_frame(RegisterFrame)

    def open_forgot_password_frame(self):
        self.forgot_password_frame = self.switch_frame(ForgotPasswordFrame)

    def open_forgot_password_frame2(self, user_email):
        self.forgot_password_frame2 = self.switch_frame(ForgotPasswordFrame2, user_email)

    def open_change_password_frame(self, username):
        # Shown after logging in with a temporary password
        self.current_user = username
        self.change_password_frame = self.switch_frame(ChangePasswordFrame, username)

    def destroy_all_frames(self):
        # Kept for backwards compatibility, there is only ever one frame now
        if self.current_frame is not None:
            self.current_frame.destroy()
            self.current_frame = None
