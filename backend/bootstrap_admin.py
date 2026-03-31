from pathlib import Path

if __package__ in (None, ""):
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import argparse
import getpass
from datetime import datetime

import bcrypt
from pymongo.errors import ServerSelectionTimeoutError

from backend.extensions import create_indexes, users_col


def _build_parser():
    parser = argparse.ArgumentParser(description="Create or update the first admin account.")
    parser.add_argument("--email", help="Admin email address")
    parser.add_argument("--username", help="Admin username")
    parser.add_argument("--password", help="Admin password")
    return parser


def _prompt(value, label, secret=False):
    if value:
        return value.strip()
    if secret:
        return getpass.getpass(f"{label}: ").strip()
    return input(f"{label}: ").strip()


def upsert_admin(email: str, username: str, password: str):
    if len(password) < 10:
        raise ValueError("Admin password must be at least 10 characters.")

    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    existing = users_col.find_one({"email": email})

    payload = {
        "username": username,
        "email": email,
        "password_hash": password_hash,
        "role": "admin",
        "is_active": True,
    }

    if existing:
        users_col.update_one({"_id": existing["_id"]}, {"$set": payload})
        return f"Updated existing admin account for {email}."

    payload["created_at"] = datetime.utcnow()
    users_col.insert_one(payload)
    return f"Created admin account for {email}."


def main():
    args = _build_parser().parse_args()
    email = _prompt(args.email, "Admin email").lower()
    username = _prompt(args.username, "Admin username")
    password = _prompt(args.password, "Admin password", secret=True)

    if not email or "@" not in email:
        raise ValueError("A valid admin email is required.")
    if not username or len(username) < 3:
        raise ValueError("Admin username must be at least 3 characters.")

    try:
        create_indexes()
    except ServerSelectionTimeoutError as exc:
        raise RuntimeError(
            "MongoDB is not reachable. Start MongoDB or update MONGO_URI in backend/.env "
            "before creating the admin account."
        ) from exc
    message = upsert_admin(email=email, username=username, password=password)
    print(message)


if __name__ == "__main__":
    raise SystemExit(main())
