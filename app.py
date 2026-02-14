from flask import Flask, render_template, redirect, url_for, request, session, flash

app = Flask(__name__)
app.secret_key = "dev-secret-change-in-prod"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_account():
    return session.get("account", {
        "first_name": "",
        "last_name": "",
        "email": "",
        "email_confirmed": False,
        "profile_complete": False,
        "avatar_uploaded": False,
    })

def save_account(data):
    session["account"] = data

def is_authenticated():
    return session.get("authenticated", False)

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not is_authenticated():
            return redirect(url_for("signin"))
        return f(*args, **kwargs)
    return decorated


# ---------------------------------------------------------------------------
# Auth routes (stubbed)
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    if not is_authenticated():
        return redirect(url_for("signin"))
    account = get_account()
    if not account["profile_complete"]:
        return redirect(url_for("account_setup"))
    return redirect(url_for("overview"))


@app.route("/signin", methods=["GET", "POST"])
def signin():
    if is_authenticated():
        return redirect(url_for("index"))
    if request.method == "POST":
        email    = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        # STUB — accept any non-empty credentials
        if email and password:
            session["authenticated"] = True
            account = get_account()
            account["email"] = email
            account["profile_complete"] = True   # stub: existing user
            save_account(account)
            flash("Welcome back.", "success")
            return redirect(url_for("overview"))
        flash("Invalid email or password.", "danger")
    return render_template("dashboard/signin.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if is_authenticated():
        return redirect(url_for("index"))
    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name  = request.form.get("last_name", "").strip()
        email      = request.form.get("email", "").strip()
        password   = request.form.get("password", "").strip()
        confirm    = request.form.get("confirm_password", "").strip()

        errors = {}
        if not first_name:          errors["first_name"] = "Required."
        if not last_name:           errors["last_name"]  = "Required."
        if not email or "@" not in email:
                                    errors["email"]      = "Valid email required."
        if not password:            errors["password"]   = "Required."
        elif len(password) < 8:     errors["password"]   = "Minimum 8 characters."
        if password != confirm:     errors["confirm_password"] = "Passwords do not match."

        if errors:
            return render_template("dashboard/signup.html", errors=errors, form_data=request.form)

        # STUB — create session as new user
        session["authenticated"] = True
        account = get_account()
        account.update({
            "first_name": first_name,
            "last_name":  last_name,
            "email":      email,
            "profile_complete": False,
        })
        save_account(account)
        flash("Account created — add a photo to finish.", "success")
        return redirect(url_for("account_avatar"))

    return render_template("dashboard/signup.html", errors={}, form_data={})


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("signin"))


# ---------------------------------------------------------------------------
# Account setup routes
# ---------------------------------------------------------------------------

@app.route("/account/setup", methods=["GET", "POST"])
@login_required
def account_setup():
    account = get_account()
    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name  = request.form.get("last_name", "").strip()
        email      = request.form.get("email", "").strip()
        errors = {}
        if not first_name:              errors["first_name"] = "Required."
        if not last_name:               errors["last_name"]  = "Required."
        if not email or "@" not in email: errors["email"]    = "Valid email required."
        if errors:
            return render_template("dashboard/change_account_profile.html",
                                   account=account, errors=errors,
                                   form_data=request.form, edit_mode=False)
        account.update({"first_name": first_name, "last_name": last_name,
                        "email": email, "profile_complete": False})
        save_account(account)
        flash("Profile saved — one more step.", "success")
        return redirect(url_for("account_avatar"))
    return render_template("dashboard/change_account_profile.html", account=account,
                           errors={}, form_data={}, edit_mode=False)


@app.route("/account/avatar", methods=["GET", "POST"])
@login_required
def account_avatar():
    account = get_account()
    if request.method == "POST":
        if "skip" in request.form:
            account["profile_complete"] = True
            save_account(account)
            return redirect(url_for("account_profile"))
        file = request.files.get("avatar")
        if not file or file.filename == "":
            return render_template("dashboard/upload_avatar.html", account=account,
                                   error="Please select an image file.")
        ext = file.filename.rsplit(".", 1)[-1].lower()
        if ext not in {"png", "jpg", "jpeg", "gif", "webp"}:
            return render_template("dashboard/upload_avatar.html", account=account,
                                   error="Allowed types: png, jpg, gif, webp.")
        # TODO: save file to disk/storage, set account["avatar_url"]
        account["avatar_uploaded"] = True
        account["profile_complete"] = True
        save_account(account)
        flash("Photo saved.", "success")
        return redirect(url_for("account_profile"))
    return render_template("dashboard/upload_avatar.html", account=account, error=None)


@app.route("/account/profile")
@login_required
def account_profile():
    account = get_account()
    return render_template("dashboard/account_profile.html", account=account)


@app.route("/account/edit", methods=["GET", "POST"])
@login_required
def account_edit():
    account = get_account()
    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name  = request.form.get("last_name", "").strip()
        email      = request.form.get("email", "").strip()
        errors = {}
        if not first_name:              errors["first_name"] = "Required."
        if not last_name:               errors["last_name"]  = "Required."
        if not email or "@" not in email: errors["email"]    = "Valid email required."
        if errors:
            return render_template("dashboard/change_account_profile.html", account=account,
                                   errors=errors, form_data=request.form, edit_mode=True)
        account.update({"first_name": first_name, "last_name": last_name, "email": email})
        save_account(account)
        flash("Account updated.", "success")
        return redirect(url_for("account_profile"))
    return render_template("dashboard/change_account_profile.html", account=account,
                           errors={}, form_data=account, edit_mode=True)


# ---------------------------------------------------------------------------
# Main app routes
# ---------------------------------------------------------------------------

@app.route("/overview")
@login_required
def overview():
    account = get_account()
    return render_template("dashboard/overview.html", account=account)


# ---------------------------------------------------------------------------
# Dev
# ---------------------------------------------------------------------------

@app.route("/dev/reset")
def dev_reset():
    session.clear()
    return redirect(url_for("signin"))


if __name__ == "__main__":
    app.run(debug=True)