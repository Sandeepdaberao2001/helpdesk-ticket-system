"""
Lightweight manual validation (no extra lib needed).
Returns (True, None) on pass, (False, [errors]) on fail.
"""

VALID_PRIORITIES = {"low", "medium", "high", "critical"}
VALID_STATUSES   = {"open", "in_progress", "resolved", "closed"}
VALID_ROLES      = {"user", "agent", "admin"}
VALID_CATEGORIES = {"General", "Technical", "Billing", "Account", "Feature Request", "Other"}


def validate_register(data: dict):
    errors = []
    username = (data.get("username") or "").strip()
    email    = (data.get("email")    or "").strip().lower()
    password = (data.get("password") or "")

    if not username or len(username) < 3:
        errors.append("Username must be at least 3 characters.")
    if not email or "@" not in email:
        errors.append("A valid email is required.")
    if not password or len(password) < 6:
        errors.append("Password must be at least 6 characters.")

    return (True, None) if not errors else (False, errors)


def validate_login(data: dict):
    errors = []
    if not data.get("email"):
        errors.append("Email is required.")
    if not data.get("password"):
        errors.append("Password is required.")
    return (True, None) if not errors else (False, errors)


def validate_ticket(data: dict):
    errors = []
    title       = (data.get("title")       or "").strip()
    description = (data.get("description") or "").strip()
    priority    = (data.get("priority")    or "medium").lower()
    category    = (data.get("category")    or "General")

    if not title or len(title) < 5:
        errors.append("Title must be at least 5 characters.")
    if not description or len(description) < 10:
        errors.append("Description must be at least 10 characters.")
    if priority not in VALID_PRIORITIES:
        errors.append(f"Priority must be one of: {', '.join(VALID_PRIORITIES)}.")
    if category not in VALID_CATEGORIES:
        errors.append(f"Category must be one of: {', '.join(VALID_CATEGORIES)}.")

    return (True, None) if not errors else (False, errors)


def validate_ticket_update(data: dict):
    errors = []
    status   = data.get("status")
    priority = data.get("priority")

    if status and status not in VALID_STATUSES:
        errors.append(f"Status must be one of: {', '.join(VALID_STATUSES)}.")
    if priority and priority not in VALID_PRIORITIES:
        errors.append(f"Priority must be one of: {', '.join(VALID_PRIORITIES)}.")

    return (True, None) if not errors else (False, errors)


def validate_comment(data: dict):
    message = (data.get("message") or "").strip()
    if not message or len(message) < 1:
        return (False, ["Comment message cannot be empty."])
    return (True, None)