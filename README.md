## Virtual Environment Logan

### Linux

```bash
source ~/.venvs/nagol-mofia/bin/activate
```

***

## Virtual Environment Logan

### Linux

```bash
source ~/.venvs/nagol-mofia/bin/activate
```

***

# Nagol Mofia

Nagol Mofia is a personal sandbox project where I'm experimenting with web development and building a multiplayer version of the social deduction game Mafia.

The project is built with Python, Flask, SQLAlchemy, SQLite, HTML, CSS, and HTMX. It supports room creation, player roles, voting, and multiple game modes.

This project is currently under development and is primarily intended for learning, experimentation, and testing with friends.

## Features

- Create and join rooms using unique four-digit room codes.
- Assign a host to each room.
- Randomly assign Mafia and Villager roles.
- Configure the number of Mafia players.
- Vote to eliminate players.
- Track eliminations and determine the winning team.
- Detect disconnected players.
- Automatically update lobby and game information.

## Game Modes

### Elimination Mode

Players vote each round to eliminate someone they suspect is Mafia.

- **Villagers win** when all Mafia players are eliminated.
- **Mafia win** when they equal or outnumber the remaining Villagers.
- **Tied vote:** Nobody is eliminated, and another round begins.

### One-Shot Mode

The game is decided by a single vote.

- **Villagers win** if the vote eliminates the last Mafia player.
- **Mafia win** if any Mafia players remain after the vote.
- **Tied vote:** The Mafia win.

## Tech Stack

- **Python** — Programming language
- **Flask** — Web application framework
- **Flask-SQLAlchemy** — Database integration
- **SQLite** — Local database
- **HTML and CSS** — User interface
- **HTMX** — Dynamic page updates
- **Git and GitHub** — Version control

## Getting Started

### Prerequisites

- Python 3
- Git
- WSL, Linux, macOS, or Windows with a compatible Python environment

### 1. Clone the Repository

```bash
git clone https://github.com/loganmicahclay-hash/nagol-mofia.git
cd nagol-mofia
```

### 2. Create a Virtual Environment

```bash
python3 -m venv .venv
```

Activate the environment.

**Linux / WSL / macOS:**

```bash
source .venv/bin/activate
```

**Windows PowerShell:**

```powershell
.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```bash
pip install Flask Flask-SQLAlchemy
```

If a `requirements.txt` file is available, install the project's listed dependencies instead:

```bash
pip install -r requirements.txt
```

### 4. Run the Application

```bash
python app.py
```

Open the application in your browser:

http://127.0.0.1:5000

Press `Ctrl+C` in the terminal to stop the server.

When finished, deactivate the virtual environment:

```bash
deactivate
```

## Project Structure

```text
nagol-mofia/
├── README.md
├── app.py
├── database.py
├── models/
│   ├── room.py
│   ├── player.py
│   └── vote.py
├── routes/
│   ├── main.py
│   └── rooms.py
├── templates/
│   ├── base.html
│   ├── home.html
│   ├── room.html
│   ├── game.html
│   └── partials/
└── static/
```

## Development Status

Nagol Mofia is an ongoing personal project. Features, gameplay rules, and the user interface may change as development continues.

The application is currently configured for local development and is not yet intended to be a production-ready public game server. The development database may be reset when the application starts, so persistent game data should not be expected.

Future improvements may include:

- Automated tests
- Improved server reliability
- Stronger handling of simultaneous player actions
- A hosted database
- Public online deployment
- Real-time multiplayer updates

---

*Built as a personal project to learn, experiment, and have fun with web development.*
