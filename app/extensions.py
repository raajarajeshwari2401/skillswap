"""Flask extensions initialization module.
Keeps extensions decoupled from the application factory to avoid circular imports.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_socketio import SocketIO
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
socketio = SocketIO()
csrf = CSRFProtect()

# Configure Flask-Login defaults
login_manager.login_view = "auth.login"
login_manager.login_message = "Please sign in to access this page."
login_manager.login_message_category = "info"
