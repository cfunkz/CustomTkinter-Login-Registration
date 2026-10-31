import os
import re
import sys

# Settings are read in this order: real environment variables, then the .env file, then the defaults below.
# Only put the values you want to change in .env, see .env.example for every option.

# True when running as the .exe made by PyInstaller
IS_FROZEN = getattr(sys, "frozen", False)

# Folder of main.py, or the folder of the .exe when running as a release
APP_DIR = os.path.dirname(sys.executable) if IS_FROZEN else os.path.dirname(os.path.abspath(__file__))

# Folder with the bundled files (images), PyInstaller unpacks them to a temporary folder
BUNDLE_DIR = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))

def resource_path(relative_path):
    # Full path to a bundled file, works both from source and from the .exe
    return os.path.join(BUNDLE_DIR, relative_path)

def get_data_dir(folder_name):
    # One fixed folder per user for the database and settings
    # Windows: %APPDATA%\<folder>   macOS: ~/Library/Application Support/<folder>   Linux: ~/.local/share/<folder>
    if sys.platform == "win32":
        base = os.getenv("APPDATA") or os.path.expanduser("~")
    elif sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support")
    else:
        base = os.getenv("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    path = os.path.join(base, folder_name)
    os.makedirs(path, exist_ok=True)
    return path

def load_env_file(path):
    # Load KEY=VALUE pairs from a .env file without overwriting variables that are already set
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as env_file:
        for line in env_file:
            line = line.strip()
            # Skip empty lines, comments and lines without "="
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip().removeprefix("export ").strip()
            value = value.strip()
            # Remove matching quotes around the value, or an inline " # comment" after an unquoted value
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
                value = value[1:-1]
            else:
                value = re.split(r"\s+#", value, maxsplit=1)[0]
            os.environ.setdefault(key, value)

def get_env(name, default=None):
    # Read a text setting
    value = os.getenv(name)
    return value if value not in (None, "") else default

def get_env_int(name, default):
    # Read a whole number setting, fall back to the default if it is not a number
    try:
        return int(get_env(name, default))
    except (TypeError, ValueError):
        return default

def get_env_float(name, default):
    # Read a decimal number setting, fall back to the default if it is not a number
    try:
        return float(get_env(name, default))
    except (TypeError, ValueError):
        return default

def get_env_bool(name, default):
    # Read a true/false setting (true, yes, 1, on)
    value = get_env(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")

def get_env_list(name, default):
    # Read a comma separated list setting
    value = get_env(name)
    if value is None:
        return default
    return [item.strip().lower() for item in value.split(",") if item.strip()]

# .env next to main.py or the .exe is read first, then .env in the data folder
load_env_file(os.path.join(APP_DIR, ".env"))
data_dir = get_data_dir(os.getenv("DATA_FOLDER", "TitlePlacement"))
load_env_file(os.path.join(data_dir, ".env"))

# ---------------------------------------------------------------- Application
app_name = get_env("APP_NAME", "Title Placement")

# ---------------------------------------------------------------- Appearance
appearance_mode = get_env("APPEARANCE_MODE", "System")  # System, Light or Dark
color_theme = get_env("COLOR_THEME", "blue")  # blue, green, dark-blue or a path to a theme .json
accent_color = get_env("ACCENT_COLOR", "#3B82F6")
accent_hover_color = get_env("ACCENT_HOVER_COLOR", "#2563EB")
danger_color = get_env("DANGER_COLOR", "#EF4444")
danger_hover_color = get_env("DANGER_HOVER_COLOR", "#DC2626")
success_color = get_env("SUCCESS_COLOR", "#22C55E")
font_family = get_env("FONT_FAMILY", "Segoe UI")
ui_scaling = get_env_float("UI_SCALING", 1.0)

# ---------------------------------------------------------------- Windows
auth_window_size = get_env("AUTH_WINDOW_SIZE", "520x640")
dashboard_window_size = get_env("DASHBOARD_WINDOW_SIZE", "1100x680")
window_resizable = get_env_bool("WINDOW_RESIZABLE", False)

# ---------------------------------------------------------------- Database
database_type = (get_env("DATABASE_TYPE", "sqlite")).lower()  # sqlite, postgres or mysql
# SQLite file, saved in the data folder by default
database_file = get_env("DATABASE_FILE", os.path.join(data_dir, "user_database.db"))
# PostgreSQL / MySQL connection
database_host = get_env("DATABASE_HOST", "localhost")
database_port = get_env_int("DATABASE_PORT", 3306 if database_type == "mysql" else 5432)
database_name = get_env("DATABASE_NAME", "user_database")
database_user = get_env("DATABASE_USER", "")
database_password = get_env("DATABASE_PASSWORD", "")

# ---------------------------------------------------------------- Security
min_password_length = get_env_int("MIN_PASSWORD_LENGTH", 8)
max_login_attempts = get_env_int("MAX_LOGIN_ATTEMPTS", 5)
lockout_minutes = get_env_int("LOCKOUT_MINUTES", 5)
max_security_attempts = get_env_int("MAX_SECURITY_ATTEMPTS", 3)
hash_iterations = get_env_int("HASH_ITERATIONS", 310000)
temporary_password_length = get_env_int("TEMPORARY_PASSWORD_LENGTH", 12)

# ---------------------------------------------------------------- Email (SMTP)
# Gmail app password: https://myaccount.google.com/apppasswords
smtp_server = get_env("SMTP_SERVER", "smtp.gmail.com")
smtp_port = get_env_int("SMTP_PORT", 587)
smtp_username = get_env("SMTP_USERNAME", "")  # Your Gmail email address
smtp_password = get_env("SMTP_PASSWORD", "")  # Your Gmail app password
smtp_timeout = get_env_int("SMTP_TIMEOUT", 15)
sender_email = get_env("SENDER_EMAIL", smtp_username)

# ---------------------------------------------------------------- OAuth
# Providers shown on the login screen, in this order
oauth_providers = get_env_list("OAUTH_PROVIDERS", ["google", "facebook", "discord"])
# Redirect URI to register with every provider: http://localhost:8765/callback
oauth_redirect_host = get_env("OAUTH_REDIRECT_HOST", "localhost")
oauth_redirect_port = get_env_int("OAUTH_REDIRECT_PORT", 8765)
oauth_redirect_path = get_env("OAUTH_REDIRECT_PATH", "/callback")
oauth_timeout = get_env_int("OAUTH_TIMEOUT", 120)  # Seconds to wait for the browser sign-in
# Link a social login to an existing account with the same verified email
oauth_link_by_email = get_env_bool("OAUTH_LINK_BY_EMAIL", True)

google_client_id = get_env("GOOGLE_CLIENT_ID", "")
google_client_secret = get_env("GOOGLE_CLIENT_SECRET", "")

facebook_client_id = get_env("FACEBOOK_CLIENT_ID", "")
facebook_client_secret = get_env("FACEBOOK_CLIENT_SECRET", "")
facebook_api_version = get_env("FACEBOOK_API_VERSION", "v19.0")

discord_client_id = get_env("DISCORD_CLIENT_ID", "")
discord_client_secret = get_env("DISCORD_CLIENT_SECRET", "")
