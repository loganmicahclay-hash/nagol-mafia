from flask import Blueprint, render_template, redirect, url_for, session, request, flash
import random

from database import db
from datetime import datetime, timedelta
from models.room import Room
from models.player import Player


rooms = Blueprint("rooms", __name__)


def remove_player(player):

    room = Room.query.get(player.room_id)

    if not room:
        db.session.delete(player)
        return

    # Find all other players before removing this one
    other_players = Player.query.filter(
        Player.room_id == room.id,
        Player.id != player.id
    ).order_by(Player.id).all()

    # If the leaving player is the host, pass the crown
    if room.host_id == player.id and other_players:
        room.host_id = other_players[0].id

    # Remove the player
    db.session.delete(player)

    # If nobody else remains, remove the room
    if not other_players:
        db.session.delete(room)


def remove_disconnected_players(room):

    timeout = datetime.utcnow() - timedelta(seconds=10)

    disconnected_players = Player.query.filter(
        Player.room_id == room.id,
        Player.last_seen < timeout
    ).all()

    for player in disconnected_players:
        remove_player(player)

    db.session.commit()


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
        player = db.session.get(Player, player_id)

        if player:
            remove_player(player)
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
        return ""

    room = Room.query.filter_by(room_code=room_code).first()

    if not room:
        return ""

    remove_disconnected_players(room)

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

    remove_disconnected_players(room)

    return render_template(
        "partials/game_settings.html",
        room=room
    )


@rooms.route("/room/heartbeat", methods=["POST"])
def heartbeat():

    player_id = session.get("player_id")

    if not player_id:
        return "", 204

    player = Player.query.get(player_id)

    if not player:
        return "", 204

    player.last_seen = datetime.utcnow()

    db.session.commit()

    return "", 204