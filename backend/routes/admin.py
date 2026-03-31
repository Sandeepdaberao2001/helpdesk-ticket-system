from flask import Blueprint, request

from backend.extensions import comments_col, tickets_col, users_col
from backend.middleware.auth_guard import admin_required
from backend.models.schemas import VALID_ROLES
from backend.utils.mongo_helpers import serialize, to_object_id
from backend.utils.response import error, success

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/stats", methods=["GET"])
@admin_required
def stats():
    def count(query=None):
        return tickets_col.count_documents(query or {})

    data = {
        "tickets": {
            "total":       count(),
            "open":        count({"status": "open"}),
            "in_progress": count({"status": "in_progress"}),
            "resolved":    count({"status": "resolved"}),
            "closed":      count({"status": "closed"}),
        },
        "priority": {
            "critical": count({"priority": "critical"}),
            "high":     count({"priority": "high"}),
            "medium":   count({"priority": "medium"}),
            "low":      count({"priority": "low"}),
        },
        "users": {
            "total":  users_col.count_documents({}),
            "admins": users_col.count_documents({"role": "admin"}),
            "agents": users_col.count_documents({"role": "agent"}),
            "users":  users_col.count_documents({"role": "user"}),
        },
        "unassigned": count({
            "assigned_to": None,
            "status": {"$in": ["open", "in_progress"]}
        }),
        "total_comments": comments_col.count_documents({}),
    }
    return success(data=data)

@admin_bp.route("/users", methods=["GET"])
@admin_required
def list_users():
    page  = max(int(request.args.get("page", 1)), 1)
    limit = 20
    skip  = (page - 1) * limit

    users = list(users_col.find({}).sort("created_at", -1).skip(skip).limit(limit))
    total = users_col.count_documents({})

    safe_users = []
    for u in users:
        s = serialize(u)
        s.pop("password_hash", None)
        s["ticket_count"] = tickets_col.count_documents({"created_by": u["_id"]})
        safe_users.append(s)

    return success(data={
        "users": safe_users,
        "total": total,
        "page":  page,
        "pages": max(1, -(-total // limit)),
    })

@admin_bp.route("/tickets", methods=["GET"])
@admin_required
def all_tickets():
    page = max(int(request.args.get("page", 1)), 1)
    limit = min(max(int(request.args.get("limit", 50)), 1), 100)
    skip = (page - 1) * limit
    total = tickets_col.count_documents({})
    tickets = list(
        tickets_col.find({})
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )
    enriched = []
    for t in tickets:
        s = serialize(t)
        creator = users_col.find_one({"_id": t.get("created_by")})
        s["created_by_username"] = creator["username"] if creator else "Unknown"
        enriched.append(s)
    return success(data={
        "tickets": enriched,
        "total": total,
        "page": page,
        "pages": max(1, -(-total // limit)),
        "per_page": limit,
    })

@admin_bp.route("/users/<user_id>/role", methods=["PUT"])
@admin_required
def update_role(user_id):
    oid = to_object_id(user_id)
    if not oid:
        return error("Invalid user ID.", 400)

    user = users_col.find_one({"_id": oid})
    if not user:
        return error("User not found.", 404)

    data     = request.get_json() or {}
    new_role = data.get("role", "").strip()

    if new_role not in VALID_ROLES:
        return error(f"Role must be one of: {', '.join(VALID_ROLES)}.", 422)

    if user.get("role") == "admin" and new_role != "admin":
        remaining_admins = users_col.count_documents({"role": "admin"})
        if remaining_admins <= 1:
            return error("At least one admin account must remain.", 403)

    users_col.update_one({"_id": oid}, {"$set": {"role": new_role}})
    return success(message=f"Role updated to '{new_role}'.")

@admin_bp.route("/users/<user_id>/toggle", methods=["PUT"])
@admin_required
def toggle_user(user_id):
    oid = to_object_id(user_id)
    if not oid:
        return error("Invalid user ID.", 400)

    user = users_col.find_one({"_id": oid})
    if not user:
        return error("User not found.", 404)

    new_state = not user.get("is_active", True)
    if user.get("role") == "admin" and not new_state:
        remaining_admins = users_col.count_documents({"role": "admin", "is_active": True})
        if remaining_admins <= 1:
            return error("Cannot deactivate the last active admin.", 403)

    users_col.update_one({"_id": oid}, {"$set": {"is_active": new_state}})

    state_label = "activated" if new_state else "deactivated"
    return success(message=f"User {user['username']} {state_label}.")
