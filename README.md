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

4. **Set up the database**

   If this is your first time running the app, initialise and apply the database migrations:

   ```bash
   flask db upgrade
   ```

   > If a migration folder doesn't exist yet, run `flask db init` first, then `flask db migrate -m "init"`, then `flask db upgrade`.

5. **Run the application**

   ```bash
   python app.py
   ```

6. **Open in your browser**

   Navigate to [http://localhost:5000](http://localhost:5000)

# Project Structure

```
agile-group-proj/
├── app.py              # Flask application entry point and route definitions
├── models.py           # SQLAlchemy database models
├── config.py           # Application configuration
├── requirements.txt    # Python dependencies
├── migrations/         # Flask-Migrate database migration files
├── static/             # Static assets (CSS, JS, images)
├── templates/          # Jinja2 HTML templates
└── demo_concept/       # Early design/concept files
```
