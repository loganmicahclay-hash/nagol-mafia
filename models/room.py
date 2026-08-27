from database import db


class Room(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    room_code = db.Column(
        db.String(4),
        unique=True,
        nullable=False
    )

    # The player who created the room
    host_id = db.Column(
        db.Integer,
        db.ForeignKey("player.id"),
        nullable=True
    )

    # All players currently in the room
    players = db.relationship(
        "Player",
        foreign_keys="Player.room_id",
        backref="room",
        lazy=True,
        cascade="all, delete-orphan"
    )

    # The host of the room
    host = db.relationship(
        "Player",
        foreign_keys=[host_id],
        post_update=True
    )

    # -------------------------
    # GAME INFORMATION
    # -------------------------

    game_started = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

    game_mode = db.Column(
        db.String(20),
        default="elimination",
        nullable=False
    )

    round_number = db.Column(
        db.Integer,
        default=1,
        nullable=False
    )

    round_result = db.Column(
        db.String(100),
        nullable=True
    )

    result_shown = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

    game_over = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

    winner = db.Column(
        db.String(20),
        nullable=True
    )

    game_cancelled = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

    game_cancel_reason = db.Column(
       db.String(200),
        nullable=True
    )

    def __repr__(self):
        return f"<Room {self.room_code}>"