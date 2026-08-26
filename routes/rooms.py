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

    # Make the creator the host
    new_room.host_id = new_player.id
    db.session.commit()

    # Store player information in the session
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
            room = Room.query.get(room_id)

            if room:
                # Check if the player leaving is the host
                if room.host_id == player.id:

                    # Find the other players in the room
                    other_players = Player.query.filter(
                        Player.room_id == room_id,
                        Player.id != player.id
                    ).all()

                    if other_players:
                        # Give the host position to another player
                        new_host = other_players[0]
                        room.host_id = new_host.id

                    else:
                        # No players remain, so delete the room
                        db.session.delete(room)

                # Delete the player who is leaving
                db.session.delete(player)

                db.session.commit()

    # Clear this player's session
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


@rooms.route("/room/players")
def player_list():

    room_code = session.get("room_code")

    if not room_code:
        return "", 204

    room = Room.query.filter_by(room_code=room_code).first()

    if not room:
        return "", 204

    return render_template(
        "partials/player_list.html",
        room=room
    )


@rooms.route("/room/game-settings")
def game_settings():

    room_code = session.get("room_code")

    if not room_code:
        return "", 204

    room = Room.query.filter_by(room_code=room_code).first()

    if not room:
        return "", 204

    return render_template(
        "partials/game_settings.html",
        room=room
    )