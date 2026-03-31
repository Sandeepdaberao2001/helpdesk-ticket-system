import jwt
from functools import wraps
from flask import request, g

from backend.config import Config
from backend.extensions import users_col
from backend.utils.mongo_helpers import to_object_id
from backend.utils.response import error


def _decode_token():
    """
    Reads the Authorization header, decodes the JWT.
    Returns the payload dict or None.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None

    token = auth_header.split(" ")[1]           # "Bearer <token>" -> token
    try:
        payload = jwt.decode(
            token,
            Config.JWT_SECRET_KEY,
            algorithms=["HS256"]
        )
        return payload
    except jwt.ExpiredSignatureError:
        return "expired"
    except jwt.InvalidTokenError:
        return None


def _load_current_user(payload):
    user = users_col.find_one({"_id": to_object_id(payload["user_id"])})
    if not user or not user.get("is_active"):
        return None

    g.current_user = user
    g.current_user_id = str(user["_id"])
    return user


def login_required(f):
    """
    Decorator: any logged-in user can access.
    Injects g.current_user for use in the route.

    Usage:
        @tickets_bp.route('/api/tickets')
        @login_required
        def get_tickets():
            user = g.current_user
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        payload = _decode_token()

        if payload == "expired":
            return error("Session expired. Please log in again.", 401)
        if not payload:
            return error("Authentication required.", 401)

        if not _load_current_user(payload):
            return error("User not found or deactivated.", 401)
        return f(*args, **kwargs)

    return decorated


def agent_required(f):
    """
    Decorator: only agents and admins.
    Must be used AFTER @login_required.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        payload = _decode_token()
        if payload == "expired":
            return error("Session expired.", 401)
        if not payload:
            return error("Authentication required.", 401)

        user = _load_current_user(payload)
        if not user or user.get("role") not in ("agent", "admin"):
            return error("Agent or Admin access required.", 403)
        return f(*args, **kwargs)

    return decorated


def admin_required(f):
    """
    Decorator: only admins.
    Must be used AFTER @login_required.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        payload = _decode_token()
        if payload == "expired":
            return error("Session expired.", 401)
        if not payload:
            return error("Authentication required.", 401)

        user = _load_current_user(payload)
        if not user or user.get("role") != "admin":
            return error("Admin access required.", 403)
        return f(*args, **kwargs)

    return decorated
