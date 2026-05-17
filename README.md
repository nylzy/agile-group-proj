# Fitness Tracker Web Application

A group project developed for **CITS3403 Agile Web Development** at the University of Western Australia.

# Group Members
The following application is developed by the following students:

| Student ID | Name | GitHub Username |
|---|---|---|
| 24215157 | Lukas Rohwer | [lukasmrohwer](https://github.com/lukasmrohwer) |
| 22708177 | Tom Nylund | [nylzy](https://github.com/nylzy) |
| 24220855 | Eric Townsend | [yamato1327](https://github.com/yamato1327) |
| 24012961 | Kenn Lukman | [kenserous](https://github.com/kenserous) |

# Description

This web application is a **personal fitness tracking platform** that allows users to log their exercise activity, track performance over time, and compare results with friends on a leaderboard.

# Purpose

The application is designed to motivate users to stay active by giving them a centralised place to record workouts, view their progress, and engage socially with friends. By standardising scores across different exercise types, users can be ranked fairly on a shared leaderboard regardless of whether they run, lift, or swim.

# Design

The application is built using:

- **Python Flask:** backend web framework handling routing, authentication, and database interaction
- **SQLAlchemy + Flask-Migrate:** ORM and database migration management usingSQLite
- **HTML + Bootstrap CSS:** frontend web templates
- **JavaScript / jQuery (AJAX):** dynamic interactions without full page reloads
- **Flask-Login:** session-based user authentication

The database consists of four core models:

| Model | Description |
|---|---|
| `User` | Stores account credentials and profile information |
| `Exercise` | Catalogue of exercises with statistical benchmarks (mean & std dev) |
| `Log` | Records of individual exercise sessions per user, including a standardised z-score |
| `Friendship` | Tracks connections between users for social features |

## Key Pages

| Route | Description |
|---|---|
| `/` | Landing / index page |
| `/login` | User login |
| `/register` | New account registration |
| `/home` | User dashboard (login required) |
| `/log` | Log a new exercise session (login required) |
| `/leaderboard` | View ranked leaderboard (login required) |
| `/social` | Friend activity and social features (login required) |
| `/profile` | User profile page (login required) |

# Launching the Application

## Prerequisites

- Python 3.8 or higher
- `pip` package manager

## Steps

1. **Clone the repository**

   ```bash
   git clone https://github.com/nylzy/agile-group-proj.git
   cd agile-group-proj
   ```

2. **Create and activate a virtual environment** (recommended)

   ```bash
   # macOS / Linux
   python3 -m venv venv
   source venv/bin/activate

   # Windows
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

   > `requirements.txt` includes `pytest` and `selenium` for running the test suite.

4. **Set up Environment Variables**

   The application requires a secure secret key to run correctly. You can copy the example `.env` file and generate a new key using Python:

   ```bash
   # Windows (PowerShell)
   cp .env.example .env
   $key = python -c "import secrets; print(secrets.token_hex(32))"
   (Get-Content .env) -replace 'your_secure_secret_key_here', $key | Set-Content .env

   # macOS / Linux (Bash)
   cp .env.example .env
   sed -i "s/your_secure_secret_key_here/$(python3 -c 'import secrets; print(secrets.token_hex(32))')/g" .env
   ```

5. **Set up the database**

   If this is your first time running the app, initialise and apply the database migrations:

   ```bash
   flask db upgrade
   ```

   > If a migration folder doesn't exist yet, run `flask db init` first, then `flask db migrate -m "init"`, then `flask db upgrade`.

6. **Run the application**

   ```bash
   python app.py
   ```

7. **Open in your browser**

   Navigate to [http://localhost:5000](http://localhost:5000)

# Project Structure

```
agile-group-proj/
├── app.py              # Flask application entry point and route definitions
├── models.py           # SQLAlchemy database models
├── config.py           # Application configuration
├── extensions.py       # SQLAlchemy and Migrate extension instances
├── requirements.txt    # Python dependencies
├── migrations/         # Flask-Migrate database migration files
├── static/             # Static assets (CSS, JS, images)
├── templates/          # Jinja2 HTML templates
├── demo_concept/       # Early design/concept files
└── tests/
    ├── test_config.py  # Isolated test configuration (in-memory SQLite)
    ├── test_unit.py    # Unit tests (routes, scoring logic, auth)
    └── test_selenium.py# Selenium UI/browser tests
```

# Running Tests

The test suite uses an in-memory SQLite database completely isolated from `app.db`. You do **not** need to start the server manually — the Selenium tests spin up Flask automatically.

## Prerequisites

Install test dependencies (already in `requirements.txt`):

```bash
pip install -r requirements.txt
```

For Selenium tests, Chrome and ChromeDriver are also required:
Instructions below are only if you don't already have either installed.

```bash
# Ubuntu / Debian
sudo apt-get install -y chromium-browser chromium-chromedriver

# macOS (via Homebrew)
brew install --cask chromedriver
```

## Running Unit Tests

Unit tests cover route logic, scoring calculations, authentication, and database behaviour.

```bash
pytest tests/test_unit.py -v
```

## Running Selenium Tests

Selenium tests launch a headless Chrome browser and exercise the full UI. Flask is started automatically on port 5099 — no separate terminal needed.

```bash
pytest tests/test_selenium.py -v
```

## Running All Tests

```bash
pytest tests/ -v
```