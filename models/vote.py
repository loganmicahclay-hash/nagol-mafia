from database import db


class Vote(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    room_id = db.Column(
        db.Integer,
        db.ForeignKey("room.id"),
        nullable=False
    )

    voter_id = db.Column(
        db.Integer,
        db.ForeignKey("player.id"),
        nullable=False
    )

    target_id = db.Column(
        db.Integer,
        db.ForeignKey("player.id"),
        nullable=False
    )

    round_number = db.Column(
        db.Integer,
        nullable=False
    )

    def __repr__(self):
        return (
            f"<Vote "
            f"voter={self.voter_id} "
            f"target={self.target_id} "
            f"round={self.round_number}>"
        )