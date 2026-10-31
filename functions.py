import smtplib
import hashlib
import hmac
import secrets
import string
import time
import re
from functools import lru_cache
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import config
import pycountry
from database import database, init_database, now, DatabaseError, IntegrityError

# Password hashing settings (PBKDF2 with SHA-256)
HASH_ITERATIONS = config.hash_iterations
SALT_BYTES = 16

# Login lockout settings
MAX_LOGIN_ATTEMPTS = config.max_login_attempts
LOCKOUT_SECONDS = config.lockout_minutes * 60

# Pre-compiled regular expressions (compiled once instead of on every call)
EMAIL_PATTERN = re.compile(r'^[\w\.+-]+@[\w-]+(\.[\w-]+)*\.[a-zA-Z]{2,}$')
CHARS_PATTERN = re.compile(r'^[a-zA-Z0-9_\-]+$')
CHARS_SPACE_PATTERN = re.compile(r'^[a-zA-Z0-9_\- ]+$')
PASSWORD_CHARS_PATTERN = re.compile(r'^[!-~]+$')  # Any printable ASCII character without spaces


def test_buttons():
    print("Button is working bro!")

def toggle_password(p_block, show_password_var):
    if show_password_var.get():
        p_block.configure(show="")
    else:
        p_block.configure(show="*")

def hash_password(password):
    # Hash a password with a random salt, stored as "iterations$salt$hash"
    salt = secrets.token_bytes(SALT_BYTES)
    password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, HASH_ITERATIONS)
    return f"{HASH_ITERATIONS}${salt.hex()}${password_hash.hex()}"

def verify_password(password, stored_password):
    # Check a password against a stored hash (constant-time compare)
    if not stored_password:
        return False
    try:
        iterations, salt, stored_hash = stored_password.split('$')
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), int(iterations))
        return hmac.compare_digest(password_hash.hex(), stored_hash)
    except ValueError:
        # Legacy plain-text password from an older database
        return hmac.compare_digest(password, stored_password)

def is_hashed(stored_password):
    # Check if a stored password is already hashed
    return stored_password is not None and stored_password.count('$') == 2

def normalize_answer(answer):
    # Make security answers case and space insensitive
    return " ".join(answer.lower().split())

def send_password_reset_email(email, temporary_password):
    # Email configuration
    smtp_server = config.smtp_server
    smtp_port = config.smtp_port
    smtp_username = config.smtp_username
    smtp_password = config.smtp_password

    # Email content
    sender_email = config.sender_email
    recipient_email = email
    subject = "Password Reset"
    message = (f"Your temporary password is: {temporary_password}\n\n"
               "You will be asked to choose a new password after you log in.\n"
               "If you did not request this, please contact support.")

    # Create a message
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject

    # Attach the message to the email
    msg.attach(MIMEText(message, 'plain'))

    # Email can't be sent without SMTP details
    if not smtp_username or not smtp_password:
        print("Email error: SMTP_USERNAME and SMTP_PASSWORD are not set.")
        return False

    try:
        # Connect to the SMTP server (closes automatically), with a timeout so the app can't hang
        with smtplib.SMTP(smtp_server, smtp_port, timeout=config.smtp_timeout) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
        return True  # Email sent

    except (smtplib.SMTPException, OSError) as e:
        print("Email error:", e)
        return False  # Email failed

def generate_temporary_password(length=None):
    # Generate a cryptographically secure temporary password with at least one letter and one digit
    length = max(length or config.temporary_password_length, config.min_password_length)
    characters = string.ascii_letters + string.digits
    while True:
        temporary_password = ''.join(secrets.choice(characters) for letters in range(length))
        if is_strong_password(temporary_password):
            return temporary_password

def check_login(username, password):
    # Returns a tuple (status, username) where status is "ok", "change_password", "locked" or "invalid"
    # Users can log in with their username or their email
    try:
        with database() as cursor:
            cursor.execute('''
                SELECT username, password, failed_attempts, locked_until, must_change_password
                FROM Users WHERE LOWER(username) = LOWER(?) OR LOWER(email) = LOWER(?)
            ''', (username, username))
            result = cursor.fetchone()

            if not result:
                # Run a dummy hash so a missing user takes as long as a wrong password
                verify_password(password, hash_password("dummy"))
                return "invalid", None

            db_username, stored_password, failed_attempts, locked_until, must_change = result

            # Refuse login while the account is locked
            if locked_until and locked_until > time.time():
                return "locked", db_username

            if not verify_password(password, stored_password):
                # Count the failed attempt and lock the account after too many
                failed_attempts = (failed_attempts or 0) + 1
                if failed_attempts >= MAX_LOGIN_ATTEMPTS:
                    cursor.execute("UPDATE Users SET failed_attempts = 0, locked_until = ? WHERE username = ?",
                                   (time.time() + LOCKOUT_SECONDS, db_username))
                    return "locked", db_username
                cursor.execute("UPDATE Users SET failed_attempts = ? WHERE username = ?", (failed_attempts, db_username))
                return "invalid", None

            # Successful login: reset the counter and save the login time
            cursor.execute("UPDATE Users SET failed_attempts = 0, locked_until = 0, last_login = ? WHERE username = ?",
                           (now(), db_username))

            # Upgrade a legacy plain-text password to a hash
            if not is_hashed(stored_password):
                cursor.execute("UPDATE Users SET password = ? WHERE username = ?", (hash_password(password), db_username))

            if must_change:
                return "change_password", db_username
            return "ok", db_username

    except DatabaseError as e:
        # Handle any potential database errors here
        print("Database error:", e)
        return "invalid", None

def get_lockout_remaining(username):
    # Return how many seconds are left on an account lockout (0 if not locked)
    with database() as cursor:
        cursor.execute("SELECT locked_until FROM Users WHERE LOWER(username) = LOWER(?)", (username,))
        result = cursor.fetchone()
    if result and result[0]:
        return max(0, int(result[0] - time.time()))
    return 0

def register_user(first_name, last_name, country, username, email, password, security_question, security_answer):
    try:
        with database() as cursor:
            # Insert user data into the Users table (password and answer are hashed, never stored as plain text)
            cursor.execute('''
                INSERT INTO Users (first_name, last_name, country, username, email, password, security_question, security_answer, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (first_name.strip(), last_name.strip(), country, username, email.strip().lower(), hash_password(password),
                  security_question, hash_password(normalize_answer(security_answer)), now()))

        return True  # Registration successful

    except IntegrityError:
        return False  # Username or email is already in use

def email_exists(email):
    # Return True if the email is registered
    with database() as cursor:
        cursor.execute("SELECT 1 FROM Users WHERE LOWER(email) = LOWER(?)", (email.strip(),))
        return cursor.fetchone() is not None

def username_exists(username):
    # Return True if the username is taken
    with database() as cursor:
        cursor.execute("SELECT 1 FROM Users WHERE LOWER(username) = LOWER(?)", (username.strip(),))
        return cursor.fetchone() is not None

@lru_cache(maxsize=1)
def get_countries():
    # Load and sort the country list only once
    return sorted(country.name for country in pycountry.countries)

@lru_cache(maxsize=1)
def get_countries_set():
    # Set of countries for fast lookups
    return frozenset(get_countries())

def validate_country(country_name):
    # Check if the entered country is in the list of available countries
    return country_name in get_countries_set()

def update_password(email, new_password, must_change=False):
    try:
        with database() as cursor:
            # Save the hashed password and clear any lockout
            cursor.execute('''
                UPDATE Users SET password = ?, must_change_password = ?, failed_attempts = 0, locked_until = 0
                WHERE LOWER(email) = LOWER(?)
            ''', (hash_password(new_password), int(must_change), email.strip()))
            return cursor.rowcount > 0  # Password updated successfully

    except DatabaseError as e:
        print("Error updating password:", str(e))
        return False  # Password update failed

def reset_password(email):
    # Create a temporary password, email it and save it only if the email was sent
    temporary_password = generate_temporary_password()
    if not send_password_reset_email(email, temporary_password):
        return False
    return update_password(email, temporary_password, must_change=True)

def change_password(username, old_password, new_password):
    # Change a password after checking the old one, returns (success, message)
    with database() as cursor:
        cursor.execute("SELECT password, password_set FROM Users WHERE LOWER(username) = LOWER(?)", (username,))
        result = cursor.fetchone()

        # Social login accounts without a password can set one without an old password
        if result and result[1] == 0:
            cursor.execute("UPDATE Users SET password = ?, password_set = 1, must_change_password = 0 WHERE LOWER(username) = LOWER(?)",
                           (hash_password(new_password), username))
            return True, "Password set. You can now also log in with your username and password."

        if not result or not verify_password(old_password, result[0]):
            return False, "Current password is incorrect."
        if verify_password(new_password, result[0]):
            return False, "New password must be different from the current one."

        cursor.execute("UPDATE Users SET password = ?, must_change_password = 0 WHERE LOWER(username) = LOWER(?)",
                       (hash_password(new_password), username))
    return True, "Password changed successfully."

def get_user_data(username):
    # Return a dictionary of the user's profile (no password or answer)
    with database() as cursor:
        cursor.execute('''
            SELECT first_name, last_name, country, username, email, security_question, created_at, last_login,
                   oauth_provider, password_set
            FROM Users WHERE LOWER(username) = LOWER(?)
        ''', (username,))
        result = cursor.fetchone()
        if not result:
            return None
        columns = [column[0] for column in cursor.description]
        return dict(zip(columns, result))

def update_user_profile(username, first_name, last_name, country):
    # Update the user's name and country
    with database() as cursor:
        cursor.execute("UPDATE Users SET first_name = ?, last_name = ?, country = ? WHERE LOWER(username) = LOWER(?)",
                       (first_name.strip(), last_name.strip(), country, username))
        return cursor.rowcount > 0

def delete_user(username, confirmation):
    # Delete an account after confirming the password (or the username for social login accounts without a password)
    with database() as cursor:
        cursor.execute("SELECT password, password_set FROM Users WHERE LOWER(username) = LOWER(?)", (username,))
        result = cursor.fetchone()
        if not result:
            return False
        if result[1] == 0:
            if confirmation.strip().lower() != username.lower():
                return False
        elif not verify_password(confirmation, result[0]):
            return False
        cursor.execute("DELETE FROM Users WHERE LOWER(username) = LOWER(?)", (username,))
        return True

def make_unique_username(base):
    # Turn a name or email into a valid username and add a number if it is already taken
    base = re.sub(r'[^a-zA-Z0-9_\-]', '', base.replace(" ", "_"))[:16] or "user"
    if len(base) < 3:
        base = f"{base}_user"
    username = base
    number = 1
    while username_exists(username):
        number += 1
        username = f"{base}{number}"
    return username

def oauth_login_user(profile):
    # Log in or register a user from a social login profile, returns (status, username)
    # status is "ok", "linked" (added to an existing account), "created" (new account) or "email_in_use"
    provider = profile["provider"]
    oauth_id = str(profile["id"])
    email = (profile.get("email") or "").strip().lower() or None

    with database() as cursor:
        # 1. Signed in with this provider before
        cursor.execute("SELECT username FROM Users WHERE oauth_provider = ? AND oauth_id = ?", (provider, oauth_id))
        result = cursor.fetchone()
        if result:
            cursor.execute("UPDATE Users SET last_login = ?, failed_attempts = 0, locked_until = 0 WHERE username = ?", (now(), result[0]))
            return "ok", result[0]

        # 2. An account with the same verified email exists, link the provider to it
        cursor.execute("SELECT username, oauth_provider FROM Users WHERE LOWER(email) = LOWER(?)", (email,))
        result = cursor.fetchone() if email else None
        if result:
            if result[1] is None and profile.get("email_verified") and config.oauth_link_by_email:
                cursor.execute('''
                    UPDATE Users SET oauth_provider = ?, oauth_id = ?, last_login = ?, failed_attempts = 0, locked_until = 0
                    WHERE username = ?
                ''', (provider, oauth_id, now(), result[0]))
                return "linked", result[0]
            # Never create a second account for an email that is already registered
            return "email_in_use", None

    # 3. Create a new account with an unusable random password
    username = make_unique_username(profile.get("username") or (email or "").split("@")[0] or provider)
    with database() as cursor:
        cursor.execute('''
            INSERT INTO Users (first_name, last_name, country, username, email, password, created_at, last_login,
                               oauth_provider, oauth_id, password_set)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
        ''', ((profile.get("first_name") or username).strip(), (profile.get("last_name") or "").strip(), "", username, email,
              hash_password(secrets.token_urlsafe(32)), now(), now(), provider, oauth_id))
    return "created", username

def get_security_question(email):
    try:
        with database() as cursor:
            cursor.execute("SELECT security_question FROM Users WHERE LOWER(email) = LOWER(?)", (email.strip(),))
            result = cursor.fetchone()

        if result:
            return result[0]  # Return the security question
        else:
            return None  # User not found or no security question associated with the email

    except DatabaseError as e:
        print("Database error:", str(e))
        return None

def check_security_answer(email, provided_answer):
    try:
        with database() as cursor:
            cursor.execute("SELECT security_answer FROM Users WHERE LOWER(email) = LOWER(?)", (email.strip(),))
            result = cursor.fetchone()

            if not result:
                return False  # User not found or no security answer associated with the email

            stored_answer = result[0]
            answer = normalize_answer(provided_answer)

            if is_hashed(stored_answer):
                return verify_password(answer, stored_answer)

            # Legacy plain-text answer: compare, then upgrade it to a hash
            if hmac.compare_digest(answer, normalize_answer(stored_answer)):
                cursor.execute("UPDATE Users SET security_answer = ? WHERE LOWER(email) = LOWER(?)", (hash_password(answer), email.strip()))
                return True
            return False

    except DatabaseError as e:
        print("Database error:", str(e))
        return False

def is_valid_email(email):
    # Check if the email matches a standard email format
    return EMAIL_PATTERN.match(email.strip()) is not None

def is_valid_chars(input_string):
    # Allow only English letters, digits, "_" and "-"
    return CHARS_PATTERN.match(input_string) is not None

def is_valid_chars_space(input_string):
    # Allow only English letters, digits, "_", "-" and spaces
    return CHARS_SPACE_PATTERN.match(input_string) is not None

def is_valid_password_chars(input_string):
    # Allow letters, digits and symbols, but no spaces
    return PASSWORD_CHARS_PATTERN.match(input_string) is not None

def is_strong_password(password, min_length=None):
    # A strong password has a minimum length, at least one letter and at least one digit
    min_length = min_length or config.min_password_length
    return (len(password) >= min_length
            and any(char.isalpha() for char in password)
            and any(char.isdigit() for char in password))

def password_strength(password):
    # Score a password from 0 to 4 for the strength meter
    score = 0
    if len(password) >= config.min_password_length:
        score += 1
    if len(password) >= 12:
        score += 1
    if any(char.islower() for char in password) and any(char.isupper() for char in password):
        score += 1
    if any(char.isdigit() for char in password) and any(not char.isalnum() for char in password):
        score += 1
    return score
