from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from .forms import RegistrationForm, LoginForm, ProjectForm, ExpenseForm, ShareProjectForm, RemoveParticipantForm, SettlePaymentForm
from .models import db, User, Project, Expense, ProjectParticipant
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@login_required
def index():
    projects_created = current_user.projects_created
    projects_participating = [pp.project for pp in current_user.projects_shared]
    projects = projects_created + projects_participating
    return render_template('index.html', projects=projects)

@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256', salt_length=8) #Added salt and sha256
        new_user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('main.login'))
    return render_template('register.html', title='Register', form=form)

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.index'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)

@main_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@main_bp.route('/create_project', methods=['GET', 'POST'])
@login_required
def create_project():
    form = ProjectForm()
    if form.validate_on_submit():
        new_project = Project(name=form.name.data, creator=current_user)
        db.session.add(new_project)
        db.session.commit()
        flash('Project created successfully!', 'success')
        return redirect(url_for('main.index'))
    return render_template('create_project.html', form=form)

@main_bp.route('/api/projects')
def api_projects():
    """
    Returns a JSON list of projects the current user has access to.
    """
    projects = Project.query.all()

    project_list = []
    for project in projects:
        project_data = {
            'id': project.id,
            'name': project.name,
            'creator': project.creator.username,
            'created_at': project.created_at.isoformat(),
        }
        project_list.append(project_data)

    return jsonify(project_list)

@main_bp.route('/api/projects/<int:project_id>/expenses')
def api_project_expenses(project_id):
    """
    Returns a JSON list of expenses for a specific project.
    Requires authentication and access control.
    """
    project = Project.query.get_or_404(project_id)

    expense_list = []
    for expense in project.expenses:
        expense_data = {
            'id': expense.id,
            'description': expense.description,
            'amount': expense.amount,
            'user': expense.user.username,
            'created_at': expense.created_at.isoformat(),
        }
        expense_list.append(expense_data)

    return jsonify(expense_list)

@main_bp.route('/project/<int:project_id>', methods=['GET', 'POST'])
@login_required
def project(project_id):
    project = Project.query.get_or_404(project_id)

    # Check if the user has access to the project
    if current_user != project.creator and current_user not in [p.user for p in project.participants]:
        flash('You do not have access to this project.', 'danger')
        return redirect(url_for('main.index'))

    # Use prefixes for the forms!
    expense_form = ExpenseForm(prefix='expense')
    share_form = ShareProjectForm(prefix='share')
    remove_participant_form = RemoveParticipantForm(prefix='remove')
    settle_payment_form = SettlePaymentForm(prefix='settle')

    # Populate choices for the dropdowns
    participants = [project.creator] + [p.user for p in project.participants]
    participant_choices = [(user.id, user.username) for user in participants if user.id != project.creator.id]

    remove_participant_form.user_id.choices = participant_choices
    settle_payment_form.user_id.choices = [(user.id, user.username) for user in participants]


    if expense_form.is_submitted() and expense_form.validate():
        new_expense = Expense(description=expense_form.description.data,
                              amount=expense_form.amount.data,
                              user=current_user,
                              project=project)
        db.session.add(new_expense)
        db.session.commit()
        flash('Expense added successfully!', 'success')
        return redirect(url_for('main.project', project_id=project_id))

    if share_form.is_submitted() and share_form.validate():
        user_to_share = User.query.filter_by(email=share_form.email.data).first()
        if user_to_share:
            if user_to_share == project.creator:
                flash('Cannot share the project with the owner.', 'warning')
            elif any(participant_user_id == user_to_share.id for participant_user_id in [p.user_id for p in project.participants]):
                flash('This user is already a participant in this project.', 'warning')
            else:
                project_participant = ProjectParticipant(project_id=project.id, user_id=user_to_share.id)
                db.session.add(project_participant)
                db.session.commit()
                flash('Project shared successfully!', 'success')
        else:
            flash('User with this email does not exist.', 'danger')
        return redirect(url_for('main.project', project_id=project_id))

    if remove_participant_form.is_submitted() and remove_participant_form.validate():
        user_id_to_remove = int(remove_participant_form.user_id.data)
        if user_id_to_remove == project.creator_id:
            flash("You cannot remove the project creator.", "danger")
            return redirect(url_for('main.project', project_id=project_id))
        participant_to_remove = ProjectParticipant.query.filter_by(project_id=project_id, user_id=user_id_to_remove).first()
        if participant_to_remove:
            db.session.delete(participant_to_remove)
            db.session.commit()
            flash('Participant removed successfully!', 'success')
        else:
            flash('Participant not found.', 'danger')
        return redirect(url_for('main.project', project_id=project_id))

    if settle_payment_form.is_submitted() and settle_payment_form.validate():
        user_id_to_settle = int(settle_payment_form.user_id.data)
        expenses_to_settle = Expense.query.filter_by(project_id=project_id).all()
        for expense in expenses_to_settle:
            db.session.delete(expense)
        db.session.commit()
        flash('Expenses settled successfully!', 'success')
        return redirect(url_for('main.project', project_id=project_id))

    # --- Debt Calculation Logic ---
    total_spent = db.session.query(func.sum(Expense.amount)).filter(Expense.project_id == project_id).scalar() or 0
    expenses = Expense.query.filter_by(project_id=project_id).order_by(Expense.created_at.desc()).all()
    all_participants = [project.creator] + [p.user for p in project.participants]
    num_participants = len(all_participants)
    split_amount = total_spent / num_participants if num_participants > 0 else 0

    balances = {}
    for user in all_participants:
        user_spent = db.session.query(func.sum(Expense.amount)).filter(Expense.project_id == project_id, Expense.user_id == user.id).scalar() or 0
        balances[user.username] = split_amount - user_spent

    debts = []
    receivers = {user: balance for user, balance in balances.items() if balance < 0}
    payers = {user: balance for user, balance in balances.items() if balance > 0}

    for payer, pay_amount in payers.items():
        for receiver, receive_amount in receivers.items():
            if pay_amount <= 0:  # Optimization: Skip if payer has paid all debts
                break
            if receive_amount >= 0: # Optimization: Skip if receiver is fully paid
                continue

            amount_to_transfer = min(pay_amount, -receive_amount)
            debts.append({'payer': payer, 'receiver': receiver, 'amount': amount_to_transfer})
            pay_amount -= amount_to_transfer
            receivers[receiver] += amount_to_transfer  # Update the receiver's balance

    return render_template('project.html', project=project, expenses=expenses,
                           expense_form=expense_form, share_form=share_form,
                           total_spent=total_spent, split_amount=split_amount,
                           debts=debts, # Pass debts to the template
                           remove_participant_form=remove_participant_form,
                           settle_payment_form=settle_payment_form)