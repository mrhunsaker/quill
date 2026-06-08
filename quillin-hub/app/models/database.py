from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# This is usually initialized in __init__.py using db.init_app(app)
# but we import the db instance to define models.
from .. import db

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    role = db.Column(db.String(20), default='User') # Admin, Author, User
    reputation_score = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Plugin(db.Model):
    __tablename__ = 'plugins'
    id = db.Column(db.Integer, primary_key=True)
    manifest_id = db.Column(db.String(128), unique=True, nullable=False)
    version = db.Column(db.String(32), nullable=False)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    download_url = db.Column(db.String(512))
    status = db.Column(db.String(20), default='Pending') # Pending, Verified, Rejected
    is_gold_standard = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Submission(db.Model):
    __tablename__ = 'submissions'
    id = db.Column(db.Integer, primary_key=True)
    plugin_id = db.Column(db.Integer, db.ForeignKey('plugins.id'))
    submitter_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    lint_report = db.Column(db.JSON)
    review_notes = db.Column(db.Text)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

class Interaction(db.Model):
    __tablename__ = 'interactions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    plugin_id = db.Column(db.Integer, db.ForeignKey('plugins.id'))
    type = db.Column(db.String(20)) # Upvote, Downvote, Comment
    content = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
