from datetime import datetime
from flask import Blueprint, request, g

from backend.extensions import comments_col, tickets_col, users_col
from backend.middleware.auth_guard import login_required
from backend.models.schemas import validate_comment, validate_ticket, validate_ticket_update
from backend.utils.mongo_helpers import serialize, to_object_id
from backend.utils.response import error, success

tickets_bp = Blueprint("tickets", __name__)


@tickets_bp.route("/", methods=["GET"])
@login_required
def list_tickets():
    page     = max(int(request.args.get("page",     1)), 1)
    limit    = 10
    skip     = (page - 1) * limit
    status   = request.args.get("status",   "")
    priority = request.args.get("priority", "")
    search   = request.args.get("search",   "").strip()

    query = {}

    if g.current_user.get("role") == "user":
        query["created_by"] = g.current_user["_id"]

    if status:
        query["status"] = status
    if priority:
        query["priority"] = priority
    if search:
        query["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
        ]

    total   = tickets_col.count_documents(query)
    tickets = list(
        tickets_col.find(query)
        .sort("created_at", -1)                # newest first
        .skip(skip)
        .limit(limit)
    )

    enriched = []
    for t in tickets:
        s = serialize(t)
        creator = users_col.find_one({"_id": t.get("created_by")})
        s["created_by_username"] = creator["username"] if creator else "Unknown"
        if t.get("assigned_to"):
            agent = users_col.find_one({"_id": t["assigned_to"]})
            s["assigned_to_username"] = agent["username"] if agent else None
        s["comment_count"] = comments_col.count_documents({"ticket_id": t["_id"]})
        enriched.append(s)

    return success(data={
        "tickets":    enriched,
        "total":      total,
        "page":       page,
        "pages":      max(1, -(-total // limit)),
        "per_page":   limit,
    })

@tickets_bp.route("/", methods=["POST"])
@login_required
def create_ticket():
    data = request.get_json() or {}
    ok, errors = validate_ticket(data)
    if not ok:
        return error("Validation failed.", 422, errors)

    now = datetime.utcnow()
    ticket = {
        "title":       data["title"].strip(),
        "description": data["description"].strip(),
        "priority":    data.get("priority", "medium").strip().lower(),
        "category":    data.get("category", "General").strip(),
        "status":      "open",
        "created_by":  g.current_user["_id"],
        "assigned_to": None,
        "created_at":  now,
        "updated_at":  now,
        "resolved_at": None,
    }
    result = tickets_col.insert_one(ticket)

    new_ticket = tickets_col.find_one({"_id": result.inserted_id})
    return success(
        data={"ticket": serialize(new_ticket)},
        message="Ticket created successfully.",
        status=201
    )


@tickets_bp.route("/<ticket_id>", methods=["GET"])
@login_required
def get_ticket(ticket_id):
    oid = to_object_id(ticket_id)
    if not oid:
        return error("Invalid ticket ID.", 400)

    ticket = tickets_col.find_one({"_id": oid})
    if not ticket:
        return error("Ticket not found.", 404)

    is_owner = str(ticket["created_by"]) == g.current_user_id
    is_agent = g.current_user.get("role") in ("agent", "admin")
    if not is_owner and not is_agent:
        return error("Access denied.", 403)

    s = serialize(ticket)

    creator = users_col.find_one({"_id": ticket["created_by"]})
    s["created_by_username"] = creator["username"] if creator else "Unknown"

    if ticket.get("assigned_to"):
        agent = users_col.find_one({"_id": ticket["assigned_to"]})
        s["assigned_to_username"] = agent["username"] if agent else None

    raw_comments = list(
        comments_col.find({"ticket_id": oid}).sort("created_at", 1)
    )
    comments_out = []
    for c in raw_comments:
        if c.get("is_internal") and not is_agent:
            continue
        cs = serialize(c)
        author = users_col.find_one({"_id": c["user_id"]})
        cs["author_username"] = author["username"] if author else "Unknown"
        cs["author_role"]     = author["role"]     if author else "user"
        comments_out.append(cs)

    s["comments"] = comments_out

    agents = []
    if is_agent:
        agent_docs = users_col.find({"role": {"$in": ["agent", "admin"]}})
        agents = [{"id": str(a["_id"]), "username": a["username"]} for a in agent_docs]

    return success(data={"ticket": s, "agents": agents})

@tickets_bp.route("/<ticket_id>", methods=["PUT"])
@login_required
def update_ticket(ticket_id):
    oid = to_object_id(ticket_id)
    if not oid:
        return error("Invalid ticket ID.", 400)

    ticket = tickets_col.find_one({"_id": oid})
    if not ticket:
        return error("Ticket not found.", 404)

    is_owner = str(ticket["created_by"]) == g.current_user_id
    is_agent = g.current_user.get("role") in ("agent", "admin")

    if not is_owner and not is_agent:
        return error("Access denied.", 403)

    data = request.get_json() or {}
    ok, errors = validate_ticket_update(data)
    if not ok:
        return error("Validation failed.", 422, errors)

    updates = {"updated_at": datetime.utcnow()}

    if "status" in data:
        new_status = str(data["status"]).strip().lower()
        if not is_agent and new_status not in ("closed",):
            return error("Users can only close their own tickets.", 403)
        updates["status"] = new_status
        if new_status == "resolved":
            updates["resolved_at"] = datetime.utcnow()
        elif ticket.get("resolved_at") is not None:
            updates["resolved_at"] = None

    if "priority" in data and is_agent:
        updates["priority"] = str(data["priority"]).strip().lower()

    if "assigned_to" in data and is_agent:
        if not data["assigned_to"]:
            updates["assigned_to"] = None
        else:
            agent_oid = to_object_id(data["assigned_to"])
            if not agent_oid:
                return error("Invalid assignee ID.", 400)
            agent_user = users_col.find_one({"_id": agent_oid})
            if agent_user and agent_user.get("role") in ("agent", "admin"):
                updates["assigned_to"] = agent_oid
            else:
                return error("Assignee must be an active agent or admin.", 422)

    tickets_col.update_one({"_id": oid}, {"$set": updates})
    updated = tickets_col.find_one({"_id": oid})
    return success(data={"ticket": serialize(updated)}, message="Ticket updated.")


@tickets_bp.route("/<ticket_id>/comments", methods=["POST"])
@login_required
def add_comment(ticket_id):
    oid = to_object_id(ticket_id)
    if not oid:
        return error("Invalid ticket ID.", 400)

    ticket = tickets_col.find_one({"_id": oid})
    if not ticket:
        return error("Ticket not found.", 404)

    is_owner = str(ticket["created_by"]) == g.current_user_id
    is_agent = g.current_user.get("role") in ("agent", "admin")
    if not is_owner and not is_agent:
        return error("Access denied.", 403)

    data = request.get_json() or {}
    ok, errors = validate_comment(data)
    if not ok:
        return error("Validation failed.", 422, errors)

    comment = {
        "ticket_id":   oid,
        "user_id":     g.current_user["_id"],
        "message":     data["message"].strip(),
        "is_internal": bool(data.get("is_internal")) and is_agent,
        "created_at":  datetime.utcnow(),
    }
    result  = comments_col.insert_one(comment)
    new_com = comments_col.find_one({"_id": result.inserted_id})

    cs = serialize(new_com)
    cs["author_username"] = g.current_user["username"]
    cs["author_role"]     = g.current_user["role"]

    if is_agent and ticket["status"] == "open":
        tickets_col.update_one(
            {"_id": oid},
            {"$set": {"status": "in_progress", "updated_at": datetime.utcnow()}}
        )

    return success(data={"comment": cs}, message="Comment added.", status=201)
