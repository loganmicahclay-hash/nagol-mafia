
from flask import Flask

from database import db
from routes.main import main
from routes.rooms import rooms

# Import models so SQLAlchemy registers their tables.
from models.room import Room
from models.player import Player
from models.vote import Vote


def create_app(test_config=None):
    app = Flask(__name__)

    app.config["SECRET_KEY"] = "your-secret-key"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///Mafia.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Apply test or other custom configuration BEFORE initializing SQLAlchemy.
    if test_config is not None:
        app.config.update(test_config)

    db.init_app(app)

    app.register_blueprint(main)
    app.register_blueprint(rooms)

    return app


app = create_app()


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run()
