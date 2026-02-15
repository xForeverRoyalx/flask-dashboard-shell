import os
from flask import Flask
from dotenv import load_dotenv
from extensions import db, login_manager

load_dotenv()


def create_app():
    app = Flask(__name__, instance_relative_config=True)

    # -------------------------------------------------------------------------
    # Config
    # -------------------------------------------------------------------------
    app.config["SECRET_KEY"]                     = os.getenv("SECRET_KEY", "dev-secret-change-in-prod")
    app.config["SQLALCHEMY_DATABASE_URI"]        = "sqlite:///site.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    app.config["GOOGLE_CLIENT_ID"]               = os.getenv("GOOGLE_CLIENT_ID")
    app.config["GOOGLE_CLIENT_SECRET"]           = os.getenv("GOOGLE_CLIENT_SECRET")
    app.config["GITHUB_CLIENT_ID"]               = os.getenv("GITHUB_CLIENT_ID")
    app.config["GITHUB_CLIENT_SECRET"]           = os.getenv("GITHUB_CLIENT_SECRET")

    # -------------------------------------------------------------------------
    # Extensions
    # -------------------------------------------------------------------------
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "dashboard.signin"
    login_manager.login_message_category = "danger"

    # -------------------------------------------------------------------------
    # Blueprints
    # -------------------------------------------------------------------------
    from blueprints.dashboard.routes import dashboard_bp
    app.register_blueprint(dashboard_bp)

    # -------------------------------------------------------------------------
    # DB init
    # -------------------------------------------------------------------------
    with app.app_context():
        db.create_all()

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)