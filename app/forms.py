from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, FloatField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from .models import User

class RegistrationForm(FlaskForm):
    """
    Form for user registration.

    Includes fields for username, email, password, and password confirmation.
    Validates that the username and email are not already taken.
    """
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken. Please choose a different one.')

class LoginForm(FlaskForm):
    """
    Form for user login.

    Includes fields for email, password, and a "remember me" option.
    """
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class ProjectForm(FlaskForm):
    """
    Form for creating a new project.

    Includes a field for the project name.
    """
    name = StringField('Project Name', validators=[DataRequired()])
    submit = SubmitField('Create Project')

class ExpenseForm(FlaskForm):
    """
    Form for adding a new expense.

    Includes fields for description and amount.
    """
    description = StringField('Description', validators=[DataRequired()])
    amount = FloatField('Amount', validators=[DataRequired()])
    submit = SubmitField('Add Expense')

class ShareProjectForm(FlaskForm):
    """
    Form for sharing a project with another user.

    Includes a field for the email of the user to share with.
    """
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Share Project')

class RemoveParticipantForm(FlaskForm):
    """
    Form for removing a participant from a project.

    Includes a select field to choose the user to remove.
    """
    user_id = SelectField('Select User to Remove', coerce=int, validators=[DataRequired()])  # Use SelectField
    submit = SubmitField('Remove Participant')

class SettleAllForm(FlaskForm):
    """
    Form for settling all expenses in a project.

    Includes a submit button.
    """
    submit = SubmitField('Settle All Payments')