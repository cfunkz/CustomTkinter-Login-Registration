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
        self.frames = {}

    def change_geometry(self, new_geometry):
        # Change the window geometry
        self.geometry(new_geometry)

    def open_loggedin_frame(self):
        # Destroy the Main frame and open the LoggedIn frame
        self.main_frame.destroy()
        # Start logged in frame
        self.loggedin_frame = LoggedInFrame(self)
        self.frames["loggedin_frame"] = self.loggedin_frame
        self.loggedin_frame.pack(expand=True, fill="both") # Expand to fill the main app window

    def open_register_frame(self):
        # Destroy the Main frame and open the Register frame
        self.main_frame.destroy()
        # Start registration frame
        self.register_frame = RegisterFrame(self)
        self.frames["register_frame"] = self.register_frame
        self.register_frame.pack(expand=True, fill="both") # Expand to fill the main app window

    def open_forgot_password_frame(self):
        self.main_frame.destroy()
        self.main_frame = MainFrame(self)
        self.forgot_password_frame = ForgotPasswordFrame(self)
        self.frames["forgot_password_frame"] = self.forgot_password_frame
        self.forgot_password_frame.pack(expand=True, fill="both")

    def open_main_frame(self):
        self.destroy_all_frames()
        self.main_frame = MainFrame(self)
        self.main_frame.pack(expand=True, fill="both")

    def destroy_all_frames(self):
        # Destroy all frames in the dictionary
        for frame_name, frame in self.frames.items():
            frame.destroy()
        self.frames = {}  # Clear the dictionary