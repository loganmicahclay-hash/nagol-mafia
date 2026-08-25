from database import db


class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_code = db.Column(db.String(4), unique=True, nullable=False)

    players = db.relationship(
        "Player",
        backref="room",
        lazy=True,
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Room {self.room_code}>"