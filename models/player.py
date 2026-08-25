from database import db


class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)

    room_id = db.Column(
        db.Integer,
        db.ForeignKey("room.id"),
        nullable=False
    )

    def __repr__(self):
        return f"<Player {self.username}>"