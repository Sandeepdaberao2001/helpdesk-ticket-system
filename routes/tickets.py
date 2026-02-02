from flask import Blueprint, render_template, request, redirect, url_for, session
from models.models import db, Ticket
from utils.decorators import login_required, role_required
from flask import flash
from models.models import Comment
from flask import request, flash
from models.models import TicketStatusHistory



tickets_bp = Blueprint("tickets", __name__)

# SHOW CREATE TICKET FORM
@tickets_bp.route("/tickets/create", methods=["GET", "POST"])
@login_required
def create_ticket():
    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        priority = request.form["priority"]

        ticket = Ticket(
            title=title,
            description=description,
            priority=priority,
            status="Open",
            created_by=session["user_id"]
        )

        db.session.add(ticket)
        db.session.commit()

        flash("Ticket created successfully!", "success")
        return redirect(url_for("tickets.my_tickets"))

    return render_template("create_ticket.html")


# VIEW USER'S OWN TICKETS
@tickets_bp.route("/tickets/my")
@login_required
def my_tickets():
    tickets = Ticket.query.filter_by(created_by=session["user_id"]).all()

    output = "<h2>My Tickets</h2>"
    for t in tickets:
        output += f"""
        <p>
        <b>{t.title}</b><br>
        {t.description}<br>
        Priority: {t.priority} | Status: {t.status}
        </p><hr>
        """

    return render_template("my_tickets.html", tickets=tickets)

@tickets_bp.route("/agent/my-tickets")
@login_required
@role_required("agent")
def agent_tickets():
    tickets = Ticket.query.filter_by(assigned_to=session["user_id"]).all()
    return render_template("my_tickets.html", tickets=tickets)

# What this route does
#
# ✔ Only logged-in agents
# ✔ Only assigned tickets
# ✔ Updates status safely
# ✔ Uses flash feedback
@tickets_bp.route("/tickets/update-status/<int:ticket_id>", methods=["POST"])
@login_required
@role_required("agent")
def update_ticket_status(ticket_id):
    new_status = request.form["status"]
    ticket = Ticket.query.get(ticket_id)

    # Security check (agent can update only assigned tickets)
    if ticket.assigned_to != session["user_id"]:
        flash("Unauthorized action", "error")
        return redirect(url_for("tickets.agent_tickets"))

    old_status = ticket.status

    ticket.status = new_status

    history = TicketStatusHistory(
        ticket_id=ticket.id,
        old_status=old_status,
        new_status=new_status,
        changed_by=session["user_id"]
    )

    db.session.add(history)
    db.session.commit()

    flash("Ticket status updated", "success")
    return redirect(url_for("tickets.agent_tickets"))


@tickets_bp.route("/tickets/<int:ticket_id>")
@login_required
def ticket_detail(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    comments = Comment.query.filter_by(ticket_id=ticket_id).order_by(Comment.created_at).all()
    history = TicketStatusHistory.query.filter_by(ticket_id=ticket_id)\
              .order_by(TicketStatusHistory.changed_at).all()

    return render_template(
        "ticket_detail.html",
        ticket=ticket,
        comments=comments,
        history=history
    )


@tickets_bp.route("/tickets/<int:ticket_id>/comment", methods=["POST"])
@login_required
def add_comment(ticket_id):
    message = request.form["message"]

    if not message.strip():
        flash("Comment cannot be empty", "error")
        return redirect(url_for("tickets.ticket_detail", ticket_id=ticket_id))

    comment = Comment(
        ticket_id=ticket_id,
        user_id=session["user_id"],
        message=message
    )

    db.session.add(comment)
    db.session.commit()

    flash("Comment added", "success")
    return redirect(url_for("tickets.ticket_detail", ticket_id=ticket_id))

