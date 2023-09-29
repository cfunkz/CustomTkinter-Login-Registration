import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import string
import config
import pycountry
import re

def get_database_connection():
    # Open a database connection and return the connection and cursor
    db = sqlite3.connect('user_database.db')
    cursor = db.cursor()
    return db, cursor

def close_database_connection(db):
    # Close the database connection
    if db:
        db.close()

def test_buttons():
    print("Button is working bro!")

def toggle_password(p_block, show_password_var):
    if show_password_var.get():
        p_block.configure(show="")
    else:
        p_block.configure(show="*")

def send_password_reset_email(email, temporary_password):
    # Email configuration
    smtp_server = config.smtp_server
    smtp_port = config.smtp_port
    smtp_username = config.smtp_username  # Replace with your Gmail email address
    smtp_password = config.smtp_password  # Replace with your Gmail password

    # Email content
    sender_email = config.sender_email
    recipient_email = email
    subject = "Password Reset"
    message = f"Your temporary password is: {temporary_password}"

    # Create a message
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject

    # Attach the message to the email
    msg.attach(MIMEText(message, 'plain'))

    # Connect to the SMTP server
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(smtp_username, smtp_password)

    # Send the email
    server.sendmail(sender_email, recipient_email, msg.as_string())

    # Disconnect from the server
    server.quit()

def generate_temporary_password(length=8):
    # Generate a random temporary password
    characters = string.ascii_letters + string.digits
    temporary_password = ''.join(random.choice(characters) for letters in range(length))
    return temporary_password

def check_login(username, password):
    db, cursor = get_database_connection()
    try:

        # Check if the provided username and password match a record in the Users table
        cursor.execute("SELECT username, password FROM Users WHERE username = ? AND password = ?", (username, password))
        result = cursor.fetchone()

        # If a matching record is found, return True for a successful login
        if result:
            return True

    except sqlite3.Error as e:
        # Handle any potential database errors here
        print("SQLite error:", e)

    finally:
        # Close the database connection
        close_database_connection(db)

    # Return False for an unsuccessful login
    return False

def register_user(first_name, last_name, country, username, email, password, security_question, security_answer):
    db, cursor = get_database_connection()
    try:
        # Create a Users table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Users (
                first_name TEXT,
                last_name TEXT,
                country TEXT,
                username TEXT UNIQUE,
                email TEXT UNIQUE,
                password TEXT,
                security_question TEXT,
                security_answer TEXT
            )
        ''')

        # Insert user data into the Users table
        cursor.execute('''
            INSERT INTO Users (first_name, last_name, country, username, email, password, security_question, security_answer)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (first_name, last_name, country, username, email, password, security_question, security_answer.lower()))

        # Commit the changes and close the database connection
        db.commit()

        return True  # Registration successful

    except sqlite3.IntegrityError:
        return False  # Username or email is already in use

    finally:
        # Close the database connection
        close_database_connection(db)

def email_exists(email):
    db, cursor = get_database_connection()
    try:
        cursor.execute("SELECT * FROM Users WHERE email = ?", (email,))
        user = cursor.fetchone()

        return user

    finally:
        # Close the database connection
        close_database_connection(db)


def get_countries():
    country_names_unsorted = [country.name for country in pycountry.countries]
    country_names = sorted(country_names_unsorted)
    return country_names


def validate_country(country_name):
    # Check if the entered country is in the list of available countries
    available_countries = get_countries()
    return country_name in available_countries

def update_password(email, temporary_password):
    db, cursor = get_database_connection()
    try:
        # Update the user's password with the temporary password
        update_query = "UPDATE Users SET password = ? WHERE email = ?"
        cursor.execute(update_query, (temporary_password, email))

        # Commit the changes to the database
        db.commit()

        return True  # Password updated successfully

    except Exception as e:
        print("Error updating password:", str(e))
        return False  # Password update failed

    finally:
        # Close the database connection
        close_database_connection(db)


def get_security_question(email):
    db, cursor = get_database_connection()
    try:
        # Assuming you have a table called 'users' with columns 'email', 'security_question', and 'security_answer'
        cursor.execute("SELECT security_question FROM users WHERE email = ?", (email,))
        result = cursor.fetchone()

        if result:
            return result[0]  # Return the security question
        else:
            return None  # User not found or no security question associated with the email

    except sqlite3.Error as e:
        print("Database error:", str(e))
        return None
    finally:
        close_database_connection(db)

def check_security_answer(email, provided_answer):
    db, cursor = get_database_connection()
    try:
        # Assuming you have a table called 'users' with columns 'email', 'security_question', and 'security_answer'
        cursor.execute("SELECT security_answer FROM users WHERE email = ?", (email,))
        result = cursor.fetchone()

        if result:
            stored_answer = result[0]
            # Compare the provided answer with the stored answer (case-insensitive)
            if provided_answer.lower() == stored_answer.lower():
                return True  # Security answer matches
            else:
                return False  # Security answer does not match
        else:
            return False  # User not found or no security answer associated with the email

    except sqlite3.Error as e:
        print("Database error:", str(e))
        return False
    finally:
        close_database_connection(db)

def is_valid_email(email):
    # Regular expression pattern for a valid email address
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'

    # Use the re.match() function to check if the email matches the pattern
    if re.match(pattern, email):
        return True
    else:
        return False

def is_valid_chars(input_string):
    # Regular expression pattern to allow only English letters and standard characters
    pattern = re.compile(r'^[a-zA-Z0-9_\-]+$')
    return pattern.match(input_string) is not None

def is_valid_chars_space(input_string):
    # Regular expression pattern to allow only English letters and standard characters
    pattern = re.compile(r'^[a-zA-Z0-9_\- ]+$')
    return pattern.match(input_string) is not None
