from . import db, login_manager
from flask_login import UserMixin
from datetime import datetime

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    projects_created = db.relationship('Project', backref='creator', lazy=True, cascade="all, delete-orphan")  # Projects created by the user
    projects_shared = db.relationship('ProjectParticipant', back_populates='user', cascade="all, delete-orphan")

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    expenses = db.relationship('Expense', backref='project', lazy=True, cascade="all, delete-orphan")
    participants = db.relationship('ProjectParticipant', back_populates='project', cascade="all, delete-orphan")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"Project('{self.name}')"

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref=db.backref('expenses', lazy=True)) #add user relationship

    def __repr__(self):
        return f"Expense('{self.description}', '{self.amount}')"

class ProjectParticipant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    project = db.relationship('Project', back_populates='participants')
    user = db.relationship('User', back_populates='projects_shared')

    __table_args__ = (
        db.UniqueConstraint('project_id', 'user_id', name='_project_user_uc'),
    )
    def __repr__(self):
        return f"ProjectParticipant(project_id={self.project_id}, user_id={self.user_id})"