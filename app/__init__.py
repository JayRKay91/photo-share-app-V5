from flask import Flask
from app.extensions import db, login_manager
from app.routes import register_routes

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    db.init_app(app)
    login_manager.init_app(app)

    # Set login route for @login_required redirects
    login_manager.login_view = 'auth.login'

    register_routes(app)
    return app
