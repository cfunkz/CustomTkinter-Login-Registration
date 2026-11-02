import threading
import tkinter
from functools import lru_cache
from tkinter import filedialog, messagebox
import customtkinter
from PIL import Image
import config
from functions import (is_valid_chars_space, is_valid_chars, is_valid_password_chars, is_strong_password, password_strength,
                       check_security_answer, get_security_question, is_valid_email, get_countries, validate_country,
                       toggle_password, register_user, check_login, get_lockout_remaining, reset_password,
                       email_exists, username_exists, change_password, get_user_data, update_user_profile, delete_user,
                       oauth_login_user, update_bio, export_user_data, days_since, time_ago, format_date, get_greeting,
                       get_initials, profile_completion, security_score)
from oauth import oauth_sign_in, get_display_providers, get_provider_name, is_provider_configured, OAuthError

# ---------------------------------------------------------------- Style
def mix_color(color, other, amount):
    # Blend two hex colors, amount 0 = color, 1 = other (used for the soft tints)
    first = [int(color[i:i + 2], 16) for i in (1, 3, 5)]
    second = [int(other[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(a + (b - a) * amount):02X}" for a, b in zip(first, second))

# Colors are (light mode, dark mode) pairs, customtkinter picks the right one
# Block style: paper / ink colors, near-square corners and solid offset shadows behind the panels
BACKGROUND_COLOR = ("#F2EEE6", "#0E0E10")
CARD_COLOR = ("#FFFFFF", "#18181B")
INPUT_COLOR = ("#F7F5F0", "#111113")
BORDER_COLOR = ("#1A1A1A", "#33333A")
TEXT_COLOR = ("#141414", "#F2F0EB")
MUTED_TEXT_COLOR = ("#6B6760", "#8E8C87")
HOVER_COLOR = ("#ECE7DD", "#232328")
SCROLLBAR_COLOR = ("#D6CFC2", "#2A2A30")  # Scrollbars, empty progress bars and dropdown buttons
ACCENT_COLOR = config.accent_color
ACCENT_HOVER_COLOR = config.accent_hover_color
ACCENT_SOFT_COLOR = (mix_color(ACCENT_COLOR, "#FFFFFF", 0.82), mix_color(ACCENT_COLOR, "#18181B", 0.75))
SHADOW_COLOR = ("#1A1A1A", mix_color(ACCENT_COLOR, "#0E0E10", 0.55))
DANGER_COLOR = config.danger_color
DANGER_HOVER_COLOR = config.danger_hover_color
SUCCESS_COLOR = config.success_color
WARNING_COLOR = "#F59E0B"

# Hero banner on the profile page
BANNER_COLOR = ACCENT_COLOR
BANNER_BORDER_COLOR = ("#1A1A1A", mix_color(ACCENT_COLOR, "#FFFFFF", 0.3))
BANNER_CHIP_COLOR = mix_color(ACCENT_COLOR, "#000000", 0.2)
BANNER_TEXT_COLOR = "#FFFFFF"
BANNER_MUTED_COLOR = mix_color(ACCENT_COLOR, "#FFFFFF", 0.75)

# Almost square corners
CARD_RADIUS = 6
WIDGET_RADIUS = 4
SHADOW_OFFSET = 5

FORM_WIDTH = 360
FIELD_HEIGHT = 42

# Logos for the social login buttons
PROVIDER_LOGOS = {
    "google": config.resource_path("images/g.png"),
    "facebook": config.resource_path("images/fb.png"),
    "discord": config.resource_path("images/discord.png"),
}

# Strength meter labels and colors (index = score from password_strength)
STRENGTH_TEXT = ["Very weak", "Weak", "Fair", "Good", "Strong"]
STRENGTH_COLORS = ["#EF4444", "#F97316", "#EAB308", "#22C55E", "#16A34A"]

SECURITY_QUESTIONS = ["What is your mother's maiden name?", "What is your favorite pet's name?", "Where were you born?",
                      "What is your favorite movie?", "What is your favorite book?"]

# ---------------------------------------------------------------- UI helper functions

@lru_cache(maxsize=None)
def font(size=13, weight="normal"):
    # Shared fonts, created once and reused
    return customtkinter.CTkFont(family=config.font_family, size=size, weight=weight)

@lru_cache(maxsize=None)
def mono(size=11, weight="bold"):
    # Monospace font for labels and numbers
    return customtkinter.CTkFont(family=config.mono_font_family, size=size, weight=weight)

@lru_cache(maxsize=None)
def load_image(path, size):
    # Load an image once and reuse it (the logos are large files)
    image = Image.open(path)
    image.thumbnail((size[0] * 2, size[1] * 2), Image.LANCZOS)  # 2x for sharp images on high DPI screens
    return customtkinter.CTkImage(light_image=image, size=size)

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
                                     fg_color=INPUT_COLOR, button_color=SCROLLBAR_COLOR, button_hover_color=ACCENT_COLOR,
                                     text_color=TEXT_COLOR, font=font(13), dropdown_font=font(12))

def create_button(master, text, command, style="primary", width=FORM_WIDTH, height=FIELD_HEIGHT, image=None):
    # Buttons in five styles: primary, secondary, danger, ghost and banner (on the profile banner)
    styles = {
        "primary": {"fg_color": ACCENT_COLOR, "hover_color": ACCENT_HOVER_COLOR, "text_color": "#FFFFFF", "border_width": 0},
        "secondary": {"fg_color": CARD_COLOR, "hover_color": HOVER_COLOR, "text_color": TEXT_COLOR, "border_width": 1},
        "danger": {"fg_color": DANGER_COLOR, "hover_color": DANGER_HOVER_COLOR, "text_color": "#FFFFFF", "border_width": 0},
        "ghost": {"fg_color": "transparent", "hover_color": HOVER_COLOR, "text_color": TEXT_COLOR, "border_width": 0},
        "banner": {"fg_color": BANNER_CHIP_COLOR, "hover_color": BANNER_BORDER_COLOR, "text_color": BANNER_TEXT_COLOR, "border_width": 1},
    }
    border_color = BANNER_BORDER_COLOR if style == "banner" else BORDER_COLOR
    return customtkinter.CTkButton(master=master, text=text, command=command, width=width, height=height, corner_radius=WIDGET_RADIUS,
                                   border_color=border_color, font=font(13, "bold"), image=image, **styles[style])

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
    meter.bar = customtkinter.CTkProgressBar(master=meter, width=width, height=6, corner_radius=0, progress_color=SCROLLBAR_COLOR,
                                             fg_color=SCROLLBAR_COLOR)
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
    menu = customtkinter.CTkOptionMenu(master=master, values=["System", "Light", "Dark"], width=110, height=32, corner_radius=WIDGET_RADIUS,
                                       font=font(12), dropdown_font=font(12), fg_color=CARD_COLOR, button_color=CARD_COLOR,
                                       button_hover_color=HOVER_COLOR, text_color=TEXT_COLOR,
                                       command=customtkinter.set_appearance_mode)
    menu.set(customtkinter.get_appearance_mode() if config.appearance_mode.lower() != "system" else "System")
    return menu

def create_panel(master, shadow=True, **kwargs):
    # Bordered panel with a solid shadow offset to the bottom right
    # Returns (outer, inner): place the outer frame, put content in the inner one
    outer = customtkinter.CTkFrame(master=master, fg_color="transparent")
    outer.grid_columnconfigure(0, weight=1)
    outer.grid_rowconfigure(0, weight=1)
    offset = SHADOW_OFFSET if shadow else 0
    if shadow:
        customtkinter.CTkFrame(master=outer, width=1, height=1, fg_color=SHADOW_COLOR, corner_radius=CARD_RADIUS).grid(row=0, column=0, sticky="nsew", padx=(offset, 0), pady=(offset, 0))
    options = {"fg_color": CARD_COLOR, "corner_radius": CARD_RADIUS, "border_width": 1, "border_color": BORDER_COLOR}
    options.update(kwargs)
    inner = customtkinter.CTkFrame(master=outer, **options)
    inner.grid(row=0, column=0, sticky="nsew", padx=(0, offset), pady=(0, offset))
    return outer, inner

def create_section_label(master, text, color=ACCENT_COLOR):
    # Small square marker and an uppercase monospace label, e.g. "■ ABOUT ME"
    return customtkinter.CTkLabel(master=master, text=f"■ {text.upper()}", font=mono(11), text_color=color, anchor="w")

def create_card(master, title, subtitle=""):
    # Panel with a heading, returns the outer frame (to place) and the frame to put content in
    card, inner = create_panel(master)
    create_section_label(inner, title).pack(fill="x", padx=24, pady=(18, 0))
    if subtitle:
        customtkinter.CTkLabel(master=inner, text=subtitle, font=font(13), text_color=TEXT_COLOR, anchor="w",
                               justify="left").pack(fill="x", padx=24, pady=(2, 0))
    body = customtkinter.CTkFrame(master=inner, fg_color="transparent")
    body.pack(fill="both", expand=True, padx=24, pady=(12, 20))
    return card, body

def create_chip(master, text, fg_color=ACCENT_SOFT_COLOR, text_color=TEXT_COLOR):
    # Small square "tag" label
    return customtkinter.CTkLabel(master=master, text=f" {text} ", height=24, corner_radius=2, fg_color=fg_color,
                                  text_color=text_color, font=mono(11))

def create_stat_tile(master, title, value, caption, color=ACCENT_COLOR):
    # Panel with a big number, used in the stats row
    tile, inner = create_panel(master)
    header = customtkinter.CTkFrame(master=inner, fg_color="transparent")
    header.pack(fill="x", padx=18, pady=(16, 0))
    customtkinter.CTkFrame(master=header, width=10, height=10, corner_radius=0, fg_color=color).pack(side="left", padx=(0, 8))
    customtkinter.CTkLabel(master=header, text=title.upper(), font=mono(10), text_color=MUTED_TEXT_COLOR, anchor="w").pack(side="left")
    customtkinter.CTkLabel(master=inner, text=value, font=mono(26), text_color=TEXT_COLOR, anchor="w").pack(fill="x", padx=18, pady=(6, 0))
    customtkinter.CTkLabel(master=inner, text=caption, font=font(11), text_color=MUTED_TEXT_COLOR, anchor="w").pack(fill="x", padx=18, pady=(0, 14))
    return tile

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

        # The form sits on a panel in the middle of the window
        self.card_panel, self.card = create_panel(self)
        self.card_panel.place(relx=0.5, rely=0.52, anchor=tkinter.CENTER)
        self.form = customtkinter.CTkFrame(master=self.card, fg_color="transparent")
        self.form.pack(padx=34, pady=(26, 28))

        # App name above every form
        create_section_label(self.form, config.app_name).pack(fill="x")

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
                                                       checkbox_width=18, checkbox_height=18, corner_radius=2, border_width=2,
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
        self.setup_loggedin_frame()

    def setup_loggedin_frame(self):
        self.master.change_geometry(config.dashboard_window_size)
        self.master.change_title(f"Dashboard - {config.app_name}")
        self.user = get_user_data(self.username) or {}

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.setup_sidebar()

        # Page area on the right
        self.page_area = customtkinter.CTkFrame(master=self, fg_color="transparent")
        self.page_area.grid(row=0, column=1, sticky="nsew", padx=(28, 16), pady=(20, 12))
        self.page = None
        self.current_page = None
        self.show_page("profile")

    def setup_sidebar(self):
        # Full height sidebar with a line on the right
        self.sidebar = customtkinter.CTkFrame(master=self, width=240, fg_color=CARD_COLOR, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="ns")
        customtkinter.CTkFrame(master=self, width=1, fg_color=BORDER_COLOR, corner_radius=0).grid(row=0, column=0, sticky="nse")
        self.sidebar.grid_propagate(False)
        self.sidebar.pack_propagate(False)

        # App name with a small accent mark
        brand = customtkinter.CTkFrame(master=self.sidebar, fg_color="transparent")
        brand.pack(fill="x", padx=22, pady=(24, 26))
        customtkinter.CTkLabel(master=brand, text="", width=14, height=14, corner_radius=0, fg_color=ACCENT_COLOR).pack(side="left", padx=(0, 10))
        customtkinter.CTkLabel(master=brand, text=config.app_name, font=font(16, "bold"), text_color=TEXT_COLOR, anchor="w").pack(side="left")

        # Avatar with the user's initials
        self.avatar = customtkinter.CTkLabel(master=self.sidebar, text=get_initials(self.user, self.username), width=60, height=60,
                                             corner_radius=WIDGET_RADIUS, fg_color=ACCENT_COLOR, text_color="#FFFFFF", font=mono(20))
        self.avatar.pack(padx=22, anchor="w")
        self.name_label = customtkinter.CTkLabel(master=self.sidebar, text=self.get_full_name(), font=font(15, "bold"),
                                                 text_color=TEXT_COLOR, anchor="w")
        self.name_label.pack(fill="x", padx=22, pady=(10, 0))
        customtkinter.CTkLabel(master=self.sidebar, text=f"@{self.username}", font=mono(11, "normal"), text_color=MUTED_TEXT_COLOR,
                               anchor="w").pack(fill="x", padx=22, pady=(0, 22))

        # Navigation
        customtkinter.CTkLabel(master=self.sidebar, text="MENU", font=mono(10), text_color=MUTED_TEXT_COLOR, anchor="w").pack(fill="x", padx=24, pady=(0, 4))
        for page, text in (("profile", "Profile"), ("security", "Security")):
            button = customtkinter.CTkButton(master=self.sidebar, text=text, height=40, corner_radius=WIDGET_RADIUS, anchor="w", font=font(13),
                                             fg_color="transparent", hover_color=HOVER_COLOR, text_color=TEXT_COLOR,
                                             command=lambda p=page: self.show_page(p))
            button.pack(fill="x", padx=14, pady=2)
            self.nav_buttons[page] = button

        # Bottom of the sidebar
        self.logout_button = create_button(self.sidebar, "Logout", self.master.open_main_frame, style="secondary", width=212)
        self.logout_button.pack(side="bottom", padx=14, pady=(8, 20))
        self.appearance_menu = create_appearance_menu(self.sidebar)
        self.appearance_menu.configure(width=212)
        self.appearance_menu.pack(side="bottom", padx=14)
        customtkinter.CTkLabel(master=self.sidebar, text="APPEARANCE", font=mono(10), text_color=MUTED_TEXT_COLOR, anchor="w").pack(side="bottom", fill="x", padx=24, pady=(0, 4))

    def get_full_name(self):
        # "First Last", or the username if there is no name
        name = f"{self.user.get('first_name') or ''} {self.user.get('last_name') or ''}".strip()
        return name or self.username

    def show_page(self, page, keep_scroll=False):
        # Switch between the dashboard pages (keep_scroll keeps the scroll position when the same page is rebuilt)
        scroll_position = self.page._parent_canvas.yview()[0] if keep_scroll and self.page is not None else 0
        if self.page is not None:
            self.page.destroy()
        self.current_page = page
        for name, button in self.nav_buttons.items():
            active = name == page
            button.configure(fg_color=ACCENT_SOFT_COLOR if active else "transparent", font=font(13, "bold" if active else "normal"))

        # Pages scroll when they are taller than the window
        self.page = customtkinter.CTkScrollableFrame(master=self.page_area, fg_color="transparent", corner_radius=0,
                                                     scrollbar_button_color=SCROLLBAR_COLOR, scrollbar_button_hover_color=MUTED_TEXT_COLOR)
        self.page.pack(fill="both", expand=True)
        if page == "profile":
            self.setup_profile_page()
        else:
            self.setup_security_page()
        if scroll_position:
            self.after(10, lambda: self.page._parent_canvas.yview_moveto(scroll_position))

    def create_page_header(self, title, subtitle=""):
        create_section_label(self.page, f"{self.current_page_number()} / {title}", MUTED_TEXT_COLOR).pack(fill="x")
        customtkinter.CTkLabel(master=self.page, text=title, font=font(24, "bold"), text_color=TEXT_COLOR, anchor="w").pack(fill="x", padx=(0, 12))
        if subtitle:
            customtkinter.CTkLabel(master=self.page, text=subtitle, font=font(13), text_color=MUTED_TEXT_COLOR, anchor="w").pack(fill="x")
        customtkinter.CTkFrame(master=self.page, height=14, fg_color="transparent").pack()  # Space under the header

    def current_page_number(self):
        # "01", "02"... shown above the page title
        return f"{list(self.nav_buttons).index(self.current_page) + 1:02d}"

    def setup_profile_page(self):
        self.user = get_user_data(self.username) or self.user
        self.create_page_header("Profile", f"{get_greeting()}, {self.user.get('first_name') or self.username}. Here is your account at a glance.")
        self.setup_profile_banner()
        self.setup_stats_row()

        # About me and profile strength next to each other
        row = customtkinter.CTkFrame(master=self.page, fg_color="transparent")
        row.pack(fill="x", pady=(16, 0), padx=(0, 12))
        row.grid_columnconfigure((0, 1), weight=1, uniform="half")
        self.setup_about_card(row).grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self.setup_completion_card(row).grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        self.setup_account_card()
        self.setup_personal_card()

    def setup_profile_banner(self):
        # Colored hero card with the avatar, name and a few "chips"
        banner_panel, banner = create_panel(self.page, fg_color=BANNER_COLOR, border_color=BANNER_BORDER_COLOR)
        banner_panel.pack(fill="x", padx=(0, 12))
        banner.grid_columnconfigure(1, weight=1)

        customtkinter.CTkLabel(master=banner, text=get_initials(self.user, self.username), width=84, height=84, corner_radius=WIDGET_RADIUS,
                               fg_color=BANNER_CHIP_COLOR, text_color=BANNER_TEXT_COLOR,
                               font=mono(30)).grid(row=0, column=0, rowspan=3, padx=(26, 18), pady=24)
        customtkinter.CTkLabel(master=banner, text=self.get_full_name(), font=font(24, "bold"), text_color=BANNER_TEXT_COLOR,
                               anchor="w").grid(row=0, column=1, sticky="sw", pady=(24, 0))
        bio = (self.user.get("bio") or "").strip() or "No bio yet. Tell people a little about yourself below."
        customtkinter.CTkLabel(master=banner, text=bio, font=font(13), text_color=BANNER_MUTED_COLOR, anchor="w", justify="left",
                               wraplength=480).grid(row=1, column=1, sticky="w")

        # Chips: username, country, sign-in method and member since
        chips = customtkinter.CTkFrame(master=banner, fg_color="transparent")
        chips.grid(row=2, column=1, sticky="nw", pady=(8, 24))
        provider = self.user.get("oauth_provider")
        chip_texts = [f"@{self.username}", self.user.get("country") or "", get_provider_name(provider) if provider else "",
                      f"JOINED {format_date(self.user.get('created_at')).upper()}"]
        for text in chip_texts:
            if text:
                create_chip(chips, text, fg_color=BANNER_CHIP_COLOR, text_color=BANNER_TEXT_COLOR).pack(side="left", padx=(0, 6))

        self.export_button = create_button(banner, "Export data", self.handle_export_data, style="banner", width=120, height=36)
        self.export_button.grid(row=0, column=2, sticky="ne", padx=24, pady=24)

    def setup_stats_row(self):
        # Four small tiles with numbers about the account
        stats = customtkinter.CTkFrame(master=self.page, fg_color="transparent")
        stats.pack(fill="x", pady=(16, 0), padx=(0, 12))
        days = days_since(self.user.get("created_at"))
        completion, _ = profile_completion(self.user)
        score, score_label = security_score(self.user)
        score_color = {"Strong": SUCCESS_COLOR, "Good": WARNING_COLOR, "Weak": DANGER_COLOR}[score_label]
        logins = self.user.get("login_count") or 0
        tiles = (("Member for", f"{days} day{'' if days == 1 else 's'}", f"Since {format_date(self.user.get('created_at'))}", ACCENT_COLOR),
                 ("Logins", str(logins), f"Last seen {time_ago(self.user.get('last_login')).lower()}", "#06B6D4"),
                 ("Profile", f"{completion}%", "Complete" if completion == 100 else "Almost there", "#A855F7"),
                 ("Security", score_label, f"Score {score} / 100", score_color))
        for index, (title, value, caption, color) in enumerate(tiles):
            stats.grid_columnconfigure(index, weight=1, uniform="tile")
            create_stat_tile(stats, title, value, caption, color).grid(row=0, column=index, sticky="nsew", padx=(0 if index == 0 else 10, 0))

    def setup_about_card(self, master):
        # Short bio with a live character counter
        card, body = create_card(master, "About me", f"Shown on your profile, up to {config.bio_max_length} characters.")
        self.bio_box = customtkinter.CTkTextbox(master=body, height=92, corner_radius=WIDGET_RADIUS, border_width=1, border_color=BORDER_COLOR,
                                                fg_color=INPUT_COLOR, text_color=TEXT_COLOR, font=font(13), wrap="word")
        self.bio_box.insert("1.0", self.user.get("bio") or "")
        self.bio_box.pack(fill="x")
        self.bio_box.bind("<KeyRelease>", lambda event: self.update_bio_counter())

        footer = customtkinter.CTkFrame(master=body, fg_color="transparent")
        footer.pack(fill="x", pady=(10, 0))
        self.bio_counter = customtkinter.CTkLabel(master=footer, text="", font=mono(11, "normal"), text_color=MUTED_TEXT_COLOR)
        self.bio_counter.pack(side="left")
        create_button(footer, "Save bio", self.save_bio, width=110, height=36).pack(side="right")
        self.bio_status = create_status_label(body)
        self.bio_status.pack(fill="x")
        self.update_bio_counter()
        return card

    def setup_completion_card(self, master):
        # Progress bar and checklist of what is still missing
        completion, items = profile_completion(self.user)
        card, body = create_card(master, "Profile strength", f"{completion}% complete")
        bar = customtkinter.CTkProgressBar(master=body, height=10, corner_radius=0, fg_color=SCROLLBAR_COLOR,
                                           progress_color=SUCCESS_COLOR if completion == 100 else ACCENT_COLOR)
        bar.set(completion / 100)
        bar.pack(fill="x", pady=(0, 10))
        checklist = customtkinter.CTkFrame(master=body, fg_color="transparent")
        checklist.pack(fill="x")
        checklist.grid_columnconfigure((0, 1), weight=1, uniform="check")
        for index, (label, done) in enumerate(items):
            customtkinter.CTkLabel(master=checklist, text=f"{'■' if done else '□'}  {label}", font=font(12, "bold" if done else "normal"),
                                   text_color=SUCCESS_COLOR if done else MUTED_TEXT_COLOR,
                                   anchor="w").grid(row=index // 2, column=index % 2, sticky="w", pady=2)
        return card

    def setup_account_card(self):
        # Read only account details
        details_card, details = create_card(self.page, "Account")
        details_card.pack(fill="x", pady=(16, 0), padx=(0, 12))
        provider = self.user.get("oauth_provider")
        sign_in_method = "Password" + (f" and {get_provider_name(provider)}" if provider else "")
        if provider and not self.user.get("password_set"):
            sign_in_method = get_provider_name(provider)
        rows = (("Username", self.user.get("username", "")), ("Email", self.user.get("email") or "Not provided"),
                ("Sign-in method", sign_in_method), ("Member since", format_date(self.user.get("created_at"))),
                ("Last login", time_ago(self.user.get("last_login"))), ("Security question", "Set" if self.user.get("security_question") else "Not set"))
        details.grid_columnconfigure((0, 1, 2), weight=1, uniform="detail")
        for index, (label, value) in enumerate(rows):
            column = index % 3
            customtkinter.CTkLabel(master=details, text=label.upper(), font=mono(10), text_color=MUTED_TEXT_COLOR, anchor="w").grid(row=(index // 3) * 2, column=column, sticky="w")
            customtkinter.CTkLabel(master=details, text=value, font=font(13, "bold"), text_color=TEXT_COLOR, anchor="w").grid(row=(index // 3) * 2 + 1, column=column, sticky="w", pady=(0, 10))

    def setup_personal_card(self):
        # Editable fields
        profile_card, profile = create_card(self.page, "Personal Information")
        profile_card.pack(fill="x", pady=(16, 4), padx=(0, 12))
        profile.grid_columnconfigure((0, 1, 2), weight=1, uniform="field")
        self.name_entry = create_entry(profile, "First name", width=200)
        if self.user.get("first_name"):  # Inserting an empty value would hide the placeholder
            self.name_entry.insert(0, self.user["first_name"])
        self.name_entry.grid(row=0, column=0, sticky="ew", padx=(0, 12))
        self.surname_entry = create_entry(profile, "Last name", width=200)
        if self.user.get("last_name"):  # Inserting an empty value would hide the placeholder
            self.surname_entry.insert(0, self.user["last_name"])
        self.surname_entry.grid(row=0, column=1, sticky="ew", padx=(0, 12))
        self.country_var = customtkinter.StringVar(value=self.user.get("country") or "Select Country")
        self.country_box = create_combobox(profile, self.country_var, get_countries(), width=200)
        self.country_box.grid(row=0, column=2, sticky="ew")

        self.profile_status = create_status_label(profile)
        self.profile_status.grid(row=1, column=0, columnspan=2, sticky="w", pady=(10, 0))
        self.save_button = create_button(profile, "Save", self.save_profile, width=140)
        self.save_button.grid(row=1, column=2, sticky="e", pady=(10, 0))

    def setup_security_page(self):
        self.user = get_user_data(self.username) or self.user  # Refresh in case the password was just set
        score, score_label = security_score(self.user)
        self.create_page_header("Security", f"Your account security is {score_label.lower()} ({score} / 100).")

        # Change (or set) password
        password_set = bool(self.user.get("password_set", 1))
        title = "Change Password" if password_set else "Set Password"
        password_card, password_body = create_card(self.page, title)
        password_card.pack(fill="x", padx=(0, 12))
        self.change_password_form = ChangePasswordForm(password_body, self.username, self.finish_change_password, password_set=password_set, width=400)
        self.change_password_form.pack(anchor="w")

        # Delete account
        danger_card, danger_body = create_card(self.page, "Delete Account", "Permanently remove your account and all of its data.")
        danger_card.pack(fill="x", pady=(16, 4), padx=(0, 12))
        self.delete_button = create_button(danger_body, "Delete Account", self.handle_delete_account, style="danger", width=160)
        self.delete_button.pack(anchor="w")

    def finish_change_password(self, message):
        # Rebuild the page so it shows the right form, then show the message
        self.show_page("security")
        show_status(self.change_password_form.status_label, message, "success")

    def refresh_sidebar(self):
        # Update the name and avatar after the profile was changed
        self.name_label.configure(text=self.get_full_name())
        self.avatar.configure(text=get_initials(self.user, self.username))

    def update_bio_counter(self):
        # Show how many characters are left, red when the bio is too long
        length = len(self.bio_box.get("1.0", "end-1c").strip())
        self.bio_counter.configure(text=f"{length} / {config.bio_max_length}",
                                   text_color=DANGER_COLOR if length > config.bio_max_length else MUTED_TEXT_COLOR)

    def save_bio(self):
        bio = " ".join(self.bio_box.get("1.0", "end-1c").split())  # One line, no extra spaces
        if len(bio) > config.bio_max_length:
            show_status(self.bio_status, f"Keep it under {config.bio_max_length} characters.")
            return
        if update_bio(self.username, bio):
            self.show_page("profile", keep_scroll=True)
            show_status(self.bio_status, "Bio saved.", "success")
        else:
            show_status(self.bio_status, "Could not save your bio.")

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
            self.refresh_sidebar()
            self.show_page("profile", keep_scroll=True)  # Banner, stats and checklist show the new values
            show_status(self.profile_status, "Profile updated.", "success")
        else:
            show_status(self.profile_status, "Could not update your profile.")

    def handle_export_data(self):
        # Save the profile as a JSON file, a small "download my data" feature
        path = filedialog.asksaveasfilename(title="Export profile", defaultextension=".json", initialfile=f"{self.username}-profile.json",
                                            filetypes=[("JSON file", "*.json")])
        if not path:
            return
        try:
            saved = export_user_data(self.username, path)
        except OSError as e:
            print("Export error:", e)
            saved = False
        if saved:
            messagebox.showinfo("Export data", f"Your profile was saved to:\n{path}")
        else:
            messagebox.showerror("Export data", "Could not export your profile.")

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
