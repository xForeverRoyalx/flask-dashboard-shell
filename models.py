from datetime import datetime
from flask_login import UserMixin
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from extensions import db, login_manager


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id               = db.Column(db.Integer, primary_key=True)
    first_name       = db.Column(db.String(64), nullable=False, default="")
    last_name        = db.Column(db.String(64), nullable=False, default="")
    email            = db.Column(db.String(120), unique=True, nullable=False)
    password_hash    = db.Column(db.String(256), nullable=True)
    avatar_url       = db.Column(db.String(512), nullable=True)
    email_confirmed  = db.Column(db.Boolean, default=False)
    profile_complete = db.Column(db.Boolean, default=False)
    avatar_uploaded  = db.Column(db.Boolean, default=False)

    google_id        = db.Column(db.String(128), unique=True, nullable=True)
    github_id        = db.Column(db.String(128), unique=True, nullable=True)

    created_at       = db.Column(db.DateTime, default=datetime.utcnow)
    last_login       = db.Column(db.DateTime, nullable=True)

    def set_password(self, password):
        ph = PasswordHasher()
        self.password_hash = ph.hash(password)

    def check_password(self, password):
        ph = PasswordHasher()
        try:
            return ph.verify(self.password_hash, password)
        except VerifyMismatchError:
            return False

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def __repr__(self):
        return f"<User {self.email}>"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))