from flask import Blueprint, render_template, redirect, url_for, session, request, flash
import random

from database import db
from models.room import Room
from models.player import Player


rooms = Blueprint("rooms", __name__)


@rooms.route("/create-room")
def create_room():
    if "room_code" in session:
        return redirect(url_for("rooms.room"))

    # Generate a unique room code
    while True:
        room_code = str(random.randint(1000, 9999))

        existing_room = Room.query.filter_by(room_code=room_code).first()

        if existing_room is None:
            break

    # Create the room
    new_room = Room(room_code=room_code)

    db.session.add(new_room)
    db.session.commit()

    # Get the username
    username = session.get("username")

    # Create the player
    new_player = Player(
        username=username,
        room_id=new_room.id
    )

    db.session.add(new_player)
    db.session.commit()

    # Store the player's information in the session
    session["room_code"] = room_code
    session["player_id"] = new_player.id

    return redirect(url_for("rooms.room"))


@rooms.route("/exit-room")
def exit_room():
    player_id = session.get("player_id")

    if player_id:
        player = Player.query.get(player_id)

        if player:
            room_id = player.room_id

            # Remove the player
            db.session.delete(player)
            db.session.commit()

            # Check whether anyone is left
            remaining_players = Player.query.filter_by(
                room_id=room_id
            ).count()

            # Delete the room if nobody remains
            if remaining_players == 0:
                room = Room.query.get(room_id)

                if room:
                    db.session.delete(room)
                    db.session.commit()

    # Clear the player's room information
    session.pop("player_id", None)
    session.pop("room_code", None)

    return redirect(url_for("main.home"))


@rooms.route("/join-room", methods=["GET", "POST"])
def join_room():
    if request.method == "POST":
        room_code = request.form["room_code"]

        room = Room.query.filter_by(room_code=room_code).first()

        if room:
            username = session.get("username")

            # Create the player
            new_player = Player(
                username=username,
                room_id=room.id
            )

            db.session.add(new_player)
            db.session.commit()

            # Store the player's information
            session["room_code"] = room_code
            session["player_id"] = new_player.id

            return redirect(url_for("rooms.room"))

        flash("Room not found. Please check the code and try again.")

    return render_template("join_room.html")


@rooms.route("/room")
def room():
    room_code = session.get("room_code")

    if not room_code:
        return redirect(url_for("main.home"))

    room = Room.query.filter_by(room_code=room_code).first()

    if not room:
        return redirect(url_for("main.home"))

    return render_template("room.html", room=room)