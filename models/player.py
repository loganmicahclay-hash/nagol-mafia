from database import db
from datetime import datetime


class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)

    room_id = db.Column(
        db.Integer,
        db.ForeignKey("room.id"),
        nullable=False
    )

    last_seen = db.Column(
        db.DateTime, 
        default=datetime.utcnow
    )

    def __repr__(self):
        return f"<Player {self.username}>"