from functools import wraps
from flask import session, redirect, url_for

def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        return func(*args, **kwargs)
    return wrapper

def role_required(required_role):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if "user_id" not in session:
                return redirect(url_for("auth.login"))

            if session.get("user_role") != required_role:
                return "❌ Access Denied: Unauthorized Role", 403

            return func(*args, **kwargs)
        return wrapper
    return decorator
