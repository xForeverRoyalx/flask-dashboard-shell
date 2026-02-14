from flask import Flask, render_template, redirect, url_for, request, session, flash

app = Flask(__name__)
app.secret_key = "dev-secret-change-in-prod"


# ---------------------------------------------------------------------------
# Simulated "account" state (replace with DB model later)
# ---------------------------------------------------------------------------

def get_account():
    """Return the current account state from session (stand-in for DB row)."""
    return session.get("account", {
        "first_name": "",
        "last_name": "",
        "email": "user@example.com",
        "email_confirmed": False,
        "profile_complete": False,
        "avatar_uploaded": False,
    })


def save_account(data):
    session["account"] = data


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    account = get_account()
    if not account["profile_complete"]:
        return redirect(url_for("account_setup"))
    return redirect(url_for("account_profile"))


@app.route("/account/setup", methods=["GET", "POST"])
def account_setup():
    account = get_account()

    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name  = request.form.get("last_name", "").strip()
        email      = request.form.get("email", "").strip()

        errors = {}
        if not first_name:
            errors["first_name"] = "First name is required."
        if not last_name:
            errors["last_name"] = "Last name is required."
        if not email or "@" not in email:
            errors["email"] = "A valid email address is required."

        if errors:
            return render_template(
                "change_account_profile.html",
                account=account,
                errors=errors,
                form_data=request.form,
                edit_mode=False,
            )

        account.update({
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "email_confirmed": False,
            "profile_complete": True,
        })
        save_account(account)
        flash("Profile saved — one more step.", "success")
        return redirect(url_for("account_avatar"))

    return render_template(
        "change_account_profile.html",
        account=account,
        errors={},
        form_data={},
        edit_mode=False,
    )


@app.route("/account/profile")
def account_profile():
    account = get_account()
    if not account["profile_complete"]:
        return redirect(url_for("account_setup"))
    return render_template("account_profile.html", account=account)


@app.route("/account/edit", methods=["GET", "POST"])
def account_edit():
    account = get_account()

    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name  = request.form.get("last_name", "").strip()
        email      = request.form.get("email", "").strip()

        errors = {}
        if not first_name:
            errors["first_name"] = "First name is required."
        if not last_name:
            errors["last_name"] = "Last name is required."
        if not email or "@" not in email:
            errors["email"] = "A valid email address is required."

        if errors:
            return render_template(
                "change_account_profile.html",
                account=account,
                errors=errors,
                form_data=request.form,
                edit_mode=True,
            )

        account.update({
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
        })
        save_account(account)
        flash("Account updated.", "success")
        return redirect(url_for("account_profile"))

    return render_template(
        "change_account_profile.html",
        account=account,
        errors={},
        form_data=account,
        edit_mode=True,
    )


@app.route("/account/avatar", methods=["GET", "POST"])
def account_avatar():
    account = get_account()
    if not account["profile_complete"]:
        return redirect(url_for("account_setup"))

    if request.method == "POST":
        if "skip" in request.form:
            return redirect(url_for("account_profile"))

        file = request.files.get("avatar")
        if not file or file.filename == "":
            return render_template("upload_avatar.html", account=account,
                                   error="Please select an image file.")

        allowed = {"png", "jpg", "jpeg", "gif", "webp"}
        ext = file.filename.rsplit(".", 1)[-1].lower()
        if ext not in allowed:
            return render_template("upload_avatar.html", account=account,
                                   error="Allowed types: png, jpg, gif, webp.")

        # TODO: save file to disk/storage, set account["avatar_url"]
        account["avatar_uploaded"] = True
        save_account(account)
        flash("Photo saved.", "success")
        return redirect(url_for("account_profile"))

    return render_template("upload_avatar.html", account=account, error=None)


# Dev helper — reset session to re-test setup flow
@app.route("/dev/reset")
def dev_reset():
    session.clear()
    return redirect(url_for("index"))


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)