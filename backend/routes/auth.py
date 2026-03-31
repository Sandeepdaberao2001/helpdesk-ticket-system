import jwt
import bcrypt
from datetime import datetime, timedelta, timezone
from flask import Blueprint, request, g

from backend.config import Config
from backend.extensions import users_col
from backend.middleware.auth_guard import login_required
from backend.models.schemas import validate_login, validate_register
from backend.utils.mongo_helpers import serialize
from backend.utils.response import error, success

auth_bp = Blueprint("auth", __name__)

def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def _check_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def _generate_jwt(user_id: str, role: str) -> str:
    payload = {
        "user_id": user_id,
        "role":    role,
        "exp":     datetime.now(timezone.utc) + timedelta(hours=Config.JWT_EXPIRY_HOURS)
    }
    return jwt.encode(payload, Config.JWT_SECRET_KEY, algorithm="HS256")


def _safe_user(user: dict) -> dict:
    """Strip password_hash before sending user to frontend."""
    s = serialize(user)
    s.pop("password_hash", None)
    return s


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    ok, errors = validate_register(data)
    if not ok:
        return error("Validation failed.", 422, errors)

    username = data["username"].strip()
    email    = data["email"].strip().lower()
    password = data["password"]

    # Uniqueness check
    if users_col.find_one({"email": email}):
        return error("Email is already registered.", 409)
    if users_col.find_one({"username": username}):
        return error("Username is already taken.", 409)

    new_user = {
        "username":      username,
        "email":         email,
        "password_hash": _hash_password(password),
        "role":          "user",          # all new users start as 'user'
        "is_active":     True,
        "created_at":    datetime.utcnow(),
    }
    result  = users_col.insert_one(new_user)
    user_id = str(result.inserted_id)
    token   = _generate_jwt(user_id, "user")

    return success(
        data={"token": token, "user": _safe_user(users_col.find_one({"_id": result.inserted_id}))},
        message="Account created successfully.",
        status=201
    )


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    ok, errors = validate_login(data)
    if not ok:
        return error("Validation failed.", 422, errors)

    email    = data["email"].strip().lower()
    password = data["password"]

    user = users_col.find_one({"email": email})

    if not user or not _check_password(password, user["password_hash"]):
        return error("Invalid email or password.", 401)

    if not user.get("is_active", True):
        return error("Your account has been deactivated. Contact support.", 403)

    token = _generate_jwt(str(user["_id"]), user["role"])

    return success(
        data={"token": token, "user": _safe_user(user)},
        message=f"Welcome back, {user['username']}!"
    )


@auth_bp.route("/me", methods=["GET"])
@login_required
def me():
    return success(data={"user": _safe_user(g.current_user)})
