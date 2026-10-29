"""WSGI production entry point for SkillSwap.
Used by Gunicorn, Eventlet, Render, Heroku, or AWS Elastic Beanstalk.
"""

import os
from app import create_app
from app.extensions import db

env = os.environ.get("FLASK_ENV", "production")
app = create_app(env)

# Ensure database tables exist upon cold-start in production
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    from app.extensions import socketio
    socketio.run(app)
