from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from .config import Config

db = SQLAlchemy()

def create_app(config_object=None):
    app = Flask(__name__, static_folder=None)  # static served by nginx
    app.config.from_object(config_object or Config)

    db.init_app(app)

    # register API blueprint
    from .api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    # create DB tables if they don't exist (simple dev convenience)
    with app.app_context():
        db.create_all()

    return app
