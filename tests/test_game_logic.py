
from database import db
from models.room import Room
from models.player import Player
from models.vote import Vote
from routes.rooms import check_win_condition, remove_player


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

# Clear the first room's session and create a second room.
    with client.session_transaction() as session:
        session.clear()
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



def test_votes_do_not_resolve_until_everyone_has_voted(client):
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

    # Retrieve the players.
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
        db.select(Room).where(Room.room_code == room_code)
    ).scalar_one()

    # Submit only one vote.
    client.post(
        "/submit-vote",
        data={"target_id": str(target.id)},
    )

    # Refresh database objects to inspect the saved state.
    db.session.refresh(room)
    db.session.refresh(target)

    # The round should not resolve after only one of four votes.
    assert target.is_alive is True
    assert room.result_shown is False
    assert room.round_number == 1



def test_player_with_most_votes_is_eliminated(client):
    # Create the room as the host.
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

    players = db.session.execute(
        db.select(Player).order_by(Player.id)
    ).scalars().all()

    host = next(p for p in players if p.username == "TestHost")

    # Choose two different targets, neither of which is the host.
    targets = [p for p in players if p.id != host.id]
    eliminated_target = targets[0]
    other_target = targets[1]

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

    room = db.session.execute(
        db.select(Room).where(Room.room_code == room_code)
    ).scalar_one()
    
    # Three players vote for Player2; the last votes for Player4.
    vote_plan = [
        (players[0], players[1]),  # TestHost -> Player2
        (players[2], players[1]),  # Player3 -> Player2
        (players[3], players[1]),  # Player4 -> Player2
        (players[1], players[2]),  # Player2 -> Player3
    ]


    for voter, target in vote_plan:
        with client.session_transaction() as session:
            session["username"] = voter.username
            session["player_id"] = voter.id
            session["room_code"] = room_code

        client.post(
            "/submit-vote",
            data={"target_id": str(target.id)},
        )

    db.session.refresh(eliminated_target)
    db.session.refresh(room)

    votes = db.session.execute(
        db.select(Vote).where(
            Vote.room_id == room.id,
            Vote.round_number == room.round_number,
        )
    ).scalars().all()

    assert len(votes) == 4
    assert eliminated_target.is_alive is False
    assert room.result_shown is True
    assert eliminated_target.username in room.round_result



def test_tied_votes_do_not_eliminate_anyone(client):
    # Create the room as the host.
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

    players = db.session.execute(
        db.select(Player).order_by(Player.id)
    ).scalars().all()

    host = next(p for p in players if p.username == "TestHost")

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

    room = db.session.execute(
        db.select(Room).where(Room.room_code == room_code)
    ).scalar_one()

    # TestHost and Player2 each receive two votes.
    vote_plan = [
        (players[0], players[1]),  # TestHost -> Player2
        (players[1], players[0]),  # Player2 -> TestHost
        (players[2], players[0]),  # Player3 -> TestHost
        (players[3], players[1]),  # Player4 -> Player2
    ]

    for voter, target in vote_plan:
        with client.session_transaction() as session:
            session["username"] = voter.username
            session["player_id"] = voter.id
            session["room_code"] = room_code

        client.post(
            "/submit-vote",
            data={"target_id": str(target.id)},
        )

    db.session.refresh(room)

    # Refresh the players to check their current alive status.
    for player in players:
        db.session.refresh(player)

    votes = db.session.execute(
        db.select(Vote).where(
            Vote.room_id == room.id,
            Vote.round_number == room.round_number,
        )
    ).scalars().all()

    assert len(votes) == 4
    assert all(player.is_alive for player in players)
    assert room.result_shown is True
    assert "tied" in room.round_result.lower()
    assert room.game_over is False



def test_tied_votes_in_one_shot_mode_mafia_wins(client):
    # Create the room as the host.
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

    players = db.session.execute(
        db.select(Player).order_by(Player.id)
    ).scalars().all()

    host = next(p for p in players if p.username == "TestHost")

    # Start a one-shot game as the host.
    with client.session_transaction() as session:
        session["username"] = host.username
        session["player_id"] = host.id
        session["room_code"] = room_code

    client.post(
        "/start-game",
        data={
            "mafia_count": 1,
            "game_mode": "one_shot",
        },
    )

    room = db.session.execute(
        db.select(Room).where(Room.room_code == room_code)
    ).scalar_one()

    # TestHost and Player2 each receive two votes.
    vote_plan = [
        (players[0], players[1]),  # TestHost -> Player2
        (players[1], players[0]),  # Player2 -> TestHost
        (players[2], players[0]),  # Player3 -> TestHost
        (players[3], players[1]),  # Player4 -> Player2
    ]

    for voter, target in vote_plan:
        with client.session_transaction() as session:
            session["username"] = voter.username
            session["player_id"] = voter.id
            session["room_code"] = room_code

        client.post(
            "/submit-vote",
            data={"target_id": str(target.id)},
        )

    db.session.refresh(room)

    assert room.result_shown is True
    assert room.game_over is True
    assert room.winner == "mafia"
    assert "tied" in room.round_result.lower()
    assert "Mafia wins!" in room.round_result



def test_eliminating_last_mafia_player_makes_villagers_win(client):
    # Create the room as the host.
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

    players = db.session.execute(
        db.select(Player).order_by(Player.id)
    ).scalars().all()

    host = next(p for p in players if p.username == "TestHost")

    # Start the game with one Mafia player.
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

    room = db.session.execute(
        db.select(Room).where(Room.room_code == room_code)
    ).scalar_one()

    # Find the Mafia player and have everyone vote for them.
    mafia_player = next(
        player for player in players
        if player.role == "mafia"
    )

    vote_plan = [
        (voter, mafia_player)
        for voter in players
        if voter.id != mafia_player.id
    ]

    # The Mafia player must also vote for someone else.
    other_target = next(
        player for player in players
        if player.id != mafia_player.id
    )
    vote_plan.append((mafia_player, other_target))

    for voter, target in vote_plan:
        with client.session_transaction() as session:
            session["username"] = voter.username
            session["player_id"] = voter.id
            session["room_code"] = room_code

        client.post(
            "/submit-vote",
            data={"target_id": str(target.id)},
        )

    db.session.refresh(room)
    db.session.refresh(mafia_player)

    assert mafia_player.is_alive is False
    assert room.game_over is True
    assert room.winner == "villagers"
    assert "Villagers win!" in room.round_result



def test_mafia_wins_when_they_equal_living_villagers(client):
    # Create a room.
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

    players = db.session.execute(
        db.select(Player).order_by(Player.id)
    ).scalars().all()

    room = db.session.execute(
        db.select(Room).where(Room.room_code == room_code)
    ).scalar_one()

    # Set up a game state with one Mafia and one Villager alive.
    mafia_player = players[0]
    villager_player = players[1]

    mafia_player.role = "mafia"
    mafia_player.is_alive = True

    villager_player.role = "villager"
    villager_player.is_alive = True

    # The other two players are eliminated Villagers.
    for player in players[2:]:
        player.role = "villager"
        player.is_alive = False

    room.game_mode = "elimination"
    room.game_started = True

    db.session.commit()

    assert check_win_condition(room) == "mafia"



def test_player_cannot_vote_after_game_ends(client):
    # Create the room as the host.
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

    players = db.session.execute(
        db.select(Player).order_by(Player.id)
    ).scalars().all()

    host = next(p for p in players if p.username == "TestHost")

    # Start the game.
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

    room = db.session.execute(
        db.select(Room).where(Room.room_code == room_code)
    ).scalar_one()

    # Simulate a game that has already ended.
    room.game_over = True
    room.winner = "villagers"
    db.session.commit()

    target = next(p for p in players if p.id != host.id)

    # Attempt to vote after the game ends.
    with client.session_transaction() as session:
        session["username"] = host.username
        session["player_id"] = host.id
        session["room_code"] = room_code

    response = client.post(
        "/submit-vote",
        data={"target_id": str(target.id)},
    )

    # The request should redirect without recording a vote.
    assert response.status_code == 302

    votes = db.session.execute(
        db.select(Vote).where(
            Vote.room_id == room.id,
            Vote.round_number == room.round_number,
        )
    ).scalars().all()

    assert len(votes) == 0


def test_player_cannot_vote_after_game_is_cancelled(client):
    # Create the room as the host.
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

    players = db.session.execute(
        db.select(Player).order_by(Player.id)
    ).scalars().all()

    host = next(p for p in players if p.username == "TestHost")

    # Start the game.
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

    room = db.session.execute(
        db.select(Room).where(Room.room_code == room_code)
    ).scalar_one()

    # Simulate a canceled game.
    room.game_cancelled = True
    room.game_cancel_reason = "Test cancellation"
    db.session.commit()

    target = next(p for p in players if p.id != host.id)

    # Attempt to vote after cancellation.
    with client.session_transaction() as session:
        session["username"] = host.username
        session["player_id"] = host.id
        session["room_code"] = room_code

    response = client.post(
        "/submit-vote",
        data={"target_id": str(target.id)},
    )

    assert response.status_code == 302

    votes = db.session.execute(
        db.select(Vote).where(
            Vote.room_id == room.id,
            Vote.round_number == room.round_number,
        )
    ).scalars().all()

    assert len(votes) == 0


def test_leaving_active_game_cancels_game(client):
    # Create a room with four players.
    with client.session_transaction() as session:
        session["username"] = "TestHost"

    client.get("/create-room")

    with client.session_transaction() as session:
        room_code = session["room_code"]

    for username in ["Player2", "Player3", "Player4"]:
        with client.session_transaction() as session:
            session["username"] = username

        client.post(
            "/join-room",
            data={"room_code": room_code},
        )

    players = db.session.execute(
        db.select(Player).order_by(Player.id)
    ).scalars().all()

    host = next(
        player for player in players
        if player.username == "TestHost"
    )
    leaving_player = next(
        player for player in players
        if player.username == "Player2"
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

    room = db.session.execute(
        db.select(Room).where(Room.room_code == room_code)
    ).scalar_one()

    # Simulate the player leaving.
    leaving_player_id = leaving_player.id
    leaving_username = leaving_player.username

    remove_player(leaving_player)
    db.session.commit()

    # Verify that the game was canceled.
    assert room.game_cancelled is True
    assert room.game_started is False
    assert room.game_cancel_reason == (
        f"{leaving_username} left the game."
    )

    # Verify that the player was deleted.
    assert db.session.get(Player, leaving_player_id) is None


def test_host_leaving_lobby_transfers_host(client):
    # Create a room as the original host.
    with client.session_transaction() as session:
        session["username"] = "OriginalHost"

    client.get("/create-room")

    with client.session_transaction() as session:
        room_code = session["room_code"]

    # Add a second player.
    with client.session_transaction() as session:
        session["username"] = "Player2"

    client.post(
        "/join-room",
        data={"room_code": room_code},
    )

    # Retrieve the room and its players.
    room = db.session.execute(
        db.select(Room).where(Room.room_code == room_code)
    ).scalar_one()

    original_host = next(
        player for player in room.players
        if player.username == "OriginalHost"
    )

    second_player = next(
        player for player in room.players
        if player.username == "Player2"
    )

    # Simulate the original host leaving.
    remove_player(original_host)
    db.session.commit()

    # The remaining player should become the host.
    assert db.session.get(Player, original_host.id) is None
    assert room.host_id == second_player.id


def test_room_is_deleted_when_last_player_leaves(client):
    # Create a room with one player.
    with client.session_transaction() as session:
        session["username"] = "TestHost"

    client.get("/create-room")

    with client.session_transaction() as session:
        room_code = session["room_code"]

    # Retrieve the room and its only player.
    room = db.session.execute(
        db.select(Room).where(Room.room_code == room_code)
    ).scalar_one()

    player = room.players[0]
    room_id = room.id

    # Remove the last player.
    remove_player(player)
    db.session.commit()

    # Verify that both the player and room were deleted.
    assert db.session.get(Player, player.id) is None
    assert db.session.get(Room, room_id) is None


def test_non_host_cannot_start_next_round(client):
    # Create a room and its host.
    client.post("/", data={"username": "Host"})
    client.get("/create-room")

    with client.session_transaction() as session:
        room_code = session["room_code"]
        host_id = session["player_id"]

    # Add another player.
    with client.session_transaction() as session:
        session.clear()

    client.post("/", data={"username": "Player2"})
    client.post("/join-room", data={"room_code": room_code})

    with client.session_transaction() as session:
        player2_id = session["player_id"]

    # Set up the room as if a round has finished.
    from models.room import Room
    from models.player import Player
    from database import db

    with client.application.app_context():
        room = Room.query.filter_by(room_code=room_code).first()
        room.game_started = True
        room.round_result = "A player was eliminated."
        db.session.commit()

    # Attempt to start the next round as Player 2.
    response = client.post("/next-round", follow_redirects=False)

    assert response.status_code == 302
    assert response.location.endswith("/game")

    # Verify the round did not advance.
    with client.application.app_context():
        room = Room.query.filter_by(room_code=room_code).first()
        assert room.round_number == 1


def test_non_host_cannot_start_next_round_after_game_over(client):
    # Create a room and its host.
    client.post("/", data={"username": "Host"})
    client.get("/create-room")

    with client.session_transaction() as session:
        room_code = session["room_code"]

    # Set up a finished game with a round result.
    from models.room import Room
    from database import db

    with client.application.app_context():
        room = Room.query.filter_by(room_code=room_code).first()
        room.game_started = True
        room.game_over = True
        room.round_result = "Mafia wins!"
        db.session.commit()

    # Attempt to advance the round.
    response = client.post("/next-round", follow_redirects=False)

    assert response.status_code == 302
    assert response.location.endswith("/game")

    # Verify the round did not advance.
    with client.application.app_context():
        room = Room.query.filter_by(room_code=room_code).first()
        assert room.round_number == 1


def test_host_cannot_start_next_round_without_result(client):
    client.post("/", data={"username": "Host"})
    client.get("/create-room")

    with client.session_transaction() as session:
        room_code = session["room_code"]

    from models.room import Room
    from database import db

    with client.application.app_context():
        room = Room.query.filter_by(room_code=room_code).first()
        room.game_started = True
        room.round_result = None
        db.session.commit()

    response = client.post("/next-round", follow_redirects=False)

    assert response.status_code == 302
    assert response.location.endswith("/game")

    with client.application.app_context():
        room = Room.query.filter_by(room_code=room_code).first()
        assert room.round_number == 1


def test_player_cannot_vote_after_round_is_resolved(client):
    # Create a room and host.
    client.post("/", data={"username": "Host"})
    client.get("/create-room")

    with client.session_transaction() as session:
        room_code = session["room_code"]

    # Add a second player.
    client.get("/logout")
    client.post("/", data={"username": "Player2"})
    client.post("/join-room", data={"room_code": room_code})

    from models.room import Room
    from models.player import Player
    from database import db

    with client.application.app_context():
        room = Room.query.filter_by(room_code=room_code).first()
        room_id = room.id
        players = Player.query.filter_by(room_id=room_id).all()

        room.game_started = True
        room.round_result = "Player2 was eliminated!"
        db.session.commit()

        host_id = players[0].id
        target_id = players[1].id

    # Log back in as the host.
    with client.session_transaction() as session:
        session["player_id"] = host_id
        session["room_code"] = room_code
        session["username"] = "Host"

    response = client.post(
        "/submit-vote",
        data={"target_id": target_id},
        follow_redirects=False
    )

    assert response.status_code == 302

    # Verify that no vote was recorded.
    from models.vote import Vote

    with client.application.app_context():
        assert Vote.query.filter_by(room_id=room_id).count() == 0


def test_dead_player_cannot_submit_vote(client):
    client.post("/", data={"username": "Host"})
    client.get("/create-room")

    with client.session_transaction() as session:
        room_code = session["room_code"]

    from models.room import Room
    from models.player import Player
    from models.vote import Vote
    from database import db

    with client.application.app_context():
        room = Room.query.filter_by(room_code=room_code).first()
        room_id = room.id
        player = Player.query.filter_by(room_id=room_id).first()

        room.game_started = True
        player.is_alive = False
        db.session.commit()

        player_id = player.id

    response = client.post(
        "/submit-vote",
        data={"target_id": player_id},
        follow_redirects=False
    )

    assert response.status_code == 302

    with client.application.app_context():
        assert Vote.query.filter_by(room_id=room_id).count() == 0
