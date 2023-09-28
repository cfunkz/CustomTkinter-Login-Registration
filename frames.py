import tkinter
import customtkinter
from functions import toggle_password, register_user, test_buttons, check_login, generate_temporary_password, send_password_reset_email, email_exists, update_password
from PIL import ImageTk, Image
from tkinter import messagebox
import pycountry

country_names_unsorted = [country.name for country in pycountry.countries]
country_names = sorted(country_names_unsorted)

class MainFrame(customtkinter.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master

        self.setup_login_frame()

    def setup_login_frame(self):

        #Create Login FRAME
        self.login_frame = customtkinter.CTkFrame(master=self, width=320, height=360)
        self.login_frame.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)

        #TOP text
        self.text = customtkinter.CTkLabel(master=self.login_frame, text="Log Into Account", font=('Century Gothic', 25))
        self.text.place(x=50, y=45)

        #Username entry block
        self.u_block = customtkinter.CTkEntry(master=self.login_frame, width=220, placeholder_text="Username")
        self.u_block.place(x=50, y=110)

        #Password entry block
        self.show_password_var = tkinter.BooleanVar()
        self.p_block = customtkinter.CTkEntry(master=self.login_frame, width=220, placeholder_text="Password", show="*")
        self.p_block.place(x=50, y=150)

        #checkbox for showing password
        self.show_password = customtkinter.CTkCheckBox(master=self.login_frame, text="Show Password", font=('Century Gothic', 12), command=lambda: toggle_password(self.p_block, self.show_password_var), variable=self.show_password_var)
        self.show_password.place(x=50, y=190)

        #Forgot password text
        self.label3 = customtkinter.CTkLabel(master=self.login_frame, text="Forgot password?", font=('Century Gothic', 10))
        self.label3.place(x=180, y=180)
        self.label3.bind("<Button-1>", lambda event: self.master.open_forgot_password_frame())

        #Login button
        self.login_button = customtkinter.CTkButton(master=self.login_frame, width=100, text="Login", corner_radius=6, fg_color="#72bcd4", text_color="#1e5364", hover_color="#e8f4f8", command=self.check_login_credentials)
        self.login_button.place(x=110, y=230)

        #Register button
        self.register_button = customtkinter.CTkButton(master=self.login_frame, width=100, text="Register", corner_radius=6, fg_color="#72bcd4", text_color="#1e5364", hover_color="#e8f4f8", command=self.master.open_register_frame)
        self.register_button.place(x=110, y=270)

        #Google and facebook logos
        self.g_logo = customtkinter.CTkImage(Image.open("images/g.png").resize((20, 20), Image.LANCZOS))
        self.fb_logo = customtkinter.CTkImage(Image.open("images/fb.png").resize((20, 20), Image.LANCZOS))

        #Google login button
        self.g_button = customtkinter.CTkButton(master=self.login_frame, width=100, image=self.g_logo, text="Google", corner_radius=6, fg_color="white", text_color="black", compound="left", hover_color="#e8f4f8", anchor="w", command=test_buttons)
        self.g_button.place(x=10, y=320)

        #Facebook login button
        self.fb_button = customtkinter.CTkButton(master=self.login_frame, width=100, image=self.fb_logo, text="Facebook", corner_radius=6, fg_color="white", text_color="black", compound="left", hover_color="#e8f4f8", anchor="w", command=test_buttons)
        self.fb_button.place(x=210, y=320)

    def check_login_credentials(self):
        # Get the username and password from the input fields
        username = self.u_block.get()
        password = self.p_block.get()

        # Call the check_login function from functions.py
        if check_login(username, password):
            # Login successful, open LoggedInFrame
            self.master.open_loggedin_frame()
        else:
            # Login failed, show an error message
            messagebox.showerror("Error", "Invalid username or password. Please try again.")

class RegisterFrame(customtkinter.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master

        self.setup_register_frame()

    def setup_register_frame(self):

        # Create the registration frame
        self.registration_frame = customtkinter.CTkFrame(master=self, width=320, height=360)
        self.registration_frame.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)

        self.back_button = customtkinter.CTkButton(
            master=self.registration_frame,
            width=30,
            height=30,
            text="◀️",  # Use the left arrow character as the text
            corner_radius=6,
            fg_color="#72bcd4",
            text_color="#1e5364",
            hover_color="#e8f4f8",
            command=self.master.open_main_frame
        )
        self.back_button.place(x=10, y=10)

        # Entry fields for registration form
        self.name_entry = customtkinter.CTkEntry(master=self.registration_frame, width=220, placeholder_text="First Name")
        self.name_entry.place(x=50, y=50)

        self.surname_entry = customtkinter.CTkEntry(master=self.registration_frame, width=220, placeholder_text="Last Name")
        self.surname_entry.place(x=50, y=80)

        self.country_box = customtkinter.CTkComboBox(master=self.registration_frame, values=country_names,
                                                          width=220)
        self.country_box.place(x=50, y=110)

        self.username_entry = customtkinter.CTkEntry(master=self.registration_frame, width=220, placeholder_text="Username")
        self.username_entry.place(x=50, y=140)

        self.email_entry = customtkinter.CTkEntry(master=self.registration_frame, width=220, placeholder_text="Enter your email")
        self.email_entry.place(x=50, y=170)

        self.p_block = customtkinter.CTkEntry(master=self.registration_frame, width=220, placeholder_text="Choose a password", show="*")
        self.p_block.place(x=50, y=200)

        # Registration button
        self.register_button = customtkinter.CTkButton(master=self.registration_frame, width=100, text="Register",
                                                  corner_radius=6,
                                                  fg_color="#72bcd4", text_color="#1e5364", hover_color="#e8f4f8",
                                                  command=self.new_user_data)
        self.register_button.place(x=110, y=260)

    def new_user_data(self):
        # Get user inputs from the registration form
        first_name = self.name_entry.get()
        last_name = self.surname_entry.get()
        country = self.country_box.get()
        username = self.username_entry.get()
        email = self.email_entry.get()
        password = self.p_block.get()

        # Call the register_user function from functions.py
        if register_user(first_name, last_name, country, username, email, password):
            # Registration successful
            print("Registration successful!")
            messagebox.showinfo("Success", "Registration was successful!")
            self.registration_frame.place_forget()
            return
        else:
            # Handle the case where the username or email is already taken
            print("Username or email is already in use.")
            messagebox.showerror("Error", "The username or e-mail already exists.")
            return


class ForgotPasswordFrame(customtkinter.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.setup_forgot_password_frame()  # Correct method name

    def setup_forgot_password_frame(self):  # Correct method name
        # Create the Forgot Password frame
        self.forgot_password_frame = customtkinter.CTkFrame(master=self, width=320, height=360)
        self.forgot_password_frame.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)

        self.back_button = customtkinter.CTkButton(
            master=self.forgot_password_frame,
            width=30,
            height=30,
            text="◀️",  # Use the left arrow character as the text
            corner_radius=6,
            fg_color="#72bcd4",
            text_color="#1e5364",
            hover_color="#e8f4f8",
            command=self.master.open_main_frame
        )
        self.back_button.place(x=10, y=10)

        self.text = customtkinter.CTkLabel(master=self.forgot_password_frame, text="Enter Your E-Mail", font=('Century Gothic', 25))
        self.text.place(x=50, y=45)
        # Email entry block
        self.email_block = customtkinter.CTkEntry(master=self.forgot_password_frame, width=220, placeholder_text="Email")
        self.email_block.place(x=50, y=110)
        # Submit button
        self.submit_button = customtkinter.CTkButton(master=self.forgot_password_frame, width=100, text="Submit", corner_radius=6, fg_color="#72bcd4", text_color="#1e5364", hover_color="#e8f4f8", command=self.handle_reset_password)
        self.submit_button.place(x=110, y=230)

    def handle_reset_password(self):
        # Get the user's email address from the entry field
        user_email = self.email_block.get()
        check_exists = email_exists(user_email)
        if check_exists:
            # Generate a temporary password (or token)
            temporary_password = generate_temporary_password()
            update_password(user_email, temporary_password)
            # Send the password reset email
            send_password_reset_email(user_email, temporary_password)
            # Inform the user (you can customize this part)
            messagebox.showinfo("Password Reset", "An email with instructions has been sent to your email address.")

            # Remove the ForgotPasswordFrame and show the login frame again
            self.forgot_password_frame.destroy()
            self.master.open_main_frame()
        else:
            messagebox.showerror("Error", "E-Mail doesn't exists!")


class LoggedInFrame(customtkinter.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.setup_loggedin_frame()

    def setup_loggedin_frame(self):
        self.master.change_geometry("1280x720")
        pass
