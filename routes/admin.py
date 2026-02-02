from flask import Blueprint, render_template
from models.models import Ticket, User
from utils.decorators import login_required, role_required

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/admin/tickets")
@login_required
@role_required("admin")
def all_tickets():
    tickets = Ticket.query.all()
    agents = User.query.filter_by(role="agent").all()
    return render_template(
        "admin_tickets.html",
        tickets=tickets,
        agents=agents
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
