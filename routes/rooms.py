from flask import Blueprint, render_template, redirect, url_for, session
import random

from database import db
from models.room import Room


rooms = Blueprint("rooms", __name__)


@rooms.route("/create-room")
def create_room():

    # If the player already has a room, show that room instead
    if "room_code" in session:
        room_code = session["room_code"]
        return render_template("create_room.html", room_code=room_code)

    # Keep generating codes until we find one that isn't being used
    while True:
        room_code = str(random.randint(1000, 9999))

        existing_room = Room.query.filter_by(room_code=room_code).first()

        if existing_room is None:
            break

    # Create and save the new room
    new_room = Room(room_code=room_code)

    db.session.add(new_room)
    db.session.commit()

    # Remember which room this player created
    session["room_code"] = room_code

    return render_template("create_room.html", room_code=room_code)


@rooms.route("/exit-room")
def exit_room():
    session.pop("room_code", None)

    return redirect(url_for("main.home"))