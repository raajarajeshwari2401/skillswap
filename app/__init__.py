"""SkillSwap Application Factory.
Initializes Flask, database ORM, Flask-Login, CSRF, Socket.IO, blueprints, and filters.
"""

from flask import Flask, render_template
from config import config_by_name
from app.extensions import db, migrate, login_manager, socketio, csrf
from app.models.user import User


def create_app(config_name: str = "default") -> Flask:
    """Application factory for SkillSwap."""
    flask_app = Flask(__name__)
    flask_app.config.from_object(config_by_name[config_name])

    # Initialize extensions
    db.init_app(flask_app)
    migrate.init_app(flask_app, db)
    login_manager.init_app(flask_app)
    csrf.init_app(flask_app)
    
    # Initialize Socket.IO with proper async mode
    async_mode = flask_app.config.get("SOCKETIO_ASYNC_MODE", "threading")
    socketio.init_app(flask_app, cors_allowed_origins="*", async_mode=async_mode)

    # Flask-Login user loader
    @login_manager.user_loader
    def load_user(user_id: str):
        return User.query.get(int(user_id))

    # Context processors to supply global variables to all Jinja2 templates
    @flask_app.context_processor
    def inject_global_data():
        from flask_login import current_user
        unread_count = 0
        if current_user.is_authenticated:
            try:
                unread_count = current_user.notifications.filter_by(is_read=False).count()
            except Exception:
                unread_count = 0
        return {
            "unread_notifications_count": unread_count,
            "app_name": "SkillSwap",
        }

    # Custom Jinja filters
    @flask_app.template_filter("badge_class")
    def badge_class_filter(status: str) -> str:
        mapping = {
            "pending": "badge-warning",
            "accepted": "badge-info",
            "scheduled": "badge-primary",
            "completed": "badge-success",
            "cancelled": "badge-danger",
            "rejected": "badge-secondary",
            "disputed": "badge-danger",
            "beginner": "badge-level-beginner",
            "intermediate": "badge-level-intermediate",
            "advanced": "badge-level-advanced",
        }
        return mapping.get(str(status).lower(), "badge-secondary")

    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.skills import skills_bp
    from app.routes.exchanges import exchanges_bp
    from app.routes.matching import matching_bp
    from app.routes.wallet import wallet_bp
    from app.routes.notifications import notifications_bp
    from app.routes.profile import profile_bp
    from app.routes.reviews import reviews_bp
    from app.routes.admin import admin_bp

    flask_app.register_blueprint(main_bp)
    flask_app.register_blueprint(auth_bp)
    flask_app.register_blueprint(skills_bp)
    flask_app.register_blueprint(exchanges_bp)
    flask_app.register_blueprint(matching_bp)
    flask_app.register_blueprint(wallet_bp)
    flask_app.register_blueprint(notifications_bp)
    flask_app.register_blueprint(profile_bp)
    flask_app.register_blueprint(reviews_bp)
    flask_app.register_blueprint(admin_bp)

        # Register Socket.IO event listeners
    from app.sockets import events  # noqa

    # Initialize database tables
    with flask_app.app_context():
        db.create_all()

    # Error pages
    @flask_app.errorhandler(404)
    def not_found_error(error):
        return render_template("errors/404.html"), 404

    @flask_app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template("errors/500.html"), 500

    @flask_app.errorhandler(403)
    def forbidden_error(error):
        return render_template("errors/404.html", message="403 Forbidden: Access denied."), 403

    return flask_app
