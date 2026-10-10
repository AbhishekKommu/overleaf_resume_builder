import re
import sqlite3
from functools import wraps

from flask import session, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in first.", "error")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def register_user(db, username, email, password):
    """Returns (ok, message)."""
    username, email = username.strip(), email.strip().lower()
    if len(username) < 3:
        return False, "Username must be at least 3 characters."
    if not EMAIL_RE.match(email):
        return False, "Enter a valid email address."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."
    try:
        db.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (username, email, generate_password_hash(password)),
        )
        db.commit()
    except sqlite3.IntegrityError:
        return False, "Username or email already exists."
    return True, "Account created. Please log in."


def authenticate(db, identifier, password):
    """Returns the user row or None."""
    user = db.execute(
        "SELECT * FROM users WHERE username = ? OR email = ?",
        (identifier.strip(), identifier.strip().lower()),
    ).fetchone()
    if user and check_password_hash(user["password_hash"], password):
        return user
    return None
