from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Initialize the SQLAlchemy database object
db = SQLAlchemy()
# Initialize the Flask-Login LoginManager
login_manager = LoginManager()

def create_app():
    """
    Create and configure the Flask application.

    This function initializes the Flask app, sets up the database connection,
    configures the login manager, registers blueprints, and creates the database
    tables (if they don't exist).
    """
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    password = os.getenv('MYSQL_PASSWORD')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://tobiasvonarx:{password}@tobiasvonarx.mysql.pythonanywhere-services.com/tobiasvonarx$expenses'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_POOL_RECYCLE'] = 280
    app.config['SQLALCHEMY_POOL_TIMEOUT'] = 10
    app.config['SQLALCHEMY_POOL_PRE_PING'] = True
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'  # Redirect to login page if not authenticated

    from .routes import main_bp
    app.register_blueprint(main_bp)

    with app.app_context():
        db.create_all()  # Create tables if they don't exist

    return app