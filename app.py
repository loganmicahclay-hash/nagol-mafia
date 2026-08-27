from flask import Flask
import os

from database import db
from routes.main import main
from routes.rooms import rooms

from models.room import Room
from models.player import Player
from models.vote import Vote


app = Flask(__name__)

app.secret_key = "your-secret-key"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///Mafia.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)


with app.app_context():

    db_path = os.path.join(
        app.instance_path,
        "Mafia.db"
    )

    if os.path.exists(db_path):
        os.remove(db_path)

    db.create_all()


app.register_blueprint(main)
app.register_blueprint(rooms)


if __name__ == "__main__":
    app.run()