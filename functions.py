import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import string
import config

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
    smtp_username = config.smtp_username
    smtp_password = config.smtp_password

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
    try:
        db, cursor = get_database_connection()

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

def register_user(first_name, last_name, country, username, email, password):
    try:
        db, cursor = get_database_connection()

        # Create a Users table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Users (
                first_name TEXT,
                last_name TEXT,
                country TEXT,
                username TEXT UNIQUE,
                email TEXT UNIQUE,
                password TEXT
            )
        ''')

        # Insert user data into the Users table
        cursor.execute('''
            INSERT INTO Users (first_name, last_name, country, username, email, password)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (first_name, last_name, country, username, email, password))

        # Commit the changes and close the database connection
        db.commit()

        return True  # Registration successful

    except sqlite3.IntegrityError:
        return False  # Username or email is already in use

    finally:
        # Close the database connection
        close_database_connection(db)

def email_exists(email):
    try:
        db, cursor = get_database_connection()

        cursor.execute("SELECT * FROM Users WHERE email = ?", (email,))
        user = cursor.fetchone()

        return user

    finally:
        # Close the database connection
        close_database_connection(db)



def update_password(email, temporary_password):
    try:
        db, cursor = get_database_connection()

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
