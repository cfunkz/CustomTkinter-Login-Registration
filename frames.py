import calendar
import io
import threading
import time
import tkinter
from datetime import date, datetime
from functools import lru_cache
from tkinter import messagebox
import customtkinter
from PIL import Image, ImageDraw, ImageOps
import config
from functions import (is_valid_chars_space, is_valid_chars, is_valid_password_chars, is_strong_password, password_strength,
                       check_security_answer, get_security_question, is_valid_email, get_countries, validate_country,
                       toggle_password, register_user, check_login, get_lockout_remaining, reset_password,
                       email_exists, username_exists, change_password, get_user_data, update_user_profile, delete_user,
                       oauth_login_user, get_system_info, get_public_ip, format_duration, add_todo, get_todos, group_todos,
                       set_todo_done, delete_todo, get_due_todos, mark_todo_notified, update_webhook_url, send_webhook,
                       get_gravatar, delete_old_todos, update_archive_days)
from oauth import oauth_sign_in, get_display_providers, get_provider_name, is_provider_configured, OAuthError

# ---------------------------------------------------------------- Style
# Colors are (light mode, dark mode) pairs, customtkinter picks the right one
BACKGROUND_COLOR = ("#F3F4F6", "#0F172A")
CARD_COLOR = ("#FFFFFF", "#1E293B")
INPUT_COLOR = ("#F9FAFB", "#0F172A")
BORDER_COLOR = ("#E5E7EB", "#334155")
TEXT_COLOR = ("#111827", "#F1F5F9")
MUTED_TEXT_COLOR = ("#6B7280", "#94A3B8")
HOVER_COLOR = ("#F3F4F6", "#334155")
ACCENT_COLOR = config.accent_color
ACCENT_HOVER_COLOR = config.accent_hover_color
DANGER_COLOR = config.danger_color
DANGER_HOVER_COLOR = config.danger_hover_color
SUCCESS_COLOR = config.success_color

# Squarish corners
CARD_RADIUS = 6
WIDGET_RADIUS = 4

FORM_WIDTH = 360
FIELD_HEIGHT = 40

# Logos for the social login buttons
PROVIDER_LOGOS = {
    "google": config.resource_path("images/g.png"),
    "facebook": config.resource_path("images/fb.png"),
    "discord": config.resource_path("images/discord.png"),
}

# Strength meter labels and colors (index = score from password_strength)
STRENGTH_TEXT = ["Very weak", "Weak", "Fair", "Good", "Strong"]
STRENGTH_COLORS = ["#EF4444", "#F97316", "#EAB308", "#22C55E", "#16A34A"]

# How often the todo list checks for tasks that are due (milliseconds)
TODO_CHECK_INTERVAL = 30000

SECURITY_QUESTIONS = ["What is your mother's maiden name?", "What is your favorite pet's name?", "Where were you born?",
                      "What is your favorite movie?", "What is your favorite book?"]

# ---------------------------------------------------------------- UI helper functions

@lru_cache(maxsize=None)
def font(size=13, weight="normal"):
    # Shared fonts, created once and reused
    return customtkinter.CTkFont(family=config.font_family, size=size, weight=weight)

@lru_cache(maxsize=None)
def load_image(path, size):
    # Load an image once and reuse it (the logos are large files)
    image = Image.open(path)
    image.thumbnail((size[0] * 2, size[1] * 2), Image.LANCZOS)  # 2x for sharp images on high DPI screens
    return customtkinter.CTkImage(light_image=image, size=size)

def avatar_image(data, size):
    # Turn downloaded picture bytes into a square image with slightly rounded corners
    image = ImageOps.fit(Image.open(io.BytesIO(data)).convert("RGBA"), (size * 2, size * 2), Image.LANCZOS)
    mask = Image.new("L", image.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, image.width - 1, image.height - 1), radius=WIDGET_RADIUS * 2, fill=255)
    image.putalpha(mask)
    return customtkinter.CTkImage(light_image=image, size=(size, size))

def create_title(master, title, subtitle=""):
    # Large title with a muted subtitle underneath
    customtkinter.CTkLabel(master=master, text=title, font=font(26, "bold"), text_color=TEXT_COLOR, anchor="w").pack(fill="x")
    if subtitle:
        customtkinter.CTkLabel(master=master, text=subtitle, font=font(13), text_color=MUTED_TEXT_COLOR, anchor="w",
                               justify="left", wraplength=FORM_WIDTH).pack(fill="x", pady=(2, 0))
    customtkinter.CTkFrame(master=master, height=14, fg_color="transparent").pack()  # Space under the title

def create_entry(master, placeholder, show="", width=FORM_WIDTH):
    # Rounded input field
    return customtkinter.CTkEntry(master=master, width=width, height=FIELD_HEIGHT, placeholder_text=placeholder, show=show,
                                  corner_radius=WIDGET_RADIUS, border_width=1, border_color=BORDER_COLOR, fg_color=INPUT_COLOR,
                                  text_color=TEXT_COLOR, font=font(13))

def create_combobox(master, variable, values, width=FORM_WIDTH):
    # Read-only dropdown that matches the input fields
    return customtkinter.CTkComboBox(master=master, variable=variable, values=values, width=width, height=FIELD_HEIGHT,
                                     state="readonly", corner_radius=WIDGET_RADIUS, border_width=1, border_color=BORDER_COLOR,
                                     fg_color=INPUT_COLOR, button_color=BORDER_COLOR, button_hover_color=ACCENT_COLOR,
                                     text_color=TEXT_COLOR, font=font(13), dropdown_font=font(12))

def create_button(master, text, command, style="primary", width=FORM_WIDTH, height=FIELD_HEIGHT, image=None):
    # Buttons in four styles: primary, secondary, danger and ghost
    styles = {
        "primary": {"fg_color": ACCENT_COLOR, "hover_color": ACCENT_HOVER_COLOR, "text_color": "#FFFFFF", "border_width": 0},
        "secondary": {"fg_color": CARD_COLOR, "hover_color": HOVER_COLOR, "text_color": TEXT_COLOR, "border_width": 1},
        "danger": {"fg_color": DANGER_COLOR, "hover_color": DANGER_HOVER_COLOR, "text_color": "#FFFFFF", "border_width": 0},
        "ghost": {"fg_color": "transparent", "hover_color": HOVER_COLOR, "text_color": TEXT_COLOR, "border_width": 0},
    }
    return customtkinter.CTkButton(master=master, text=text, command=command, width=width, height=height, corner_radius=WIDGET_RADIUS,
                                   border_color=BORDER_COLOR, font=font(13, "bold"), image=image, **styles[style])

def create_link(master, text, command, size=12):
    # Clickable text in the accent color
    link = customtkinter.CTkLabel(master=master, text=text, font=font(size, "bold"), text_color=ACCENT_COLOR, cursor="hand2")
    link.bind("<Button-1>", lambda event: command())
    return link

def create_status_label(master):
    # Label for inline error and success messages (hidden while empty)
    return customtkinter.CTkLabel(master=master, text="", font=font(12), anchor="w", justify="left", wraplength=FORM_WIDTH)

def show_status(label, text, kind="error"):
    # Show an error, success or info message in a status label
    colors = {"error": DANGER_COLOR, "success": SUCCESS_COLOR, "info": MUTED_TEXT_COLOR}
    label.configure(text=text, text_color=colors[kind])

def create_strength_meter(master, width=FORM_WIDTH):
    # Thin colored bar with a label that shows password strength
    meter = customtkinter.CTkFrame(master=master, fg_color="transparent")
    meter.bar = customtkinter.CTkProgressBar(master=meter, width=width, height=6, corner_radius=3, progress_color=BORDER_COLOR,
                                             fg_color=BORDER_COLOR)
    meter.bar.set(0)
    meter.bar.pack(fill="x", pady=(2, 0))
    meter.label = customtkinter.CTkLabel(master=meter, text="", font=font(11), height=16, anchor="w", text_color=MUTED_TEXT_COLOR)
    meter.label.pack(fill="x")
    return meter

def update_strength_meter(meter, password):
    # Update the strength meter while the user types
    if not password:
        meter.bar.set(0)
        meter.label.configure(text="")
        return
    score = password_strength(password)
    meter.bar.configure(progress_color=STRENGTH_COLORS[score])
    meter.bar.set(max(score, 1) / 4)
    meter.label.configure(text=f"Password strength: {STRENGTH_TEXT[score]}", text_color=STRENGTH_COLORS[score])

def create_appearance_menu(master):
    # Switch between System, Light and Dark mode
    menu = customtkinter.CTkOptionMenu(master=master, values=["System", "Light", "Dark"], width=110, height=30, corner_radius=WIDGET_RADIUS,
                                       font=font(12), dropdown_font=font(12), fg_color=CARD_COLOR, button_color=CARD_COLOR,
                                       button_hover_color=HOVER_COLOR, text_color=TEXT_COLOR,
                                       command=customtkinter.set_appearance_mode)
    menu.set(customtkinter.get_appearance_mode() if config.appearance_mode.lower() != "system" else "System")
    return menu

def create_card(master, title, subtitle=""):
    # Rounded card with a heading, returns the card and the frame to put content in
    card = customtkinter.CTkFrame(master=master, fg_color=CARD_COLOR, corner_radius=CARD_RADIUS, border_width=1, border_color=BORDER_COLOR)
    customtkinter.CTkLabel(master=card, text=title, font=font(16, "bold"), text_color=TEXT_COLOR, anchor="w").pack(fill="x", padx=24, pady=(20, 0))
    if subtitle:
        customtkinter.CTkLabel(master=card, text=subtitle, font=font(12), text_color=MUTED_TEXT_COLOR, anchor="w").pack(fill="x", padx=24)
    body = customtkinter.CTkFrame(master=card, fg_color="transparent")
    body.pack(fill="both", expand=True, padx=24, pady=(12, 20))
    return card, body

def run_in_background(widget, task, on_done):
    # Run a slow task (email, OAuth) in a thread so the window doesn't freeze, then call on_done(result, error) in the UI thread
    result = {}

    def worker():
        try:
            result["value"] = task()
        except Exception as e:
            result["error"] = e

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    root = widget.winfo_toplevel()

    def check():
        if thread.is_alive():
            root.after(100, check)
            return
        try:
            if widget.winfo_exists():  # The user may have left this screen
                on_done(result.get("value"), result.get("error"))
        except tkinter.TclError:
            pass

    root.after(100, check)

class PasswordDialog(customtkinter.CTkInputDialog):
    # Input dialog that hides what is typed, used to confirm the password
    def _create_widgets(self):
        super()._create_widgets()
        self._entry.configure(show="*")

class CalendarPopup(customtkinter.CTkToplevel):
    # Small window to pick a day and a time, calls on_pick("2024-01-31 18:30")
    def __init__(self, master, on_pick):
        super().__init__(master)
        self.title("Pick a date")
        self.resizable(False, False)
        self.configure(fg_color=BACKGROUND_COLOR)
        self.geometry(f"+{master.winfo_rootx() + 400}+{master.winfo_rooty() + 120}")  # Open over the dashboard
        self.on_pick = on_pick
        today = date.today()
        self.year, self.month, self.day = today.year, today.month, today.day

        # Month name with previous and next buttons
        header = customtkinter.CTkFrame(master=self, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(16, 8))
        create_button(header, "<", lambda: self.change_month(-1), style="secondary", width=36, height=32).pack(side="left")
        create_button(header, ">", lambda: self.change_month(1), style="secondary", width=36, height=32).pack(side="right")
        self.month_label = customtkinter.CTkLabel(master=header, text="", font=font(14, "bold"), text_color=TEXT_COLOR)
        self.month_label.pack(side="left", expand=True)

        # Grid of days, filled in by show_month
        self.days = customtkinter.CTkFrame(master=self, fg_color="transparent")
        self.days.pack(padx=16)

        # Hour and minute, starts at the next full hour
        time_row = customtkinter.CTkFrame(master=self, fg_color="transparent")
        time_row.pack(fill="x", padx=16, pady=(12, 16))
        self.hour_var = customtkinter.StringVar(value=f"{(datetime.now().hour + 1) % 24:02d}")
        self.minute_var = customtkinter.StringVar(value="00")
        create_combobox(time_row, self.hour_var, [f"{hour:02d}" for hour in range(24)], width=76).pack(side="left")
        customtkinter.CTkLabel(master=time_row, text=":", font=font(14, "bold"), text_color=TEXT_COLOR).pack(side="left", padx=4)
        create_combobox(time_row, self.minute_var, [f"{minute:02d}" for minute in range(0, 60, 5)], width=76).pack(side="left")
        create_button(time_row, "Set", self.pick, width=80).pack(side="right")
        create_button(time_row, "No time", self.clear, style="secondary", width=80).pack(side="right", padx=(0, 6))

        self.show_month()
        self.after(100, self.grab_set)  # Keep focus on the popup until it is closed

    def change_month(self, step):
        self.month += step
        if self.month == 0:
            self.year, self.month = self.year - 1, 12
        elif self.month == 13:
            self.year, self.month = self.year + 1, 1
        self.day = 1
        self.show_month()

    def select_day(self, day):
        self.day = day
        self.show_month()

    def show_month(self):
        for widget in self.days.winfo_children():
            widget.destroy()
        self.month_label.configure(text=f"{calendar.month_name[self.month]} {self.year}")
        for column, name in enumerate(("Mo", "Tu", "We", "Th", "Fr", "Sa", "Su")):
            customtkinter.CTkLabel(master=self.days, text=name, width=36, font=font(11), text_color=MUTED_TEXT_COLOR).grid(row=0, column=column)
        today = date.today()
        for row, week in enumerate(calendar.monthcalendar(self.year, self.month), start=1):
            for column, day in enumerate(week):
                if not day:
                    continue
                past = date(self.year, self.month, day) < today
                style = "primary" if day == self.day else "ghost"
                button = create_button(self.days, str(day), lambda d=day: self.select_day(d), style=style, width=36, height=32)
                if past:
                    button.configure(state="disabled", text_color_disabled=MUTED_TEXT_COLOR)
                button.grid(row=row, column=column, padx=1, pady=1)

    def clear(self):
        self.on_pick("")
        self.destroy()

    def pick(self):
        self.on_pick(f"{self.year}-{self.month:02d}-{self.day:02d} {self.hour_var.get()}:{self.minute_var.get()}")
        self.destroy()

# ---------------------------------------------------------------- Shared layouts

class AuthFrame(customtkinter.CTkFrame):
    # Base layout for every sign-in screen: back button, appearance menu and a centered form
    def __init__(self, master, window_title, show_back=False):
        super().__init__(master, fg_color=BACKGROUND_COLOR, corner_radius=0)
        self.master = master
        self.master.change_title(f"{window_title} - {config.app_name}")
        self.master.change_geometry(config.auth_window_size)

        if show_back:
            self.back_button = create_button(self, "←  Back", self.master.open_main_frame, style="ghost", width=90, height=32)
            self.back_button.place(x=20, y=20)

        self.appearance_menu = create_appearance_menu(self)
        self.appearance_menu.place(relx=1.0, x=-20, y=20, anchor="ne")

        self.form = customtkinter.CTkFrame(master=self, fg_color="transparent")
        self.form.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)

        # App name above every form
        customtkinter.CTkLabel(master=self.form, text=config.app_name, font=font(13, "bold"), text_color=ACCENT_COLOR, anchor="w").pack(fill="x")

    def create_footer(self, text, link_text, command):
        # "No account? Register" style footer under the form
        footer = customtkinter.CTkFrame(master=self.form, fg_color="transparent")
        footer.pack(pady=(16, 0))
        if text:
            customtkinter.CTkLabel(master=footer, text=text, font=font(12), text_color=MUTED_TEXT_COLOR).pack(side="left", padx=(0, 6))
        create_link(footer, link_text, command).pack(side="left")

class ChangePasswordForm(customtkinter.CTkFrame):
    # Change password fields, used after a password reset and on the dashboard
    def __init__(self, master, username, on_success, password_set=True, width=FORM_WIDTH):
        super().__init__(master, fg_color="transparent")
        self.username = username
        self.on_success = on_success
        self.password_set = password_set

        # Social login accounts without a password don't need the current password
        if self.password_set:
            self.old_block = create_entry(self, "Current or temporary password", show="*", width=width)
            self.old_block.pack(fill="x", pady=(0, 10))

        self.new_block = create_entry(self, "New password", show="*", width=width)
        self.new_block.pack(fill="x")
        self.strength_meter = create_strength_meter(self, width=width)
        self.strength_meter.pack(fill="x", pady=(0, 6))
        self.new_block.bind("<KeyRelease>", lambda event: update_strength_meter(self.strength_meter, self.new_block.get()))

        self.confirm_block = create_entry(self, "Confirm new password", show="*", width=width)
        self.confirm_block.pack(fill="x")
        self.confirm_block.bind("<Return>", lambda event: self.handle_change_password())

        self.status_label = create_status_label(self)
        self.status_label.pack(fill="x", pady=(6, 0))

        self.save_button = create_button(self, "Change Password" if self.password_set else "Set Password", self.handle_change_password, width=width)
        self.save_button.pack(fill="x", pady=(6, 0))

    def handle_change_password(self):
        old_password = self.old_block.get() if self.password_set else ""
        new_password = self.new_block.get()
        confirm_password = self.confirm_block.get()

        if not is_valid_password_chars(new_password):
            show_status(self.status_label, "Password can't contain spaces or non-English characters.")
            return
        if not is_strong_password(new_password):
            show_status(self.status_label, f"Use at least {config.min_password_length} characters with a letter and a number.")
            return
        if new_password != confirm_password:
            show_status(self.status_label, "Passwords do not match.")
            return

        success, message = change_password(self.username, old_password, new_password)
        if success:
            self.on_success(message)
        else:
            show_status(self.status_label, message)

# ---------------------------------------------------------------- Screens

class MainFrame(AuthFrame):
    def __init__(self, master, message=None, kind="success"):
        super().__init__(master, "Login")
        self.setup_login_frame()
        # Message from the previous screen, e.g. "Registration was successful"
        if message:
            show_status(self.error_label, message, kind)

    def setup_login_frame(self):
        #TOP text
        create_title(self.form, "Login")

        self.error_label = create_status_label(self.form)
        self.error_label.pack(fill="x")

        #Username entry block
        self.u_block = create_entry(self.form, "Username or email")
        self.u_block.pack(fill="x", pady=(4, 10))

        #Password entry block
        self.p_block = create_entry(self.form, "Password", show="*")
        self.p_block.pack(fill="x")

        #Show password checkbox and forgot password link
        options_row = customtkinter.CTkFrame(master=self.form, fg_color="transparent")
        options_row.pack(fill="x", pady=10)
        self.show_password_var = customtkinter.BooleanVar()
        self.show_password = customtkinter.CTkCheckBox(master=options_row, text="Show password", font=font(12), text_color=MUTED_TEXT_COLOR,
                                                       checkbox_width=18, checkbox_height=18, corner_radius=3, border_width=2,
                                                       fg_color=ACCENT_COLOR, hover_color=ACCENT_HOVER_COLOR, variable=self.show_password_var,
                                                       command=lambda: toggle_password(self.p_block, self.show_password_var))
        self.show_password.pack(side="left")
        self.forgot_link = create_link(options_row, "Forgot password?", self.master.open_forgot_password_frame)
        self.forgot_link.pack(side="right")

        #Login button
        self.login_button = create_button(self.form, "Login", self.check_login_credentials)
        self.login_button.pack(fill="x", pady=(4, 0))

        #Social login buttons
        self.social_buttons = {}
        providers = get_display_providers()
        if providers:
            self.setup_social_buttons(providers)

        self.create_footer("No account?", "Register", self.master.open_register_frame)

        # Press Enter to log in and start typing in the username field straight away
        self.u_block.bind("<Return>", lambda event: self.p_block.focus())
        self.p_block.bind("<Return>", lambda event: self.check_login_credentials())
        self.u_block.focus()

    def setup_social_buttons(self, providers):
        # "or continue with" divider and one button per provider
        divider = customtkinter.CTkFrame(master=self.form, fg_color="transparent")
        divider.pack(fill="x", pady=16)
        divider.grid_columnconfigure((0, 2), weight=1)
        customtkinter.CTkFrame(master=divider, height=1, fg_color=BORDER_COLOR).grid(row=0, column=0, sticky="ew")
        customtkinter.CTkLabel(master=divider, text="or", font=font(12), text_color=MUTED_TEXT_COLOR).grid(row=0, column=1, padx=12)
        customtkinter.CTkFrame(master=divider, height=1, fg_color=BORDER_COLOR).grid(row=0, column=2, sticky="ew")

        social_row = customtkinter.CTkFrame(master=self.form, fg_color="transparent")
        social_row.pack(fill="x")
        button_width = (FORM_WIDTH - 10 * (len(providers) - 1)) // len(providers)
        for index, provider in enumerate(providers):
            social_row.grid_columnconfigure(index, weight=1)
            logo = load_image(PROVIDER_LOGOS[provider], (18, 18)) if provider in PROVIDER_LOGOS else None
            button = create_button(social_row, get_provider_name(provider), lambda p=provider: self.start_oauth_login(p),
                                   style="secondary", width=button_width, image=logo)
            button.grid(row=0, column=index, sticky="ew", padx=(0 if index == 0 else 10, 0))
            self.social_buttons[provider] = button

    def check_login_credentials(self):
        # Get the username and password from the input fields
        username = self.u_block.get().strip()
        password = self.p_block.get()

        if not username or not password:
            show_status(self.error_label, "Please enter your username and password.")
            return

        # Call the check_login function from functions.py
        status, db_username = check_login(username, password)
        if status == "ok":
            # Login successful, open LoggedInFrame
            self.master.open_loggedin_frame(db_username)
        elif status == "change_password":
            # Logged in with a temporary password, a new password must be chosen first
            self.master.open_change_password_frame(db_username)
        elif status == "locked":
            minutes = max(1, round(get_lockout_remaining(db_username) / 60))
            show_status(self.error_label, f"Too many failed attempts. Try again in {minutes} min.")
            self.p_block.delete(0, "end")
        else:
            # Login failed, show an error message
            show_status(self.error_label, "Invalid username or password. Please try again.")
            self.p_block.delete(0, "end")

    def start_oauth_login(self, provider):
        # Sign in with Google, Facebook or Discord in the browser
        name = get_provider_name(provider)
        if not is_provider_configured(provider):
            show_status(self.error_label, f"{name} sign-in is not set up yet. Add {provider.upper()}_CLIENT_ID and "
                                          f"{provider.upper()}_CLIENT_SECRET to your .env file.")
            return

        show_status(self.error_label, f"Complete the {name} sign-in in your browser...", "info")
        self.set_social_buttons_state("disabled")
        run_in_background(self, lambda: oauth_login_user(oauth_sign_in(provider)), self.finish_oauth_login)

    def finish_oauth_login(self, result, error):
        # Called when the browser sign-in has finished
        self.set_social_buttons_state("normal")
        if isinstance(error, OAuthError):
            show_status(self.error_label, str(error))
            return
        if error:
            print("OAuth error:", error)
            show_status(self.error_label, "Social sign-in failed. Please try again.")
            return

        status, username = result
        if status == "email_in_use":
            show_status(self.error_label, "This email is already registered. Sign in with your password instead.")
            return
        self.master.open_loggedin_frame(username)

    def set_social_buttons_state(self, state):
        # Enable or disable all social login buttons
        for button in self.social_buttons.values():
            button.configure(state=state)

class RegisterFrame(AuthFrame):
    def __init__(self, master):
        super().__init__(master, "Register", show_back=True)
        self.setup_register_frame()

    def setup_register_frame(self):
        half_width = (FORM_WIDTH - 10) // 2
        create_title(self.form, "Register")

        # Two fields next to each other
        def create_row():
            row = customtkinter.CTkFrame(master=self.form, fg_color="transparent")
            row.pack(fill="x", pady=(0, 10))
            return row

        name_row = create_row()
        self.name_entry = create_entry(name_row, "First name", width=half_width)
        self.name_entry.pack(side="left")
        self.surname_entry = create_entry(name_row, "Last name", width=half_width)
        self.surname_entry.pack(side="right")

        account_row = create_row()
        self.username_entry = create_entry(account_row, "Username", width=half_width)
        self.username_entry.pack(side="left")
        # Dropdown with every country
        self.country_var = customtkinter.StringVar(value="Select Country")
        self.country_box = create_combobox(account_row, self.country_var, get_countries(), width=half_width)
        self.country_box.pack(side="right")

        self.email_entry = create_entry(self.form, "Email address")
        self.email_entry.pack(fill="x", pady=(0, 10))

        password_row = create_row()
        password_row.pack_configure(pady=0)
        self.p_block = create_entry(password_row, "Password", show="*", width=half_width)
        self.p_block.pack(side="left")
        self.confirm_block = create_entry(password_row, "Confirm password", show="*", width=half_width)
        self.confirm_block.pack(side="right")

        # Password strength meter, updates on every key press
        self.strength_meter = create_strength_meter(self.form)
        self.strength_meter.pack(fill="x", pady=(0, 6))
        self.p_block.bind("<KeyRelease>", lambda event: update_strength_meter(self.strength_meter, self.p_block.get()))

        self.security_questions = SECURITY_QUESTIONS
        self.security_question_var = customtkinter.StringVar(value="Select Security Question")
        self.security_question_dropdown = create_combobox(self.form, self.security_question_var, self.security_questions)
        self.security_question_dropdown.pack(fill="x", pady=(0, 10))

        # Security Answer entry field
        self.security_answer_entry = create_entry(self.form, "Security answer")
        self.security_answer_entry.pack(fill="x")

        self.error_label = create_status_label(self.form)
        self.error_label.pack(fill="x", pady=(4, 0))

        # Registration button
        self.register_button = create_button(self.form, "Register", self.new_user_data)
        self.register_button.pack(fill="x", pady=(4, 0))

        self.create_footer("Have an account?", "Login", self.master.open_main_frame)
        self.name_entry.focus()

    def new_user_data(self):
        # Get user inputs from the registration form
        first_name = self.name_entry.get().strip()
        last_name = self.surname_entry.get().strip()
        country = self.country_box.get()
        username = self.username_entry.get().strip()
        email = self.email_entry.get().strip()
        password = self.p_block.get()
        confirm_password = self.confirm_block.get()
        security_question = self.security_question_var.get()  # Get the selected security question
        security_answer = self.security_answer_entry.get().strip()

        if not first_name or not last_name or not username or not password or not security_answer:
            show_status(self.error_label, "Please fill in all required fields.")
            return
        if not is_valid_chars_space(first_name) or not is_valid_chars_space(last_name):
            show_status(self.error_label, "Names can only use English letters.")
            return
        # Check if username contains only English letters and standard characters
        if not is_valid_chars(username) or not 3 <= len(username) <= 20:
            show_status(self.error_label, "Username must be 3-20 English letters, digits, '_' or '-' without spaces.")
            return
        if not validate_country(country):
            show_status(self.error_label, "Please select a country.")
            return
        if not is_valid_email(email):
            show_status(self.error_label, "Please enter a valid email address.")
            return
        if not is_valid_password_chars(password):
            show_status(self.error_label, "Password can't contain spaces or non-English characters.")
            return
        if not is_strong_password(password):
            show_status(self.error_label, f"Password needs at least {config.min_password_length} characters with a letter and a number.")
            return
        if password != confirm_password:
            show_status(self.error_label, "Passwords do not match.")
            return
        if security_question not in self.security_questions:
            show_status(self.error_label, "Please select a security question.")
            return
        # Tell the user exactly which field is taken
        if username_exists(username):
            show_status(self.error_label, "That username is already taken.")
            return
        if email_exists(email):
            show_status(self.error_label, "That email is already registered.")
            return
        # Call the register_user function from functions.py
        if register_user(first_name, last_name, country, username, email, password, security_question, security_answer):
            # Registration successful
            self.master.open_main_frame("Registration was successful.")
        else:
            show_status(self.error_label, "The username or e-mail already exists.")


class ForgotPasswordFrame(AuthFrame):
    def __init__(self, master):
        super().__init__(master, "Forgot Password", show_back=True)
        self.setup_forgot_password_frame()

    def setup_forgot_password_frame(self):
        create_title(self.form, "Forgot Password", "Enter the email of your account.")

        # Email entry block
        self.email_block = create_entry(self.form, "Email address")
        self.email_block.pack(fill="x")
        self.email_block.bind("<Return>", lambda event: self.handle_reset_password())
        self.email_block.focus()

        self.error_label = create_status_label(self.form)
        self.error_label.pack(fill="x", pady=(4, 0))

        # Submit button
        self.submit_button = create_button(self.form, "Submit", self.handle_reset_password)
        self.submit_button.pack(fill="x", pady=(4, 0))

        
    def handle_reset_password(self):
        # Get the user's email address from the entry field
        user_email = self.email_block.get().strip()
        # Validate the format first, so the database is only queried for real emails
        if not is_valid_email(user_email):
            show_status(self.error_label, "Please enter a valid email address.")
            return
        if not email_exists(user_email):
            show_status(self.error_label, "No account uses this email address.")
            return
        # Accounts created with Google, Facebook or Discord have no security question
        if not get_security_question(user_email):
            show_status(self.error_label, "This account was created with a social sign-in. Use that button on the sign-in page.")
            return
        # Show the next step/frame
        self.master.open_forgot_password_frame2(user_email)

class ForgotPasswordFrame2(AuthFrame):
    def __init__(self, master, user_email):
        super().__init__(master, "Security Question", show_back=True)
        self.user_email = user_email
        self.attempts_left = config.max_security_attempts
        self.setup_forgot_password_frame2()

    def setup_forgot_password_frame2(self):
        create_title(self.form, "Security Question", self.user_email)

        # Security Question label
        security_question = get_security_question(self.user_email)
        self.security_question_label = customtkinter.CTkLabel(master=self.form, text=security_question, font=font(14, "bold"),
                                                              text_color=TEXT_COLOR, anchor="w", justify="left", wraplength=FORM_WIDTH)
        self.security_question_label.pack(fill="x", pady=(0, 10))

        # Security Answer entry block
        self.security_answer_block = create_entry(self.form, "Your answer")
        self.security_answer_block.pack(fill="x")
        self.security_answer_block.bind("<Return>", lambda event: self.handle_reset_password())
        self.security_answer_block.focus()

        self.error_label = create_status_label(self.form)
        self.error_label.pack(fill="x", pady=(4, 0))

        # Submit button for step 2
        self.submit_button2 = create_button(self.form, "Reset Password", self.handle_reset_password)
        self.submit_button2.pack(fill="x", pady=(4, 0))

    def handle_reset_password(self):
        # Get the user's security answer
        user_answer = self.security_answer_block.get()

        # Check if the security answer is correct
        if check_security_answer(self.user_email, user_answer):
            # Disable the button while the email is being sent so it can't be clicked twice
            self.submit_button2.configure(state="disabled", text="Sending...")
            # Email a temporary password in the background, it is only saved if the email was sent
            run_in_background(self, lambda: reset_password(self.user_email), self.finish_reset_password)
        else:
            # Limit guesses so the security answer can't be brute forced
            self.attempts_left -= 1
            if self.attempts_left <= 0:
                self.master.open_main_frame("Too many wrong answers. Please start again.", "error")
                return
            show_status(self.error_label, f"Security answer does not match. {self.attempts_left} attempt(s) left.")

    def finish_reset_password(self, sent, error):
        # Called when the email has been sent (or failed)
        if sent and not error:
            self.master.open_main_frame("A temporary password has been sent to your email.")
        else:
            show_status(self.error_label, "Could not send the email. Please check the SMTP settings and try again.")
            self.submit_button2.configure(state="normal", text="Reset Password")

class ChangePasswordFrame(AuthFrame):
    # Shown after logging in with a temporary password
    def __init__(self, master, username):
        super().__init__(master, "Change Password")
        self.username = username
        self.setup_change_password_frame()

    def setup_change_password_frame(self):
        create_title(self.form, "Change Password", "Choose a new password to replace the temporary one.")
        self.change_password_form = ChangePasswordForm(self.form, self.username, self.finish_change_password)
        self.change_password_form.pack(fill="x")
        self.create_footer("", "Logout", self.master.open_main_frame)

    def finish_change_password(self, message):
        self.master.open_loggedin_frame(self.username)

class LoggedInFrame(customtkinter.CTkFrame):
    def __init__(self, master, username):
        super().__init__(master, fg_color=BACKGROUND_COLOR, corner_radius=0)
        self.master = master
        self.username = username
        self.nav_buttons = {}
        self.login_time = time.time()  # For the session timer on the Device page
        self.gravatar = None  # Profile picture bytes from Gravatar, None until loaded
        self.setup_loggedin_frame()
        self.check_todo_alarms()

    def setup_loggedin_frame(self):
        self.master.change_geometry(config.dashboard_window_size)
        self.master.change_title(f"Dashboard - {config.app_name}")
        self.user = get_user_data(self.username) or {}

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.setup_sidebar()

        # Page area on the right
        self.page_area = customtkinter.CTkFrame(master=self, fg_color="transparent")
        self.page_area.grid(row=0, column=1, sticky="nsew", padx=36, pady=28)
        self.page = None
        self.current_page = None
        self.show_page("profile")

        # Load the profile picture in the background, get_gravatar keeps it in memory until the app restarts
        run_in_background(self, lambda: get_gravatar(self.user.get("email")), self.show_gravatar)

    def show_gravatar(self, data, error):
        # Replace the initials with the Gravatar picture (if the user has one)
        if not data:
            return
        self.gravatar = data
        self.avatar.configure(image=avatar_image(data, 64), text="", fg_color="transparent")
        if self.current_page == "profile":
            self.profile_avatar.configure(image=avatar_image(data, 72), text="", fg_color="transparent")

    def setup_sidebar(self):
        self.sidebar = customtkinter.CTkFrame(master=self, width=250, fg_color=CARD_COLOR, corner_radius=0, border_width=0)
        self.sidebar.grid(row=0, column=0, sticky="ns")
        self.sidebar.grid_propagate(False)
        self.sidebar.pack_propagate(False)

        customtkinter.CTkLabel(master=self.sidebar, text=config.app_name, font=font(16, "bold"), text_color=TEXT_COLOR, anchor="w").pack(fill="x", padx=24, pady=(24, 24))

        # Avatar with the user's initials, replaced by the Gravatar picture once it is loaded
        first_name = self.user.get("first_name") or self.username
        initials = (first_name[:1] + (self.user.get("last_name") or "")[:1]).upper()
        self.initials = initials
        self.avatar = customtkinter.CTkLabel(master=self.sidebar, text=initials, width=64, height=64, corner_radius=WIDGET_RADIUS,
                                             fg_color=ACCENT_COLOR, text_color="#FFFFFF", font=font(22, "bold"))
        self.avatar.pack(padx=24, anchor="w")
        self.name_label = customtkinter.CTkLabel(master=self.sidebar, text=f"{first_name} {self.user.get('last_name') or ''}".strip(),
                                                 font=font(15, "bold"), text_color=TEXT_COLOR, anchor="w")
        self.name_label.pack(fill="x", padx=24, pady=(10, 0))
        customtkinter.CTkLabel(master=self.sidebar, text=self.user.get("email") or f"@{self.username}", font=font(12),
                               text_color=MUTED_TEXT_COLOR, anchor="w").pack(fill="x", padx=24, pady=(0, 24))

        # Navigation
        for page, text in (("profile", "Profile"), ("security", "Security"), ("device", "Device"), ("todo", "Todo")):
            button = customtkinter.CTkButton(master=self.sidebar, text=text, height=38, corner_radius=WIDGET_RADIUS, anchor="w", font=font(13),
                                             fg_color="transparent", hover_color=HOVER_COLOR, text_color=TEXT_COLOR,
                                             command=lambda p=page: self.show_page(p))
            button.pack(fill="x", padx=16, pady=2)
            self.nav_buttons[page] = button

        # Bottom of the sidebar
        self.logout_button = create_button(self.sidebar, "Logout", self.master.open_main_frame, style="secondary", width=218)
        self.logout_button.pack(side="bottom", padx=16, pady=(8, 24))
        self.appearance_menu = create_appearance_menu(self.sidebar)
        self.appearance_menu.configure(width=218)
        self.appearance_menu.pack(side="bottom", padx=16)
        customtkinter.CTkLabel(master=self.sidebar, text="Appearance", font=font(11), text_color=MUTED_TEXT_COLOR, anchor="w").pack(side="bottom", fill="x", padx=18)

    def show_page(self, page):
        # Switch between the dashboard pages
        if self.page is not None:
            self.page.destroy()
        self.current_page = page
        for name, button in self.nav_buttons.items():
            button.configure(fg_color=HOVER_COLOR if name == page else "transparent", font=font(13, "bold" if name == page else "normal"))

        self.page = customtkinter.CTkFrame(master=self.page_area, fg_color="transparent")
        self.page.pack(fill="both", expand=True)
        if page == "profile":
            self.setup_profile_page()
        elif page == "security":
            self.setup_security_page()
        elif page == "device":
            self.setup_device_page()
        else:
            self.setup_todo_page()

    def create_page_header(self, title):
        customtkinter.CTkLabel(master=self.page, text=title, font=font(24, "bold"), text_color=TEXT_COLOR, anchor="w").pack(fill="x", pady=(0, 18))

    def setup_profile_page(self):
        self.create_page_header("Profile")

        # Profile picture from Gravatar (initials until it is loaded) next to the name
        top = customtkinter.CTkFrame(master=self.page, fg_color="transparent")
        top.pack(fill="x", pady=(0, 16))
        self.profile_avatar = customtkinter.CTkLabel(master=top, text=self.initials, width=72, height=72, corner_radius=WIDGET_RADIUS,
                                                     fg_color=ACCENT_COLOR, text_color="#FFFFFF", font=font(24, "bold"))
        if self.gravatar:
            self.profile_avatar.configure(image=avatar_image(self.gravatar, 72), text="", fg_color="transparent")
        self.profile_avatar.pack(side="left")
        names = customtkinter.CTkFrame(master=top, fg_color="transparent")
        names.pack(side="left", padx=16)
        customtkinter.CTkLabel(master=names, text=self.name_label.cget("text"), font=font(18, "bold"), text_color=TEXT_COLOR, anchor="w").pack(fill="x")
        customtkinter.CTkLabel(master=names, text="Picture from Gravatar, change it at gravatar.com", font=font(12),
                               text_color=MUTED_TEXT_COLOR, anchor="w").pack(fill="x")

        # Read only account details
        details_card, details = create_card(self.page, "Account")
        details_card.pack(fill="x")
        provider = self.user.get("oauth_provider")
        sign_in_method = "Password" + (f" and {get_provider_name(provider)}" if provider else "")
        if provider and not self.user.get("password_set"):
            sign_in_method = get_provider_name(provider)
        rows = (("Username", self.user.get("username", "")), ("Email", self.user.get("email") or "Not provided"),
                ("Sign-in method", sign_in_method), ("Member since", self.user.get("created_at") or "Unknown"),
                ("Last login", self.user.get("last_login") or "Unknown"))
        self.create_info_rows(details, rows)

        # Editable fields
        profile_card, profile = create_card(self.page, "Personal Information")
        profile_card.pack(fill="x", pady=(16, 0))
        field_width = 220
        self.name_entry = create_entry(profile, "First name", width=field_width)
        if self.user.get("first_name"):  # Inserting an empty value would hide the placeholder
            self.name_entry.insert(0, self.user["first_name"])
        self.name_entry.grid(row=0, column=0, padx=(0, 12))
        self.surname_entry = create_entry(profile, "Last name", width=field_width)
        if self.user.get("last_name"):  # Inserting an empty value would hide the placeholder
            self.surname_entry.insert(0, self.user["last_name"])
        self.surname_entry.grid(row=0, column=1, padx=(0, 12))
        self.country_var = customtkinter.StringVar(value=self.user.get("country") or "Select Country")
        self.country_box = create_combobox(profile, self.country_var, get_countries(), width=field_width)
        self.country_box.grid(row=0, column=2)

        self.profile_status = create_status_label(profile)
        self.profile_status.grid(row=1, column=0, columnspan=2, sticky="w", pady=(10, 0))
        self.save_button = create_button(profile, "Save", self.save_profile, width=140)
        self.save_button.grid(row=1, column=2, sticky="e", pady=(10, 0))

    def create_info_rows(self, master, rows):
        # Label and value pairs in three columns, returns the value labels so they can be updated
        values = {}
        for index, (label, value) in enumerate(rows):
            column = (index % 3) * 2
            customtkinter.CTkLabel(master=master, text=label, font=font(11), text_color=MUTED_TEXT_COLOR, anchor="w").grid(row=(index // 3) * 2, column=column, sticky="w", padx=(0, 40))
            values[label] = customtkinter.CTkLabel(master=master, text=value, font=font(13, "bold"), text_color=TEXT_COLOR, anchor="w")
            values[label].grid(row=(index // 3) * 2 + 1, column=column, sticky="w", padx=(0, 40), pady=(0, 10))
        return values

    def setup_device_page(self):
        self.create_page_header("Device")
        info = get_system_info()

        system_card, system = create_card(self.page, "This Computer")
        system_card.pack(fill="x")
        self.create_info_rows(system, [(name, info[name]) for name in ("Computer name", "Operating system", "Architecture",
                                                                        "CPU cores", "Memory", "Disk", "Uptime", "Python")])

        network_card, network = create_card(self.page, "Network and Session")
        network_card.pack(fill="x", pady=(16, 0))
        values = self.create_info_rows(network, [("Local IP", info["Local IP"]), ("Public IP", "Loading..."), ("MAC address", info["MAC address"]),
                                                 ("OS user", info["OS user"]), ("Logged in at", time.strftime("%H:%M:%S", time.localtime(self.login_time))),
                                                 ("Session time", "")])
        self.session_label = values["Session time"]
        self.public_ip_label = values["Public IP"]
        run_in_background(self.public_ip_label, get_public_ip,
                          lambda ip, error: self.public_ip_label.configure(text="Offline" if error else ip))
        self.update_session_time()

    def update_session_time(self):
        # Count up every second while the Device page is open
        if not self.session_label.winfo_exists():
            return
        self.session_label.configure(text=format_duration(time.time() - self.login_time))
        self.session_label.after(1000, self.update_session_time)

    def setup_todo_page(self):
        self.create_page_header("Todo")

        # New task with an optional alarm time
        tasks_card, tasks = create_card(self.page, "Tasks", "Pick a time to get an alarm, the webhook below is called when it is due.")
        tasks_card.pack(fill="x")
        add_row = customtkinter.CTkFrame(master=tasks, fg_color="transparent")
        add_row.pack(fill="x")
        self.todo_entry = create_entry(add_row, "What needs to be done?", width=420)
        self.todo_entry.pack(side="left")
        self.todo_entry.bind("<Return>", lambda event: self.handle_add_todo())
        self.due_at = ""  # Picked in the calendar, "" for no time
        self.due_button = create_button(add_row, "No time", self.open_calendar, style="secondary", width=150)
        self.due_button.pack(side="left", padx=10)
        create_button(add_row, "Add", self.handle_add_todo, width=100).pack(side="left")
        self.todo_status = create_status_label(tasks)
        self.todo_status.pack(fill="x")

        # List of tasks: Today, Upcoming and Archive
        self.todo_list = customtkinter.CTkScrollableFrame(master=tasks, height=170, fg_color="transparent")
        self.todo_list.pack(fill="x")

        # How long archived tasks are kept
        archive = customtkinter.CTkFrame(master=tasks, fg_color="transparent")
        archive.pack(fill="x", pady=(8, 0))
        customtkinter.CTkLabel(master=archive, text="Delete archived tasks after", font=font(13), text_color=TEXT_COLOR).pack(side="left")
        self.archive_days_var = customtkinter.StringVar(value=str(self.user.get("archive_days") or 7))
        archive_box = create_combobox(archive, self.archive_days_var, ["1", "3", "7", "14", "30"], width=80)
        archive_box.configure(command=self.save_archive_days)
        archive_box.pack(side="left", padx=10)
        customtkinter.CTkLabel(master=archive, text="days", font=font(13), text_color=TEXT_COLOR).pack(side="left")
        self.show_todos()

        # Webhook for the alarms (Discord, Slack or any URL that accepts a JSON POST)
        webhook_card, webhook = create_card(self.page, "Webhook Alarm")
        webhook_card.pack(fill="x", pady=(16, 0))
        self.webhook_entry = create_entry(webhook, "https://discord.com/api/webhooks/...", width=420)
        if self.user.get("webhook_url"):
            self.webhook_entry.insert(0, self.user["webhook_url"])
        self.webhook_entry.grid(row=0, column=0, padx=(0, 10))
        create_button(webhook, "Save", self.save_webhook, width=100).grid(row=0, column=1, padx=(0, 10))
        create_button(webhook, "Test", self.test_webhook, style="secondary", width=100).grid(row=0, column=2)
        self.webhook_status = create_status_label(webhook)
        self.webhook_status.grid(row=1, column=0, columnspan=3, sticky="w")

    def show_todos(self):
        # Rebuild the task list
        for widget in self.todo_list.winfo_children():
            widget.destroy()
        delete_old_todos(self.username, self.user.get("archive_days") or 7)
        for title, todos in group_todos(get_todos(self.username)).items():
            customtkinter.CTkLabel(master=self.todo_list, text=f"{title} ({len(todos)})", font=font(12, "bold"),
                                   text_color=MUTED_TEXT_COLOR, anchor="w").pack(fill="x", pady=(8, 2))
            if not todos:
                customtkinter.CTkLabel(master=self.todo_list, text="Nothing here.", font=font(12), text_color=MUTED_TEXT_COLOR, anchor="w").pack(fill="x")
            for todo in todos:
                self.show_todo_row(todo)

    def show_todo_row(self, todo):
        # One task with a checkbox, its time and a delete button
        row = customtkinter.CTkFrame(master=self.todo_list, fg_color="transparent")
        row.pack(fill="x", pady=2)
        done_var = customtkinter.BooleanVar(value=todo["done"])
        customtkinter.CTkCheckBox(master=row, text=todo["text"], variable=done_var, font=font(13), text_color=MUTED_TEXT_COLOR if todo["done"] else TEXT_COLOR,
                                  checkbox_width=18, checkbox_height=18, corner_radius=3, border_width=2, fg_color=ACCENT_COLOR,
                                  hover_color=ACCENT_HOVER_COLOR,
                                  command=lambda: self.toggle_todo(todo["id"], done_var.get())).pack(side="left")
        create_button(row, "Delete", lambda: self.remove_todo(todo["id"]), style="ghost", width=70, height=28).pack(side="right")
        if todo["due_at"]:
            customtkinter.CTkLabel(master=row, text=todo["due_at"][:16], font=font(12), text_color=MUTED_TEXT_COLOR).pack(side="right", padx=10)

    def open_calendar(self):
        # Calendar popup that sets the time of the new task
        CalendarPopup(self, self.set_due_time)

    def set_due_time(self, text):
        # Called by the calendar, shows the picked time on the button
        self.due_at = text
        self.due_button.configure(text=text or "No time")

    def save_archive_days(self, days):
        update_archive_days(self.username, days)
        self.user["archive_days"] = int(days)
        self.show_todos()

    def handle_add_todo(self):
        text = self.todo_entry.get().strip()
        if not text:
            show_status(self.todo_status, "Please enter a task.")
            return
        add_todo(self.username, text[:255], self.due_at + ":00" if self.due_at else "")
        self.todo_entry.delete(0, "end")
        self.set_due_time("")
        show_status(self.todo_status, "")
        self.show_todos()

    def toggle_todo(self, todo_id, done):
        set_todo_done(todo_id, done)
        self.show_todos()

    def remove_todo(self, todo_id):
        delete_todo(todo_id)
        self.show_todos()

    def save_webhook(self):
        url = self.webhook_entry.get().strip()
        if url and not url.startswith(("https://", "http://")):
            show_status(self.webhook_status, "The webhook must start with https://")
            return
        update_webhook_url(self.username, url)
        self.user["webhook_url"] = url
        show_status(self.webhook_status, "Webhook saved." if url else "Webhook removed.", "success")

    def test_webhook(self):
        url = self.webhook_entry.get().strip()
        if not url:
            show_status(self.webhook_status, "Enter a webhook URL first.")
            return
        show_status(self.webhook_status, "Sending...", "info")
        run_in_background(self.webhook_status, lambda: send_webhook(url, f"Test message from {config.app_name}"),
                          lambda sent, error: show_status(self.webhook_status, "Test message sent." if sent and not error else f"Could not send: {error}",
                                                          "success" if sent and not error else "error"))

    def check_todo_alarms(self):
        # Every 30 seconds: show and send tasks that are due (only while logged in)
        if not self.winfo_exists():
            return
        for todo in get_due_todos(self.username):
            mark_todo_notified(todo["id"])
            message = f"Reminder for {self.username}: {todo['text']}"
            url = self.user.get("webhook_url")
            if url:
                run_in_background(self, lambda u=url, m=message: send_webhook(u, m), lambda sent, error: error and print("Webhook error:", error))
            self.bell()
            messagebox.showinfo("Todo", todo["text"])
        self.after(TODO_CHECK_INTERVAL, self.check_todo_alarms)

    def setup_security_page(self):
        self.create_page_header("Security")
        self.user = get_user_data(self.username) or self.user  # Refresh in case the password was just set

        # Change (or set) password
        password_set = bool(self.user.get("password_set", 1))
        title = "Change Password" if password_set else "Set Password"
        password_card, password_body = create_card(self.page, title)
        password_card.pack(fill="x")
        self.change_password_form = ChangePasswordForm(password_body, self.username, self.finish_change_password, password_set=password_set, width=400)
        self.change_password_form.pack(anchor="w")

        # Delete account
        danger_card, danger_body = create_card(self.page, "Delete Account")
        danger_card.pack(fill="x", pady=(16, 0))
        self.delete_button = create_button(danger_body, "Delete Account", self.handle_delete_account, style="danger", width=160)
        self.delete_button.pack(anchor="w")

    def finish_change_password(self, message):
        # Rebuild the page so it shows the right form, then show the message
        self.show_page("security")
        show_status(self.change_password_form.status_label, message, "success")

    def save_profile(self):
        first_name = self.name_entry.get().strip()
        last_name = self.surname_entry.get().strip()
        country = self.country_box.get()

        if not first_name or not last_name:
            show_status(self.profile_status, "Please fill in all required fields.")
            return
        if not is_valid_chars_space(first_name) or not is_valid_chars_space(last_name):
            show_status(self.profile_status, "Names can only use English letters.")
            return
        if not validate_country(country):
            show_status(self.profile_status, "Please select a country.")
            return

        if update_user_profile(self.username, first_name, last_name, country):
            self.user.update(first_name=first_name, last_name=last_name, country=country)
            self.name_label.configure(text=f"{first_name} {last_name}")
            self.initials = (first_name[:1] + last_name[:1]).upper()
            if not self.gravatar:
                self.avatar.configure(text=self.initials)
            show_status(self.profile_status, "Profile updated.", "success")
        else:
            show_status(self.profile_status, "Could not update your profile.")

    def handle_delete_account(self):
        # Ask twice: a yes/no confirmation and the password (or username for social login accounts)
        if not messagebox.askyesno("Delete Account", "This will permanently delete your account. Continue?"):
            return
        if self.user.get("password_set", 1):
            dialog = PasswordDialog(text="Enter your password to confirm:", title="Delete Account")
        else:
            dialog = customtkinter.CTkInputDialog(text=f"Type your username ({self.username}) to confirm:", title="Delete Account")
        confirmation = dialog.get_input()
        if not confirmation:
            return
        if delete_user(self.username, confirmation):
            self.master.open_main_frame("Your account has been deleted.")
        else:
            messagebox.showerror("Error", "Confirmation did not match.")
