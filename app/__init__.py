from flask import Flask
from flask_migrate import Migrate
from app.extensions import db, login_manager
from app.routes import register_routes

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    Migrate(app, db)  # Enable Flask-Migrate for Alembic migrations

    # Set the login view for @login_required redirects
    login_manager.login_view = 'auth.login'

    # Register all route blueprints
    register_routes(app)

    return app
