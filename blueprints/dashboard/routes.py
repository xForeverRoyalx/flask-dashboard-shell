from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime
from app import db
from models import User
import os

dashboard_bp = Blueprint("dashboard", __name__, template_folder="../templates")


# ---------------------------------------------------------------------------
# Index
# ---------------------------------------------------------------------------

@dashboard_bp.route("/")
def index():
    if not current_user.is_authenticated:
        return redirect(url_for("dashboard.signin"))
    if not current_user.profile_complete:
        return redirect(url_for("dashboard.account_setup"))
    return redirect(url_for("dashboard.overview"))


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

@dashboard_bp.route("/signin", methods=["GET", "POST"])
def signin():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))
    if request.method == "POST":
        email    = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        user = User.query.filter_by(email=email).first()
        if user and user.password_hash and user.check_password(password):
            user.last_login = datetime.utcnow()
            db.session.commit()
            login_user(user)
            flash("Welcome back.", "success")
            return redirect(url_for("dashboard.overview"))
        flash("Invalid email or password.", "danger")
    return render_template("dashboard/signin.html")


@dashboard_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))
    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name  = request.form.get("last_name", "").strip()
        email      = request.form.get("email", "").strip()
        password   = request.form.get("password", "").strip()
        confirm    = request.form.get("confirm_password", "").strip()

        errors = {}
        if not first_name:                    errors["first_name"]        = "Required."
        if not last_name:                     errors["last_name"]         = "Required."
        if not email or "@" not in email:     errors["email"]             = "Valid email required."
        if not password:                      errors["password"]          = "Required."
        elif len(password) < 8:               errors["password"]          = "Minimum 8 characters."
        if password != confirm:               errors["confirm_password"]  = "Passwords do not match."
        if not errors and User.query.filter_by(email=email).first():
                                              errors["email"]             = "An account with that email already exists."

        if errors:
            return render_template("dashboard/signup.html", errors=errors, form_data=request.form)

        user = User(first_name=first_name, last_name=last_name, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash("Account created — add a photo to finish.", "success")
        return redirect(url_for("dashboard.account_setup"))

    return render_template("dashboard/signup.html", errors={}, form_data={})


@dashboard_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("dashboard.signin"))


# ---------------------------------------------------------------------------
# Account setup
# ---------------------------------------------------------------------------

@dashboard_bp.route("/account/setup", methods=["GET", "POST"])
@login_required
def account_setup():
    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name  = request.form.get("last_name", "").strip()
        email      = request.form.get("email", "").strip()
        errors = {}
        if not first_name:                errors["first_name"] = "Required."
        if not last_name:                 errors["last_name"]  = "Required."
        if not email or "@" not in email: errors["email"]      = "Valid email required."
        if errors:
            return render_template("dashboard/change_account_profile.html",
                                   account=current_user, errors=errors,
                                   form_data=request.form, edit_mode=False)
        current_user.first_name = first_name
        current_user.last_name  = last_name
        current_user.email      = email
        db.session.commit()
        flash("Profile saved — one more step.", "success")
        return redirect(url_for("dashboard.account_avatar"))
    return render_template("dashboard/change_account_profile.html",
                           account=current_user, errors={},
                           form_data={
                               "first_name": current_user.first_name,
                               "last_name":  current_user.last_name,
                               "email":      current_user.email,
                           }, edit_mode=False)


@dashboard_bp.route("/account/avatar", methods=["GET", "POST"])
@login_required
def account_avatar():
    if request.method == "POST":
        if "skip" in request.form:
            current_user.profile_complete = True
            db.session.commit()
            return redirect(url_for("dashboard.account_profile"))
        file = request.files.get("avatar")
        if not file or file.filename == "":
            return render_template("dashboard/upload_avatar.html",
                                   account=current_user, error="Please select an image file.")
        ext = file.filename.rsplit(".", 1)[-1].lower()
        if ext not in {"png", "jpg", "jpeg", "gif", "webp"}:
            return render_template("dashboard/upload_avatar.html",
                                   account=current_user, error="Allowed types: png, jpg, gif, webp.")
        file.seek(0, 2)
        if file.tell() > 5 * 1024 * 1024:
            return render_template("dashboard/upload_avatar.html",
                                   account=current_user, error="File exceeds 5MB limit.")
        file.seek(0)
        upload_dir = os.path.join(current_app.root_path, "static", "uploads", "avatars")
        os.makedirs(upload_dir, exist_ok=True)
        filename = f"{current_user.id}.{ext}"
        file.save(os.path.join(upload_dir, filename))
        current_user.avatar_url = url_for("static", filename=f"uploads/avatars/{filename}")
        current_user.avatar_uploaded = True
        current_user.profile_complete = True
        db.session.commit()
        flash("Photo saved.", "success")
        return redirect(url_for("dashboard.account_profile"))
    return render_template("dashboard/upload_avatar.html", account=current_user, error=None)

@dashboard_bp.route("/account/profile")
@login_required
def account_profile():
    return render_template("dashboard/account_profile.html", account=current_user)


@dashboard_bp.route("/account/edit", methods=["GET", "POST"])
@login_required
def account_edit():
    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name  = request.form.get("last_name", "").strip()
        email      = request.form.get("email", "").strip()

        errors = {}
        if not first_name:                errors["first_name"] = "Required."
        if not last_name:                 errors["last_name"]  = "Required."
        if not email or "@" not in email: errors["email"]      = "Valid email required."

        file = request.files.get("avatar")
        if file and file.filename != "":
            ext = file.filename.rsplit(".", 1)[-1].lower()
            if ext not in {"png", "jpg", "jpeg", "gif", "webp"}:
                errors["avatar"] = "Allowed types: png, jpg, gif, webp."
            else:
                file.seek(0, 2)
                if file.tell() > 5 * 1024 * 1024:
                    errors["avatar"] = "File exceeds 5MB limit."
                else:
                    file.seek(0)
                    upload_dir = os.path.join(current_app.root_path, "static", "uploads", "avatars")
                    os.makedirs(upload_dir, exist_ok=True)
                    filename = f"{current_user.id}.{ext}"
                    file.save(os.path.join(upload_dir, filename))
                    current_user.avatar_url = url_for("static", filename=f"uploads/avatars/{filename}")
                    current_user.avatar_uploaded = True

        if errors:
            return render_template("dashboard/change_account_profile.html",
                                   account=current_user, errors=errors,
                                   form_data=request.form, edit_mode=True)

        current_user.first_name = first_name
        current_user.last_name  = last_name
        current_user.email      = email
        db.session.commit()
        flash("Account updated.", "success")
        return redirect(url_for("dashboard.account_profile"))

    return render_template("dashboard/change_account_profile.html",
                           account=current_user, errors={},
                           form_data={
                               "first_name": current_user.first_name,
                               "last_name":  current_user.last_name,
                               "email":      current_user.email,
                           }, edit_mode=True)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

@dashboard_bp.route("/overview")
@login_required
def overview():
    return render_template("dashboard/overview.html", account=current_user)


# ---------------------------------------------------------------------------
# Dev
# ---------------------------------------------------------------------------

@dashboard_bp.route("/dev/reset")
def dev_reset():
    logout_user()
    return redirect(url_for("dashboard.signin"))