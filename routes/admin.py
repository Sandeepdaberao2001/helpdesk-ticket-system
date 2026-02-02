from flask import Blueprint, render_template
from models.models import Ticket, User
from utils.decorators import login_required, role_required

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/admin/tickets")
@login_required
@role_required("admin")
def admin_tickets():
    tickets = Ticket.query.all()
    agents = User.query.filter_by(role="agent").all()

    # 📊 SIMPLE ANALYTICS
    total_tickets = Ticket.query.count()
    open_tickets = Ticket.query.filter_by(status="Open").count()
    in_progress_tickets = Ticket.query.filter_by(status="In Progress").count()
    resolved_tickets = Ticket.query.filter_by(status="Resolved").count()

    # Tickets per agent
    agent_stats = []
    for agent in agents:
        count = Ticket.query.filter_by(assigned_to=agent.id).count()
        agent_stats.append({
            "name": agent.name,
            "count": count
        })

    return render_template(
        "admin_tickets.html",
        tickets=tickets,
        agents=agents,
        total_tickets=total_tickets,
        open_tickets=open_tickets,
        in_progress_tickets=in_progress_tickets,
        resolved_tickets=resolved_tickets,
        agent_stats=agent_stats
    )

from flask import request, redirect, url_for, flash
from models.models import db

@admin_bp.route("/admin/assign/<int:ticket_id>", methods=["POST"])
@login_required
@role_required("admin")
def assign_ticket(ticket_id):
    agent_id = request.form["agent_id"]
    ticket = Ticket.query.get(ticket_id)

    ticket.assigned_to = agent_id
    ticket.status = "In Progress"

    db.session.commit()

    flash("Ticket assigned successfully", "success")
    return redirect(url_for("admin.all_tickets"))
