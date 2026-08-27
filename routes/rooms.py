from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    session,
    request,
    flash,
    make_response
)

import random

from database import db
from datetime import datetime, timedelta

from models.room import Room
from models.player import Player
from models.vote import Vote


rooms = Blueprint("rooms", __name__)


# --------------------------------------------------
# PLAYER / ROOM CLEANUP
# --------------------------------------------------

def remove_player(player):

    room = Room.query.get(player.room_id)

    if not room:
        db.session.delete(player)
        return

    # ----------------------------------
    # GAME IS CURRENTLY ACTIVE
    # ----------------------------------

    if room.game_started:

        room.game_cancelled = True

        room.game_cancel_reason = (
            f"{player.username} left the game."
        )

        # Stop the game
        room.game_started = False

        # Remove votes made by this player
        Vote.query.filter_by(
            voter_id=player.id
        ).delete()

        # Remove votes targeting this player
        Vote.query.filter_by(
            target_id=player.id
        ).delete()

        db.session.delete(player)

        return

    # ----------------------------------
    # NORMAL LOBBY EXIT
    # ----------------------------------

    other_players = Player.query.filter(
        Player.room_id == room.id,
        Player.id != player.id
    ).order_by(Player.id).all()

    # If the leaving player is the host,
    # pass the crown to the next player.
    if room.host_id == player.id and other_players:
        room.host_id = other_players[0].id

    # Remove the player
    db.session.delete(player)

    # If nobody else remains, delete the room
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


# --------------------------------------------------
# ROOM CREATION
# --------------------------------------------------

@rooms.route("/create-room")
def create_room():

    if "room_code" in session:
        return redirect(url_for("rooms.room"))

    # Generate a unique room code
    while True:

        room_code = str(
            random.randint(1000, 9999)
        )

        existing_room = Room.query.filter_by(
            room_code=room_code
        ).first()

        if existing_room is None:
            break

    # Create the room
    new_room = Room(
        room_code=room_code
    )

    db.session.add(new_room)
    db.session.commit()

    # Get the username
    username = session.get("username")

    if not username:
        return redirect(
            url_for("main.home")
        )

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

    return redirect(
        url_for("rooms.room")
    )


# --------------------------------------------------
# EXIT ROOM
# --------------------------------------------------

@rooms.route("/exit-room")
def exit_room():

    player_id = session.get("player_id")
    message = None

    if player_id:

        player = db.session.get(
            Player,
            player_id
        )

        if player:

            room = Room.query.get(
                player.room_id
            )

            # Save the cancellation message if
            # someone leaves an active game.
            if room and room.game_started:
                message = f"{player.username} left the game."

            remove_player(player)
            db.session.commit()

    # Clear this player's room information
    session.pop("player_id", None)
    session.pop("room_code", None)

    if message:
        return redirect(
            url_for(
                "main.home",
                message=message
            )
        )

    return redirect(
        url_for("main.home")
    )


# --------------------------------------------------
# JOIN ROOM
# --------------------------------------------------

@rooms.route("/join-room", methods=["GET", "POST"])
def join_room():

    if request.method == "POST":

        room_code = request.form["room_code"]

        room = Room.query.filter_by(
            room_code=room_code
        ).first()

        # Room must exist, have players,
        # and not be cancelled.
        if (
            room
            and len(room.players) > 0
            and not room.game_cancelled
        ):

            # Don't allow players to join a game
            # that has already started.
            if room.game_started:

                flash(
                    "That game has already started."
                )

                return render_template(
                    "join_room.html"
                )

            username = session.get("username")

            if not username:
                return redirect(
                    url_for("main.home")
                )

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

            return redirect(
                url_for("rooms.room")
            )

        flash(
            "Room not found or is no longer active. "
            "Please check the code and try again."
        )

    return render_template(
        "join_room.html"
    )


# --------------------------------------------------
# ROOM / LOBBY
# --------------------------------------------------

@rooms.route("/room")
def room():

    room_code = session.get("room_code")

    if not room_code:
        return redirect(
            url_for("main.home")
        )

    room = Room.query.filter_by(
        room_code=room_code
    ).first()

    if not room:

        session.pop("room_code", None)
        session.pop("player_id", None)

        return redirect(
            url_for("main.home")
        )

    # If game already started,
    # send the player to the game.
    if room.game_started:

        return redirect(
            url_for("rooms.game")
        )

    # If the game was cancelled,
    # return to home with the reason.
    if room.game_cancelled:

        message = room.game_cancel_reason

        session.pop("room_code", None)
        session.pop("player_id", None)

        return redirect(
            url_for(
                "main.home",
                message=message
            )
        )

    return render_template(
        "room.html",
        room=room
    )


# --------------------------------------------------
# LIVE PLAYER LIST
# --------------------------------------------------

@rooms.route("/room/players")
def player_list():

    room_code = session.get("room_code")

    if not room_code:
        return "", 204

    room = Room.query.filter_by(
        room_code=room_code
    ).first()

    if not room:
        return "", 204

    # Remove disconnected players
    remove_disconnected_players(room)

    # Room may have been deleted during cleanup
    room = Room.query.filter_by(
        room_code=room_code
    ).first()

    if not room:
        return "", 204

    return render_template(
        "partials/player_list.html",
        room=room
    )


# --------------------------------------------------
# LIVE GAME SETTINGS
# --------------------------------------------------

@rooms.route("/room/game-settings")
def game_settings():

    room_code = session.get("room_code")

    if not room_code:
        return "", 204

    room = Room.query.filter_by(
        room_code=room_code
    ).first()

    if not room:
        return "", 204

    return render_template(
        "partials/game_settings.html",
        room=room
    )


# --------------------------------------------------
# HEARTBEAT
# --------------------------------------------------

@rooms.route("/room/heartbeat", methods=["POST"])
def heartbeat():

    player_id = session.get("player_id")

    if not player_id:
        return "", 204

    player = db.session.get(
        Player,
        player_id
    )

    if not player:
        return "", 204

    player.last_seen = datetime.utcnow()

    db.session.commit()

    return "", 204


# --------------------------------------------------
# START GAME
# --------------------------------------------------

@rooms.route("/start-game", methods=["POST"])
def start_game():

    player_id = session.get("player_id")

    if not player_id:
        return redirect(
            url_for("main.home")
        )

    player = db.session.get(
        Player,
        player_id
    )

    if not player:
        return redirect(
            url_for("main.home")
        )

    room = db.session.get(
        Room,
        player.room_id
    )

    if not room:
        return redirect(
            url_for("main.home")
        )

    # Don't start an already-started game
    if room.game_started:
        return redirect(
            url_for("rooms.game")
        )

    # Make sure only the host can start
    if room.host_id != player.id:
        return redirect(
            url_for("rooms.room")
        )

    # Get current players
    players = Player.query.filter_by(
        room_id=room.id
    ).all()

    # Minimum player requirement
    if len(players) < 4:

        flash(
            "You need at least 4 players "
            "to start the game."
        )

        return redirect(
            url_for("rooms.room")
        )

    # Get Mafia count
    try:

        mafia_count = int(
            request.form.get(
                "mafia_count",
                1
            )
        )

    except ValueError:

        mafia_count = 1

    # Get game mode
    game_mode = request.form.get(
        "game_mode",
        "elimination"
    )

    # Validate game mode
    if game_mode not in [
        "elimination",
        "one_shot"
    ]:

        game_mode = "elimination"

    # Calculate valid maximum Mafia count
    max_mafia = (
        len(players) - 1
    ) // 2

    if (
        mafia_count < 1
        or mafia_count > max_mafia
    ):

        flash(
            "Invalid number of Mafia players."
        )

        return redirect(
            url_for("rooms.room")
        )

    # Randomly select Mafia
    mafia_players = random.sample(
        players,
        mafia_count
    )

    # Assign roles
    for game_player in players:

        if game_player in mafia_players:
            game_player.role = "mafia"
        else:
            game_player.role = "villager"

        game_player.is_alive = True
        game_player.last_seen = datetime.utcnow()

    # Reset game information
    room.round_number = 1
    room.game_mode = game_mode
    room.game_started = True
    room.round_result = None
    room.result_shown = False
    room.game_over = False
    room.winner = None
    room.game_cancelled = False
    room.game_cancel_reason = None

    db.session.commit()

    return redirect(
        url_for("rooms.game")
    )


# --------------------------------------------------
# GAME PAGE
# --------------------------------------------------

@rooms.route("/game")
def game():

    player_id = session.get("player_id")

    if not player_id:
        return redirect(
            url_for("main.home")
        )

    player = db.session.get(
        Player,
        player_id
    )

    if not player:
        return redirect(
            url_for("main.home")
        )

    room = db.session.get(
        Room,
        player.room_id
    )

    if not room:
        return redirect(
            url_for("main.home")
        )

    # If the game was cancelled
    if room.game_cancelled:

        message = room.game_cancel_reason

        db.session.delete(player)
        db.session.commit()

        session.pop("room_code", None)
        session.pop("player_id", None)

        return redirect(
            url_for(
                "main.home",
                message=message
            )
        )

    # Don't allow access before game starts
    if not room.game_started:
        return redirect(
            url_for("rooms.room")
        )

    living_players = Player.query.filter_by(
        room_id=room.id,
        is_alive=True
    ).count()

    votes_submitted = Vote.query.filter_by(
        room_id=room.id,
        round_number=room.round_number
    ).count()

    has_voted = Vote.query.filter_by(
        voter_id=player.id,
        room_id=room.id,
        round_number=room.round_number
    ).first() is not None

    return render_template(
        "game.html",
        room=room,
        player=player,
        living_players=living_players,
        votes_submitted=votes_submitted,
        has_voted=has_voted
    )


# --------------------------------------------------
# GAME STATUS
# --------------------------------------------------

@rooms.route("/room/game-status")
def game_status():

    player_id = session.get("player_id")

    if not player_id:
        return "", 204

    player = db.session.get(
        Player,
        player_id
    )

    if not player:
        return "", 204

    room = db.session.get(
        Room,
        player.room_id
    )

    if not room:
        return "", 204

    if room.game_started:

        response = make_response("")

        response.headers["HX-Redirect"] = (
            url_for("rooms.game")
        )

        return response

    return "", 204


# --------------------------------------------------
# SUBMIT VOTE
# --------------------------------------------------

@rooms.route("/submit-vote", methods=["POST"])
def submit_vote():

    player_id = session.get("player_id")

    if not player_id:
        return redirect(
            url_for("main.home")
        )

    player = db.session.get(
        Player,
        player_id
    )

    if not player:
        return redirect(
            url_for("main.home")
        )

    room = db.session.get(
        Player,
        player.id
    ).room

    if not room:
        return redirect(
            url_for("main.home")
        )

    # Game must have started
    if not room.game_started:
        return redirect(
            url_for("rooms.room")
        )

    # Don't allow voting after cancellation
    if room.game_cancelled:

        return redirect(
            url_for(
                "main.home",
                message=room.game_cancel_reason
            )
        )

    # Player must be alive
    if not player.is_alive:
        return redirect(
            url_for("rooms.game")
        )

    # Get selected target
    target_id = request.form.get(
        "target_id"
    )

    if not target_id:
        return redirect(
            url_for("rooms.game")
        )

    try:

        target_id = int(target_id)

    except ValueError:

        return redirect(
            url_for("rooms.game")
        )

    target = db.session.get(
        Player,
        target_id
    )

    # Target must exist and be in same room
    if (
        not target
        or target.room_id != room.id
    ):

        return redirect(
            url_for("rooms.game")
        )

    # Can't vote for yourself
    if target.id == player.id:

        return redirect(
            url_for("rooms.game")
        )

    # Can't vote for dead players
    if not target.is_alive:

        return redirect(
            url_for("rooms.game")
        )

    # Prevent duplicate votes
    existing_vote = Vote.query.filter_by(
        voter_id=player.id,
        room_id=room.id,
        round_number=room.round_number
    ).first()

    if existing_vote:

        return redirect(
            url_for("rooms.game")
        )

    # Create vote
    new_vote = Vote(
        room_id=room.id,
        voter_id=player.id,
        target_id=target.id,
        round_number=room.round_number
    )

    db.session.add(new_vote)
    db.session.commit()

    resolve_votes(room)

    return redirect(
        url_for("rooms.game")
    )


# --------------------------------------------------
# VOTING STATUS
# --------------------------------------------------

def get_voting_status(room, player):

    living_players = Player.query.filter_by(
        room_id=room.id,
        is_alive=True
    ).all()

    votes_submitted = Vote.query.filter_by(
        room_id=room.id,
        round_number=room.round_number
    ).count()

    has_voted = Vote.query.filter_by(
        voter_id=player.id,
        room_id=room.id,
        round_number=room.round_number
    ).first() is not None

    return (
        living_players,
        votes_submitted,
        has_voted
    )


@rooms.route("/game/vote-status")
def vote_status():

    player_id = session.get("player_id")

    if not player_id:
        return "", 204

    player = db.session.get(
        Player,
        player_id
    )

    if not player:
        return "", 204

    room = db.session.get(
        Player,
        player.id
    ).room

    if not room:
        return "", 204

    # Check if game was cancelled
    if room.game_cancelled:

        message = room.game_cancel_reason

        response = make_response("")

        response.headers["HX-Redirect"] = url_for(
            "main.home",
            message=message
        )

        return response

    # Remove disconnected players
    remove_disconnected_players(room)

    # Reload player after cleanup
    player = db.session.get(
        Player,
        player_id
    )

    if not player:
        return "", 204

    # Reload room after cleanup
    room = Room.query.get(
        player.room_id
    )

    if not room:
        return "", 204

    # Check again after cleanup
    if room.game_cancelled:

        message = room.game_cancel_reason

        response = make_response("")

        response.headers["HX-Redirect"] = url_for(
            "main.home",
            message=message
        )

        return response

    if not room.game_started:
        return "", 204

    living_players = Player.query.filter_by(
        room_id=room.id,
        is_alive=True
    ).count()

    votes_submitted = Vote.query.filter_by(
        room_id=room.id,
        round_number=room.round_number
    ).count()

    return render_template(
        "partials/vote_status.html",
        living_players=living_players,
        votes_submitted=votes_submitted
    )


# --------------------------------------------------
# GAME COUNTS
# --------------------------------------------------

def get_game_counts(room):

    living_players = Player.query.filter_by(
        room_id=room.id,
        is_alive=True
    ).all()

    mafia_count = sum(
        1
        for player in living_players
        if player.role == "mafia"
    )

    villager_count = sum(
        1
        for player in living_players
        if player.role == "villager"
    )

    return (
        living_players,
        mafia_count,
        villager_count
    )


# --------------------------------------------------
# WIN CONDITION
# --------------------------------------------------

def check_win_condition(room):

    living_players, mafia_count, villager_count = (
        get_game_counts(room)
    )

    # No Mafia remain
    if mafia_count == 0:
        return "villagers"

    # One-Shot Mode
    if room.game_mode == "one_shot":
        return "mafia"

    # Elimination Mode
    if mafia_count >= villager_count:
        return "mafia"

    # No winner yet
    return None


# --------------------------------------------------
# RESOLVE VOTES
# --------------------------------------------------

def resolve_votes(room):

    living_players, mafia_count, villager_count = (
        get_game_counts(room)
    )

    votes = Vote.query.filter_by(
        room_id=room.id,
        round_number=room.round_number
    ).all()

    # Don't resolve until everyone has voted
    if len(votes) < len(living_players):
        return False

    # Count votes
    vote_counts = {}

    for vote in votes:

        vote_counts[vote.target_id] = (
            vote_counts.get(
                vote.target_id,
                0
            ) + 1
        )

    if not vote_counts:
        return False

    highest_votes = max(
        vote_counts.values()
    )

    leaders = [
        player_id
        for player_id, count
        in vote_counts.items()
        if count == highest_votes
    ]

    # ----------------------------------
    # TIE
    # ----------------------------------

    if len(leaders) > 1:

        if room.game_mode == "one_shot":

            room.round_result = (
                "The vote was tied. "
                "The Mafia wins!"
            )

            room.game_over = True
            room.winner = "mafia"

        else:

            room.round_result = (
                "The vote was tied. "
                "Nobody was eliminated."
            )

        room.result_shown = True

        db.session.commit()

        return True

    # ----------------------------------
    # ELIMINATE PLAYER
    # ----------------------------------

    eliminated_player = db.session.get(
        Player,
        leaders[0]
    )

    if not eliminated_player:
        return False

    eliminated_player.is_alive = False

    role_name = (
        "Mafia"
        if eliminated_player.role == "mafia"
        else "Villager"
    )

    # ----------------------------------
    # ONE-SHOT MODE
    # ----------------------------------

    if room.game_mode == "one_shot":

        if eliminated_player.role == "mafia":

            remaining_mafia = Player.query.filter_by(
                room_id=room.id,
                role="mafia",
                is_alive=True
            ).count()

            if remaining_mafia == 0:

                room.round_result = (
                    f"{eliminated_player.username} "
                    f"was eliminated. They were Mafia. "
                    f"Villagers win!"
                )

                room.winner = "villagers"

            else:

                room.round_result = (
                    f"{eliminated_player.username} "
                    f"was eliminated. They were Mafia, "
                    f"but other Mafia remain. "
                    f"Mafia wins!"
                )

                room.winner = "mafia"

        else:

            room.round_result = (
                f"{eliminated_player.username} "
                f"was eliminated. They were a Villager. "
                f"Mafia wins!"
            )

            room.winner = "mafia"

        room.game_over = True
        room.result_shown = True

        db.session.commit()

        return True

    # ----------------------------------
    # ELIMINATION MODE
    # ----------------------------------

    room.round_result = (
        f"{eliminated_player.username} "
        f"was eliminated. They were a {role_name}."
    )

    winner = check_win_condition(room)

    if winner == "villagers":

        room.round_result += " Villagers win!"

        room.game_over = True
        room.winner = "villagers"

    elif winner == "mafia":

        room.round_result += " Mafia wins!"

        room.game_over = True
        room.winner = "mafia"

    room.result_shown = True

    db.session.commit()

    return True


# --------------------------------------------------
# ROUND RESULT
# --------------------------------------------------

@rooms.route("/game/round-result")
def round_result():

    player_id = session.get("player_id")

    if not player_id:
        return "", 204

    player = db.session.get(
        Player,
        player_id
    )

    if not player:
        return "", 204

    room = db.session.get(
        Room,
        player.room_id
    )

    if not room:
        return "", 204

    if room.game_cancelled:

        message = room.game_cancel_reason

        response = make_response("")

        response.headers["HX-Redirect"] = url_for(
            "main.home",
            message=message
        )

        return response

    if not room.game_started:
        return "", 204

    client_round = request.args.get(
        "round",
        type=int
    )

    # The host started a new round
    if (
        client_round
        and client_round != room.round_number
    ):

        response = make_response("")

        response.headers["HX-Redirect"] = (
            url_for("rooms.game")
        )

        return response

    return render_template(
        "partials/round_result.html",
        room=room
    )


# --------------------------------------------------
# NEXT ROUND
# --------------------------------------------------

@rooms.route("/next-round", methods=["POST"])
def next_round():

    player_id = session.get("player_id")

    if not player_id:
        return redirect(
            url_for("main.home")
        )

    player = db.session.get(
        Player,
        player_id
    )

    if not player:
        return redirect(
            url_for("main.home")
        )

    room = db.session.get(
        Room,
        player.room_id
    )

    if not room:
        return redirect(
            url_for("main.home")
        )

    # Don't continue a cancelled game
    if room.game_cancelled:

        return redirect(
            url_for(
                "main.home",
                message=room.game_cancel_reason
            )
        )

    # Only the host can start the next round
    if room.host_id != player.id:
        return redirect(
            url_for("rooms.game")
        )

    # Don't continue a finished game
    if room.game_over:
        return redirect(
            url_for("rooms.game")
        )

    # Make sure there is actually a result
    if not room.round_result:
        return redirect(
            url_for("rooms.game")
        )

    # Advance the round
    room.round_number += 1

    # Clear the previous round result
    room.round_result = None
    room.result_shown = False

    db.session.commit()

    return redirect(
        url_for("rooms.game")
    )


# --------------------------------------------------
# HOST STATUS
# --------------------------------------------------

@rooms.route("/room/host-status")
def host_status():

    player_id = session.get("player_id")

    if not player_id:
        return "", 204

    player = db.session.get(
        Player,
        player_id
    )

    if not player:
        return "", 204

    room = db.session.get(
        Room,
        player.room_id
    )

    if not room:
        return "", 204

    if room.host_id == player.id:
        return "host"

    return "player"