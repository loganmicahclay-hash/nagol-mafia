from database import db
from models.room import Room
from models.player import Player


def test_create_room(client):
    with client.session_transaction() as session:
        session["username"] = "TestHost"

    response = client.get("/create-room")

    assert response.status_code == 302

    room = db.session.execute(
        db.select(Room)
    ).scalar_one()

    player = db.session.execute(
        db.select(Player)
    ).scalar_one()

    assert len(room.room_code) == 4
    assert room.host_id == player.id
    assert player.username == "TestHost"
    assert player.room_id == room.id


def test_join_room(client):
    # Create a room as the host.
    with client.session_transaction() as session:
        session["username"] = "TestHost"

    client.get("/create-room")

    # Get the room code created by the host.
    with client.session_transaction() as session:
        room_code = session["room_code"]

    # Simulate a second player joining.
    with client.session_transaction() as session:
        session["username"] = "TestPlayer"

    response = client.post(
        "/join-room",
        data={"room_code": room_code},
    )

    assert response.status_code == 302

    # Verify the second player joined the correct room.
    players = db.session.execute(
        db.select(Player).order_by(Player.id)
    ).scalars().all()

    assert len(players) == 2
    assert players[0].username == "TestHost"
    assert players[1].username == "TestPlayer"
    assert players[0].room_id == players[1].room_id

    # Verify the joining player's session was updated.
    with client.session_transaction() as session:
        assert session["room_code"] == room_code
        assert session["player_id"] == players[1].id


def test_non_host_cannot_start_game(client):
    # Create a room as the host.
    with client.session_transaction() as session:
        session["username"] = "TestHost"

    client.get("/create-room")

    # Join as a second player.
    with client.session_transaction() as session:
        room_code = session["room_code"]
        session["username"] = "TestPlayer"

    client.post(
        "/join-room",
        data={"room_code": room_code},
    )

    # Try to start the game as the non-host.
    response = client.post("/start-game")

    assert response.status_code == 302

    # The game should remain unstarted.
    room = db.session.execute(
        db.select(Room)
    ).scalar_one()

    assert room.game_started is False


def test_cannot_start_game_with_fewer_than_four_players(client):
    # Create a room as the host.
    with client.session_transaction() as session:
        session["username"] = "TestHost"

    client.get("/create-room")

    # Attempt to start with only the host in the room.
    response = client.post(
        "/start-game",
        data={
            "mafia_count": 1,
            "game_mode": "elimination",
        },
    )

    assert response.status_code == 302

    # Verify the game did not start.
    room = db.session.execute(
        db.select(Room)
    ).scalar_one()

    assert room.game_started is False

    # Verify no player roles were assigned.
    players = db.session.execute(
        db.select(Player)
    ).scalars().all()

    assert len(players) == 1
    assert players[0].role is None


def test_start_game_assigns_roles(client):
    # Create a room as the host.
    with client.session_transaction() as session:
        session["username"] = "TestHost"

    client.get("/create-room")

    # Add three more players to the room.
    with client.session_transaction() as session:
        room_code = session["room_code"]

    for username in ["Player2", "Player3", "Player4"]:
        with client.session_transaction() as session:
            session["username"] = username

        client.post(
            "/join-room",
            data={"room_code": room_code},
        )

    # Restore the host's session before starting the game.
    with client.session_transaction() as session:
        host = db.session.execute(
            db.select(Player).where(
                Player.username == "TestHost"
            )
        ).scalar_one()

        session["username"] = "TestHost"
        session["player_id"] = host.id
        session["room_code"] = room_code

    response = client.post(
        "/start-game",
        data={
            "mafia_count": 1,
            "game_mode": "elimination",
        },
    )

    assert response.status_code == 302

    # Verify the game state.
    room = db.session.execute(
        db.select(Room)
    ).scalar_one()

    players = db.session.execute(
        db.select(Player).where(
            Player.room_id == room.id
        )
    ).scalars().all()

    roles = [player.role for player in players]

    assert room.game_started is True
    assert room.round_number == 1
    assert room.game_mode == "elimination"
    assert roles.count("mafia") == 1
    assert roles.count("villager") == 3
    assert all(player.is_alive for player in players)