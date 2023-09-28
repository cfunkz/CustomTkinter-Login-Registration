import tkinter
import customtkinter
from frames import MainFrame, RegisterFrame, LoggedInFrame, ForgotPasswordFrame

customtkinter.set_appearance_mode("System")
customtkinter.set_default_color_theme("green")

class MainApp(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.geometry("600x400")
        self.title("Sign into your Account")

        # Create the Main frame
        self.main_frame = MainFrame(self)
        self.main_frame.pack(expand=True, fill="both") # Expand to fill the main app window

    def change_geometry(self, new_geometry):
        # Change the window geometry
        self.geometry(new_geometry)

    def open_loggedin_frame(self):
        # Destroy the Main frame and open the LoggedIn frame
        self.main_frame.destroy()
        # Start logged in frame
        self.loggedin_frame = LoggedInFrame(self)
        self.loggedin_frame.pack(expand=True, fill="both") # Expand to fill the main app window

    def open_register_frame(self):
        # Destroy the Main frame and open the Register frame
        self.main_frame.destroy()
        # Start registration frame
        self.register_frame = RegisterFrame(self)
        self.register_frame.pack(expand=True, fill="both") # Expand to fill the main app window

    def open_forgot_password_frame(self):
        self.main_frame.destroy()
        self.forgot_password_frame = ForgotPasswordFrame(self)
        self.forgot_password_frame.pack(expand=True, fill="both")

