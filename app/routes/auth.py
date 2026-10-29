"""Authentication blueprint: user registration, login, logout, and session safety."""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db
from app.models.user import User
from app.services.wallet_service import wallet_service

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """Register a new student account, grant 50 welcome points, and create wallet."""
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        location = request.form.get("location", "Campus / Remote").strip()

        # Server-side validation
        if not full_name or not email or not password:
            flash("All required fields must be completed.", "danger")
            return render_template("auth/register.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "danger")
            return render_template("auth/register.html")

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("auth/register.html")

        if User.query.filter_by(email=email).first():
            flash("An account with this email address already exists.", "warning")
            return render_template("auth/register.html")

        # Create persistent user record
        user = User(
            full_name=full_name,
            email=email,
            location=location,
        )
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

        # Provision wallet with welcome grant
        wallet_service.create_wallet_for_user(user.id, initial_points=50.0)
        db.session.commit()

        login_user(user)
        flash("Welcome to SkillSwap! 50 bonus points have been credited to your wallet.", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Authenticate student credentials and establish session."""
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember"))

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            flash("Invalid email or password.", "danger")
            return render_template("auth/login.html")

        if not user.is_active:
            flash("This account has been deactivated. Please contact support.", "danger")
            return render_template("auth/login.html")

        login_user(user, remember=remember)
        flash(f"Welcome back, {user.full_name}!", "success")
        next_page = request.args.get("next")
        return redirect(next_page or url_for("main.dashboard"))

    return render_template("auth/login.html")


@auth_bp.route("/logout", methods=["GET", "POST"])
@login_required
def logout():
    """Terminate authenticated session."""
    logout_user()
    flash("You have been signed out successfully.", "info")
    return redirect(url_for("main.index"))
