from flask import Flask

from database import db
from models.room import Room
from routes.main import main
from routes.rooms import rooms

app = Flask(__name__)

app.secret_key = "your-secret-key"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///mafia.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SESSION_PERMANENT"] = False

db.init_app(app)

with app.app_context():
    db.create_all()

app.register_blueprint(main)
app.register_blueprint(rooms)


if __name__ == "__main__":
    app.run(debug=True)