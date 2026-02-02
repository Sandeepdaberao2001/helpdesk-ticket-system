
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Blueprint, render_template, request, redirect, url_for, session
from models.models import db, User
from utils.decorators import login_required, role_required
from flask import flash



auth_bp = Blueprint("auth", __name__)

# SHOW REGISTRATION FORM
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]

        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            flash("User already exists!", "error")
            return redirect(url_for("auth.register"))

        hashed_password = generate_password_hash(password)

        new_user = User(
            name=name,
            email=email,
            password=hashed_password,  # ✅ hashed
            role=role
        )

        db.session.add(new_user)
        db.session.commit()

        flash("User registered successfully!", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")

# LOGIN USER
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session.clear()
            session["user_id"] = user.id
            session["user_role"] = user.role
            flash("Login successful!", "success")
            return redirect(url_for("auth.dashboard"))

        else:
            flash("Invalid email or password", "error")
            return redirect(url_for("auth.login"))

    return render_template("login.html")

@auth_bp.route("/dashboard")
@login_required
def dashboard():
    return f"Welcome! Role: {session['user_role']}"

@auth_bp.route("/admin")
@login_required
@role_required("admin")
def admin_panel():
    return "👑 Admin Panel – Full Access"

@auth_bp.route("/agent")
@login_required
@role_required("agent")
def agent_panel():
    return "🛠️ Agent Panel – Support Tasks"

# LOGOUT USER
@auth_bp.route("/logout")
def logout():
    session.clear()   # removes user_id, user_role, everything
    flash("Logged out successfully", "warning")
    return redirect(url_for("auth.login"))


# FETCH USERS
@auth_bp.route("/users")
def get_users():
    users = User.query.all()
    return "<br>".join(
        [f"{u.id} | {u.name} | {u.email} | {u.role}" for u in users]
    )
