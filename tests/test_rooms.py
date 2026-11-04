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


def test_invalid_mafia_count_does_not_start_game(client):
    # Create a room as the host.
    with client.session_transaction() as session:
        session["username"] = "TestHost"

    client.get("/create-room")

    # Get the room code.
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

    # Restore the host's session.
    host = db.session.execute(
        db.select(Player).where(
            Player.username == "TestHost"
        )
    ).scalar_one()

    with client.session_transaction() as session:
        session["username"] = "TestHost"
        session["player_id"] = host.id
        session["room_code"] = room_code

    # Try starting with zero Mafia players.
    response = client.post(
        "/start-game",
        data={
            "mafia_count": 0,
            "game_mode": "elimination",
        },
    )

    assert response.status_code == 302

    # The game should remain unstarted.
    room = db.session.execute(
        db.select(Room)
    ).scalar_one()

    assert room.game_started is False

    # No roles should have been assigned.
    players = db.session.execute(
        db.select(Player).where(
            Player.room_id == room.id
        )
    ).scalars().all()

    assert all(player.role is None for player in players)


def test_too_many_mafia_players_does_not_start_game(client):
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

    # Restore the host's session.
    host = db.session.execute(
        db.select(Player).where(
            Player.username == "TestHost"
        )
    ).scalar_one()

    with client.session_transaction() as session:
        session["username"] = "TestHost"
        session["player_id"] = host.id
        session["room_code"] = room_code

    # Two Mafia players are invalid for a four-player game.
    response = client.post(
        "/start-game",
        data={
            "mafia_count": 2,
            "game_mode": "elimination",
        },
    )

    assert response.status_code == 302

    room = db.session.execute(
        db.select(Room)
    ).scalar_one()

    assert room.game_started is False

    players = db.session.execute(
        db.select(Player).where(
            Player.room_id == room.id
        )
    ).scalars().all()

    assert all(player.role is None for player in players)


def test_player_cannot_join_after_game_starts(client):
    # Create a room as the host.
    with client.session_transaction() as session:
        session["username"] = "TestHost"

    client.get("/create-room")

    with client.session_transaction() as session:
        room_code = session["room_code"]

    # Add three players so the game can start.
    for username in ["Player2", "Player3", "Player4"]:
        with client.session_transaction() as session:
            session["username"] = username

        client.post(
            "/join-room",
            data={"room_code": room_code},
        )

    # Find the host.
    room = db.session.execute(
        db.select(Room).where(Room.room_code == room_code)
    ).scalar_one()

    host = next(
        player for player in room.players
        if player.username == "TestHost"
    )

    # Start the game as the host.
    with client.session_transaction() as session:
        session["username"] = host.username
        session["player_id"] = host.id
        session["room_code"] = room_code

    client.post(
        "/start-game",
        data={
            "mafia_count": 1,
            "game_mode": "elimination",
        },
    )

    # Attempt to join as a fifth player.
    with client.session_transaction() as session:
        session["username"] = "LatePlayer"
        session.pop("player_id", None)
        session.pop("room_code", None)

    response = client.post(
        "/join-room",
        data={"room_code": room_code},
    )

    # The player should be rejected and shown the join page.
    assert response.status_code == 200
    assert b"That game has already started." in response.data

    # Verify that no fifth player was added.
    room = db.session.get(Room, room.id)
    assert len(room.players) == 4
    assert all(
        player.username != "LatePlayer"
        for player in room.players
    )


def test_player_cannot_join_cancelled_room(client):
    # Create a room as the host.
    with client.session_transaction() as session:
        session["username"] = "TestHost"

    client.get("/create-room")

    with client.session_transaction() as session:
        room_code = session["room_code"]

    # Add another player.
    with client.session_transaction() as session:
        session["username"] = "Player2"

    client.post(
        "/join-room",
        data={"room_code": room_code},
    )

    # Mark the room as canceled.
    room = db.session.execute(
        db.select(Room).where(Room.room_code == room_code)
    ).scalar_one()

    room.game_cancelled = True
    room.game_cancel_reason = "Test cancellation"
    db.session.commit()

    # Attempt to join as a new player.
    with client.session_transaction() as session:
        session["username"] = "LatePlayer"
        session.pop("player_id", None)
        session.pop("room_code", None)

    response = client.post(
        "/join-room",
        data={"room_code": room_code},
    )

    # The join should be rejected.
    assert response.status_code == 200
    assert b"Room not found or is no longer active." in response.data

    # Verify that no new player was added.
    room = db.session.get(Room, room.id)
    assert len(room.players) == 2
    assert all(
        player.username != "LatePlayer"
        for player in room.players
    )


def test_player_cannot_access_another_rooms_lobby(client):
    # Create Room A.
    with client.session_transaction() as session:
        session["username"] = "PlayerA"

    client.get("/create-room")

    with client.session_transaction() as session:
        room_a_code = session["room_code"]
        player_a_id = session["player_id"]

    # Create Room B using a separate player session.
    with client.session_transaction() as session:
        session.clear()
        session["username"] = "PlayerB"

    client.get("/create-room")

    with client.session_transaction() as session:
        room_b_code = session["room_code"]

    # Simulate Player A trying to access Room B.
    with client.session_transaction() as session:
        session["username"] = "PlayerA"
        session["player_id"] = player_a_id
        session["room_code"] = room_b_code

    response = client.get("/room", follow_redirects=False)

    # A secure route should reject the mismatched membership.
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")


def test_player_cannot_access_game_with_wrong_room_code(client):
    # Create PlayerA's room.
    with client.session_transaction() as session:
        session["username"] = "PlayerA"

    client.get("/create-room")

    with client.session_transaction() as session:
        player_a_id = session["player_id"]

    # Create PlayerB's room.
    with client.session_transaction() as session:
        session.clear()
        session["username"] = "PlayerB"

    client.get("/create-room")

    with client.session_transaction() as session:
        room_b_code = session["room_code"]

    # Give PlayerA the wrong room code.
    with client.session_transaction() as session:
        session["player_id"] = player_a_id
        session["room_code"] = room_b_code

    response = client.get("/game", follow_redirects=False)

    assert response.status_code == 302
    assert response.location.endswith("/")


def test_player_cannot_access_another_rooms_game(client):
    # Create Room A as Player A.
    client.post("/", data={"username": "PlayerA"})
    client.get("/create-room")

    with client.session_transaction() as session:
        player_a_id = session["player_id"]

    # Create Room B as Player B.
    with client.session_transaction() as session:
        session.clear()

    client.post("/", data={"username": "PlayerB"})
    client.get("/create-room")

    with client.session_transaction() as session:
        room_b_code = session["room_code"]

    # Give Player A Room B's room code.
    with client.session_transaction() as session:
        session["player_id"] = player_a_id
        session["room_code"] = room_b_code

    # Attempt to access Room B's game.
    response = client.get("/game", follow_redirects=False)

    assert response.status_code == 302
    assert response.location.endswith("/")


def test_player_cannot_access_game_before_start(client):
    client.post("/", data={"username": "PlayerA"})
    client.get("/create-room")

    response = client.get("/game", follow_redirects=False)

    assert response.status_code == 302
    assert response.location.endswith("/room")