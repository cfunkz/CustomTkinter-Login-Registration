# CustomTkinter-Login-Registration
Registration and login app made using customtkinter.

This includes a sqlite3 database setup with many functions including saving the registration data, logging in, password reset, security questions, country selection and more. 
Change the config.py file for your details to test e-mail functions. You can get the gmail app password [HERE](https://myaccount.google.com/apppasswords)


`pip install tkinter`,
`pip install customtkinter`,
`pip install pycountry`,
`pip install Pillow`,

<img width="451" alt="image" src="https://github.com/didis97/CustomTkinter-Login-Registration/assets/116670695/c9df6bdd-d391-43d6-afa1-f203a4694a53">
<img width="449" alt="image" src="https://github.com/didis97/CustomTkinter-Login-Registration/assets/116670695/535dd044-82b6-4a17-8736-fb054557f712">
<img width="449" alt="image" src="https://github.com/didis97/CustomTkinter-Login-Registration/assets/116670695/b1037e9f-0591-4ef3-b7b4-79fd9f05496a">
<img width="449" alt="image" src="https://github.com/didis97/CustomTkinter-Login-Registration/assets/116670695/cba1b69a-774a-4629-b380-807f71122eda">
<img width="449" alt="image" src="https://github.com/didis97/CustomTkinter-Login-Registration/assets/116670695/66c35a0a-9c01-4800-b3d9-3c343806cfb2">
<img width="450" alt="image" src="https://github.com/didis97/CustomTkinter-Login-Registration/assets/116670695/7d902c2e-4184-4e7e-9741-25618fec6bfd">

# User Database Functions

The following functions are used for managing user data in a SQLite database.

### `get_database_connection()`
- Opens a database connection and returns the connection and cursor.

### `close_database_connection(db)`
- Closes the provided database connection.

### `register_user(first_name, last_name, country, username, email, password, security_question, security_answer)`
- Registers a new user with the provided information.
- Returns `True` for successful registration, or `False` if the username or email is already in use.

### `check_login(username, password)`
- Checks if the provided username and password match a record in the Users table.
- Returns `True` for a successful login, or `False` for an unsuccessful login.

### `email_exists(email)`
- Checks if an email address exists in the Users table.
- Returns user data if the email exists, or `None` if not found.

### `update_password(email, temporary_password)`
- Updates the user's password with a temporary password.
- Returns `True` for a successful password update, or `False` for a failure.

### `get_security_question(email)`
- Retrieves the security question associated with the given email address.
- Returns the security question or `None` if the email is not found.

### `check_security_answer(email, provided_answer)`
- Checks if the provided security answer matches the stored security answer associated with the email address.
- Returns `True` if the security answer matches, or `False` if it does not.

### `is_valid_email(email)`
- Validates if the provided email address follows the standard email format.
- Returns `True` for valid email addresses, or `False` for invalid ones.

### `generate_temporary_password(length=8)`
- Generates a random temporary password of the specified length (default is 8 characters).

### `send_password_reset_email(email, temporary_password)`
- Sends a password reset email to the provided email address with the temporary password.

# UI Functions

The following functions are used for UI-related tasks.

### `test_buttons()`
- A placeholder function to test button functionality.

### `toggle_password(p_block, show_password_var)`
- Toggles the visibility of a password entry field based on a Boolean variable.

### `get_countries()`
- Retrieves a list of country names sorted in alphabetical order.

### `validate_country(country_name)`
- Checks if the entered country name is in the list of available countries obtained from `get_countries()`.
