import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FloatField, TextAreaField, SelectMultipleField
from wtforms.validators import DataRequired, Length, Email, EqualTo, NumberRange
from collections import defaultdict

load_dotenv()  # Load environment variables from.env

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')  or 'zkTeAR8wnzkTeAR8wnn9CjtkZsnjvn9CjtkZsnjv'
password = os.getenv('MYSQL_PASSWORD')
#app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://tobiasvonarx:{password}@tobiasvonarx.mysql.pythonanywhere-services.com/tobiasvonarx$expenses'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://tobiasvonarx:zkTeAR8wnn9CjtkZsnjv@tobiasvonarx.mysql.pythonanywhere-services.com/tobiasvonarx$expenses'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return str(self.id)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    participants = db.relationship('User', secondary='project_participants', backref='projects', lazy=True)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200))
    paid_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    # Relationship to get user object
    paid_by = db.relationship('User', backref='expenses_paid')


project_participants = db.Table(
    'project_participants',
    db.Column('project_id', db.Integer, db.ForeignKey('project.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

# Forms

class ShareProjectForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    submit = SubmitField("Share Project")

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')

class ProjectForm(FlaskForm):
    name = StringField('Project Name', validators=[DataRequired()])
    submit = SubmitField('Create')

class ExpenseForm(FlaskForm):
    amount = FloatField('Amount', validators=[DataRequired(), NumberRange(min=0)])
    description = TextAreaField('Description')
    project = SelectMultipleField('Project', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Add Expense')

# User loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()

# Routes
@app.route('/')
@login_required
def index():
    projects = current_user.projects  # Or use another query if needed
    return render_template('projects.html', projects=projects)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(username=form.username.data).first()
        if existing_user:
            flash('Username already exists. Please choose a different one.', 'danger')
            return redirect(url_for('register'))
        existing_email = User.query.filter_by(email=form.email.data).first()
        if existing_email:
            flash('Email already exists. Please use a different one.', 'danger')
            return redirect(url_for('register'))

        new_user = User(username=form.username.data, email=form.email.data)
        new_user.set_password(form.password.data)
        db.session.add(new_user)
        db.session.commit()
        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)  # Use login_user() to log in the user
            flash('Login successful!', 'success')  # Optional: Display a success message
            return redirect(url_for('index'))  # Redirect to the index page
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/create_project', methods=['GET', 'POST'])
@login_required
def create_project():
    form = ProjectForm()
    if form.validate_on_submit():
        new_project = Project(name=form.name.data, creator_id=current_user.id)
        new_project.participants.append(current_user)  # Add this line
        db.session.add(new_project)
        db.session.commit()
        flash('Project created!', 'success')
        return redirect(url_for('index'))
    return render_template('create_project.html', form=form)

@app.route('/add_expense', methods=['GET', 'POST'])
@login_required
def add_expense():
    form = ExpenseForm()
    projects = Project.query.filter(Project.participants.any(id=current_user.id)).all()
    form.project.choices = [(project.id, project.name) for project in projects]
    if form.validate_on_submit():
        new_expense = Expense(
            amount=form.amount.data,
            description=form.description.data,
            project_id=form.project.data,
            paid_by_id=current_user.id
        )
        db.session.add(new_expense)
        db.session.commit()
        flash('Expense added!', 'success')
        return redirect(url_for('view_expenses', project_id=new_expense.project_id))
    return render_template('add_expense.html', form=form)

@app.route('/view_expenses/<int:project_id>')
@login_required
def view_expenses(project_id):
    project = Project.query.get_or_404(project_id)
    if current_user not in project.participants:
        flash('You do not have permission to view these expenses.', 'danger')
        return redirect(url_for('index'))

    expenses = Expense.query.filter_by(project_id=project_id).all()
    return render_template('view_expenses.html', project=project, expenses=expenses)

@app.route('/project/<int:project_id>/settle', methods=['POST'])
@login_required
def settle_payment(project_id):
    project = Project.query.get_or_404(project_id)

    # Ensure user is part of the project
    if current_user not in project.participants and current_user.id != project.creator_id:
        flash("You don't have access to this project.", "danger")
        return redirect(url_for('project_expenses', project_id=project_id))

    # Get form data
    payer_id = int(request.form.get('payer_id'))
    receiver_id = int(request.form.get('receiver_id'))
    amount = float(request.form.get('amount'))

    if amount <= 0:
        flash("Invalid amount", "danger")
        return redirect(url_for('project_expenses', project_id=project_id))

    # Get all the expenses for the project
    expenses = Expense.query.filter_by(project_id=project_id).all()

    # Calculate total spent by each user
    total_spent = defaultdict(float)
    for expense in expenses:
        total_spent[expense.paid_by_id] += expense.amount

    # Calculate the split amount (how much each participant should have paid)
    split_amount = sum(total_spent.values()) / len(project.participants)

    # Calculate balances (how much each user is owed or owes)
    balances = {user.id: total_spent[user.id] - split_amount for user in project.participants}

    # Check if the transaction is valid (payer should owe money and receiver should be owed money)
    if balances[payer_id] >= 0 or balances[receiver_id] <= 0:
        flash("Invalid transaction", "danger")
        return redirect(url_for('project_expenses', project_id=project_id))

    # Adjust the balances for the transaction
    balances[payer_id] += amount
    balances[receiver_id] -= amount

    # Save changes to the database (if needed) or do further actions based on your application logic

    flash(f"Payment of ${amount:.2f} settled from {User.query.get(payer_id).username} to {User.query.get(receiver_id).username}", "success")
    return redirect(url_for('project_expenses', project_id=project_id))

@app.route('/project/<int:project_id>/expenses')
@login_required
def project_expenses(project_id):
    project = Project.query.get_or_404(project_id)

    # Ensure the user is part of the project
    if current_user not in project.participants and current_user.id != project.creator_id:
        flash("You don't have permission to view this project!", "danger")
        return redirect(url_for('index'))

    # Get all expenses for this project
    expenses = Expense.query.filter_by(project_id=project_id).all()

    # Calculate total spending per user
    user_expenses = {}
    total_amount = sum(exp.amount for exp in expenses)

    for exp in expenses:
        user = User.query.get(exp.paid_by_id)
        if user.id not in user_expenses:
            user_expenses[user.id] = 0
        user_expenses[user.id] += exp.amount

    # Calculate equal split for all participants (including the creator)
    num_members = len(project.participants)  # Correct split among participants only
    split_amount = total_amount / num_members if num_members > 0 else 0

    # Calculate the balance (spent - split amount)
    user_balances = {user_id: amount - split_amount for user_id, amount in user_expenses.items()}

    # Get all users in the project to pass to the template
    users = {user.id: user for user in project.participants}

    return render_template(
        'project_expenses.html',
        project=project,
        expenses=expenses,
        user_expenses=user_expenses,
        user_balances=user_balances,
        split_amount=split_amount,
        users=users  # Pass users to the template
    )


@app.route('/share_project/<int:project_id>', methods=['GET', 'POST'])
@login_required
def share_project(project_id):
    project = Project.query.get_or_404(project_id)
    # Only the project creator (or someone with permission) can share the project
    if project.creator_id != current_user.id:
        flash("You are not authorized to share this project.", "danger")
        return redirect(url_for('index'))

    form = ShareProjectForm()
    if form.validate_on_submit():
        user_to_share = User.query.filter_by(username=form.username.data).first()
        if user_to_share:
            if user_to_share not in project.participants:
                project.participants.append(user_to_share)
                db.session.commit()
                flash(f"Project shared with {user_to_share.username} successfully!", "success")
            else:
                flash("This user is already a participant in the project.", "info")
        else:
            flash("User not found.", "danger")
        # Redirect back to the same page or elsewhere as needed.
        return redirect(url_for('share_project', project_id=project.id))
    return render_template('share_project.html', form=form, project=project)

@app.route('/join_project/<int:project_id>')
@login_required
def join_project(project_id):
    project = Project.query.get_or_404(project_id)
    if current_user in project.participants:
        flash("You are already a participant in this project.", "info")
    else:
        project.participants.append(current_user)
        db.session.commit()
        flash("You have successfully joined the project!", "success")
    return redirect(url_for('index'))

@app.route('/projects')
@login_required
def projects():
    user_projects = Project.query.filter(
        (Project.creator_id == current_user.id) |
        (Project.participants.any(id=current_user.id))
    ).all()
    return render_template('projects.html', projects=user_projects)



if __name__ == '__main__':
    app.run(debug=True)