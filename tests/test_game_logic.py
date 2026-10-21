
from database import db
from models.room import Room
from models.player import Player
from models.vote import Vote


def test_valid_vote_is_recorded(client):
    # Create a room as the host.
    with client.session_transaction() as session:
        session["username"] = "TestHost"

    client.get("/create-room")

    # Save the room code.
    with client.session_transaction() as session:
        room_code = session["room_code"]

    # Add three more players.
    for username in ["Player2", "Player3", "Player4"]:
        with client.session_transaction() as session:
            session["username"] = username

        client.post(
            "/join-room",
            data={"room_code": room_code},
        )

    # Find the host and the target player.
    players = db.session.execute(
        db.select(Player).order_by(Player.id)
    ).scalars().all()

    host = next(p for p in players if p.username == "TestHost")
    target = next(p for p in players if p.id != host.id)

    # Restore the host's session.
    with client.session_transaction() as session:
        session["username"] = host.username
        session["player_id"] = host.id
        session["room_code"] = room_code

    # Start a game with one Mafia player.
    client.post(
        "/start-game",
        data={
            "mafia_count": 1,
            "game_mode": "elimination",
        },
    )

    room = db.session.execute(
        db.select(Room)
    ).scalar_one()

    assert room.game_started is True

    # Submit a vote for another player.
    response = client.post(
        "/submit-vote",
        data={"target_id": str(target.id)},
    )

    assert response.status_code == 302

    # Verify the vote was saved for the current round.
    vote = db.session.execute(
        db.select(Vote).where(
            Vote.voter_id == host.id,
            Vote.room_id == room.id,
            Vote.round_number == room.round_number,
        )
    ).scalar_one_or_none()

    assert vote is not None
    assert vote.target_id == target.id



def test_player_cannot_vote_for_themselves(client):
    # Create a room as the host.
    with client.session_transaction() as session:
        session["username"] = "TestHost"

    client.get("/create-room")

    with client.session_transaction() as session:
        room_code = session["room_code"]

    # Add three more players.
    for username in ["Player2", "Player3", "Player4"]:
        with client.session_transaction() as session:
            session["username"] = username

        client.post(
            "/join-room",
            data={"room_code": room_code},
        )

    # Find the host.
    host = db.session.execute(
        db.select(Player).where(
            Player.username == "TestHost"
        )
    ).scalar_one()

    # Restore the host's session.
    with client.session_transaction() as session:
        session["username"] = host.username
        session["player_id"] = host.id
        session["room_code"] = room_code

    # Start the game.
    client.post(
        "/start-game",
        data={
            "mafia_count": 1,
            "game_mode": "elimination",
        },
    )

    room = db.session.execute(
        db.select(Room)
    ).scalar_one()

    # Attempt to vote for the host themselves.
    response = client.post(
        "/submit-vote",
        data={"target_id": str(host.id)},
    )

    assert response.status_code == 302

    # No vote should have been recorded.
    vote_count = db.session.execute(
        db.select(db.func.count())
        .select_from(Vote)
        .where(
            Vote.voter_id == host.id,
            Vote.room_id == room.id,
            Vote.round_number == room.round_number,
        )
    ).scalar_one()

    assert vote_count == 0



def test_player_cannot_vote_twice_in_one_round(client):
    # Create a room as the host.
    with client.session_transaction() as session:
        session["username"] = "TestHost"

    client.get("/create-room")

    with client.session_transaction() as session:
        room_code = session["room_code"]

    # Add three more players.
    for username in ["Player2", "Player3", "Player4"]:
        with client.session_transaction() as session:
            session["username"] = username

        client.post(
            "/join-room",
            data={"room_code": room_code},
        )

    # Find the host and two possible targets.
    players = db.session.execute(
        db.select(Player).order_by(Player.id)
    ).scalars().all()

    host = next(p for p in players if p.username == "TestHost")
    targets = [p for p in players if p.id != host.id]

    # Restore the host's session.
    with client.session_transaction() as session:
        session["username"] = host.username
        session["player_id"] = host.id
        session["room_code"] = room_code

    # Start the game.
    client.post(
        "/start-game",
        data={
            "mafia_count": 1,
            "game_mode": "elimination",
        },
    )

    room = db.session.execute(
        db.select(Room)
    ).scalar_one()

    # Submit the first vote.
    client.post(
        "/submit-vote",
        data={"target_id": str(targets[0].id)},
    )

    # Attempt to change the vote to a different target.
    client.post(
        "/submit-vote",
        data={"target_id": str(targets[1].id)},
    )

    # Only the original vote should exist.
    votes = db.session.execute(
        db.select(Vote).where(
            Vote.voter_id == host.id,
            Vote.room_id == room.id,
            Vote.round_number == room.round_number,
        )
    ).scalars().all()

    assert len(votes) == 1
    assert votes[0].target_id == targets[0].id



def test_dead_player_cannot_vote(client):
    # Create a room as the host.
    with client.session_transaction() as session:
        session["username"] = "TestHost"

    client.get("/create-room")

    with client.session_transaction() as session:
        room_code = session["room_code"]

    # Add three more players.
    for username in ["Player2", "Player3", "Player4"]:
        with client.session_transaction() as session:
            session["username"] = username

        client.post(
            "/join-room",
            data={"room_code": room_code},
        )

    # Find the players.
    players = db.session.execute(
        db.select(Player).order_by(Player.id)
    ).scalars().all()

    host = next(p for p in players if p.username == "TestHost")
    target = next(p for p in players if p.id != host.id)

    # Restore the host's session.
    with client.session_transaction() as session:
        session["username"] = host.username
        session["player_id"] = host.id
        session["room_code"] = room_code

    # Start the game.
    client.post(
        "/start-game",
        data={
            "mafia_count": 1,
            "game_mode": "elimination",
        },
    )

    room = db.session.execute(
        db.select(Room)
    ).scalar_one()

    # Mark the host as dead.
    host.is_alive = False
    db.session.commit()

    # Attempt to vote as the dead host.
    client.post(
        "/submit-vote",
        data={"target_id": str(target.id)},
    )

    # No vote should have been recorded.
    votes = db.session.execute(
        db.select(Vote).where(
            Vote.voter_id == host.id,
            Vote.room_id == room.id,
            Vote.round_number == room.round_number,
        )
    ).scalars().all()

    assert len(votes) == 0



def test_player_cannot_vote_for_dead_target(client):
    # Create a room as the host.
    with client.session_transaction() as session:
        session["username"] = "TestHost"

    client.get("/create-room")

    with client.session_transaction() as session:
        room_code = session["room_code"]

    # Add three more players.
    for username in ["Player2", "Player3", "Player4"]:
        with client.session_transaction() as session:
            session["username"] = username

        client.post(
            "/join-room",
            data={"room_code": room_code},
        )

    # Find the host and another player.
    players = db.session.execute(
        db.select(Player).order_by(Player.id)
    ).scalars().all()

    host = next(p for p in players if p.username == "TestHost")
    target = next(p for p in players if p.id != host.id)

    # Restore the host's session.
    with client.session_transaction() as session:
        session["username"] = host.username
        session["player_id"] = host.id
        session["room_code"] = room_code

    # Start the game.
    client.post(
        "/start-game",
        data={
            "mafia_count": 1,
            "game_mode": "elimination",
        },
    )

    room = db.session.execute(
        db.select(Room)
    ).scalar_one()

    # Eliminate the target.
    target.is_alive = False
    db.session.commit()

    # Attempt to vote for the eliminated player.
    client.post(
        "/submit-vote",
        data={"target_id": str(target.id)},
    )

    # Verify no vote was recorded.
    votes = db.session.execute(
        db.select(Vote).where(
            Vote.voter_id == host.id,
            Vote.room_id == room.id,
            Vote.round_number == room.round_number,
        )
    ).scalars().all()

    assert len(votes) == 0



def test_player_cannot_vote_for_someone_in_another_room(client):
    # Create the first room.
    with client.session_transaction() as session:
        session["username"] = "Host1"

    client.get("/create-room")

    with client.session_transaction() as session:
        first_room_code = session["room_code"]

    # Add three more players to the first room.
    for username in ["Player2", "Player3", "Player4"]:
        with client.session_transaction() as session:
            session["username"] = username

        client.post(
            "/join-room",
            data={"room_code": first_room_code},
        )

    # Create a second room with a separate player.
    with client.session_transaction() as session:
        session["username"] = "Host2"

    client.get("/create-room")

    # Find the first room's players and the second room's host.
    players = db.session.execute(
        db.select(Player).order_by(Player.id)
    ).scalars().all()

    host1 = next(p for p in players if p.username == "Host1")
    host2 = next(p for p in players if p.username == "Host2")

    # Restore Host1's session.
    with client.session_transaction() as session:
        session["username"] = host1.username
        session["player_id"] = host1.id
        session["room_code"] = first_room_code

    # Start the first room's game.
    client.post(
        "/start-game",
        data={
            "mafia_count": 1,
            "game_mode": "elimination",
        },
    )

    room = db.session.execute(
        db.select(Room).where(
            Room.room_code == first_room_code
        )
    ).scalar_one()

    # Attempt to vote for Host2, who belongs to another room.
    client.post(
        "/submit-vote",
        data={"target_id": str(host2.id)},
    )

    # Verify that no vote was recorded against Host2.
    votes = db.session.execute(
        db.select(Vote).where(
            Vote.voter_id == host1.id,
            Vote.target_id == host2.id,
            Vote.room_id == room.id,
            Vote.round_number == room.round_number,
        )
    ).scalars().all()

    assert len(votes) == 0