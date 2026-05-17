"""
FitScore Unit Tests
===================
Tests routes, scoring logic, auth, and social features using an
in-memory SQLite database — completely isolated from app.db.

Run:
    pytest test_unit.py -v
"""
import os
os.environ["TESTING"] = "1"

import math
import sys
import pytest

# ---------------------------------------------------------------------------
# Make sure the app directory is on the path.
# Adjust this if your project layout differs.
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tests.test_config import TestConfig


# ---------------------------------------------------------------------------
# App / DB fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope='session')
def app():
    """Create the Flask app configured for testing (in-memory DB)."""
    from app import app as flask_app
    from extensions import db as _db

    flask_app.config.from_object(TestConfig)

    with flask_app.app_context():
        _db.create_all()
        yield flask_app
        _db.drop_all()


@pytest.fixture(scope='function')
def db(app):
    """Give each test a clean database state."""
    from extensions import db as _db
    with app.app_context():
        yield _db
        _db.session.rollback()
        # Truncate all tables between tests
        for table in reversed(_db.metadata.sorted_tables):
            _db.session.execute(table.delete())
        _db.session.commit()


@pytest.fixture
def client(app):
    return app.test_client()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def create_user(db, username='testuser', email='test@test.com', password='password123'):
    from models import User
    u = User(username=username, email=email)
    u.set_password(password)
    db.session.add(u)
    db.session.commit()
    return u


def create_exercise(db, name='Bench Press', etype='Lifting', units='kg',
                    mean=100.0, stdev=20.0):
    from models import Exercise
    e = Exercise(exercise_name=name, exercise_type=etype,
                 units=units, mean_statistic=mean, stdev_statistic=stdev)
    db.session.add(e)
    db.session.commit()
    return e


def create_log(db, user, exercise, stat_value=100.0):
    from models import Log
    z = (stat_value - exercise.mean_statistic) / exercise.stdev_statistic
    log = Log(user_id=user.user_id, exercise_id=exercise.exercise_id,
              stat_value=stat_value, standardised_score=z)
    db.session.add(log)
    db.session.commit()
    return log


def login(client, username='testuser', password='password123'):
    return client.post('/login', data={'username': username, 'password': password},
                       follow_redirects=True)


# ===========================================================================
# 1. Scoring / z_to_percentile logic
# ===========================================================================

class TestScoringLogic:

    def test_z_to_percentile_zero(self, app):
        """z=0 should map to exactly the 50th percentile."""
        with app.app_context():
            from app import z_to_percentile
            assert z_to_percentile(0) == 50

    def test_z_to_percentile_positive(self, app):
        """Positive z-score should give a percentile above 50."""
        with app.app_context():
            from app import z_to_percentile
            assert z_to_percentile(1.0) > 50

    def test_z_to_percentile_negative(self, app):
        """Negative z-score should give a percentile below 50."""
        with app.app_context():
            from app import z_to_percentile
            assert z_to_percentile(-1.0) < 50


# ===========================================================================
# 2. Authentication
# ===========================================================================

class TestAuth:

    def test_register_new_user(self, client, db, app):
        """POST /register with JSON creates a user and redirects to /home."""
        with app.app_context():
            r = client.post('/register',
                            json={'username': 'newuser', 'email': 'new@test.com',
                                  'password': 'securepass'},
                            follow_redirects=True)
            assert r.status_code == 200

            from models import User
            assert User.query.filter_by(username='newuser').first() is not None

    def test_register_duplicate_username(self, client, db, app):
        """Registering with a taken username returns 409."""
        with app.app_context():
            create_user(db, username='taken', email='taken@test.com')
            r = client.post('/register',
                            json={'username': 'taken', 'email': 'other@test.com',
                                  'password': 'password123'})
            assert r.status_code == 409
            assert r.get_json()['field'] == 'username'


# ===========================================================================
# 3. Home route
# ===========================================================================

class TestHomeRoute:

    def test_home_loads_for_authenticated_user(self, client, db, app):
        with app.app_context():
            create_user(db)
            login(client)
            r = client.get('/home')
            assert r.status_code == 200
            assert b'Welcome to FitScore' in r.data

    def test_home_shows_no_workout_message(self, client, db, app):
        with app.app_context():
            create_user(db)
            login(client)
            r = client.get('/home')
            assert b'No workouts logged yet' in r.data


# ===========================================================================
# 4. Log Exercise route
# ===========================================================================

class TestLogRoute:

    def test_log_page_loads(self, client, db, app):
        with app.app_context():
            create_user(db)
            login(client)
            r = client.get('/log')
            assert r.status_code == 200
            assert b'Log Exercise' in r.data

    def test_log_exercise_creates_entry(self, client, db, app):
        """POST /log with valid JSON creates a Log record."""
        with app.app_context():
            u = create_user(db)
            e = create_exercise(db)
            login(client)

            r = client.post('/log',
                            json={'exercise_id': e.exercise_id, 'stat_value': 105.0})
            assert r.status_code == 200
            data = r.get_json()
            assert data['success'] is True

            from models import Log
            assert Log.query.filter_by(user_id=u.user_id).count() == 1


# ===========================================================================
# 6. Leaderboard route
# ===========================================================================

class TestLeaderboardRoute:

    def test_leaderboard_loads(self, client, db, app):
        with app.app_context():
            create_user(db)
            login(client)
            r = client.get('/leaderboard')
            assert r.status_code == 200
            assert b'Leaderboard' in r.data

    def test_leaderboard_hides_users_without_logs(self, client, db, app):
        """Users with no logs should not appear on the leaderboard."""
        with app.app_context():
            create_user(db, username='nologs', email='nologs@t.com')
            u2 = create_user(db, username='haslogs', email='has@t.com')
            e = create_exercise(db)
            create_log(db, u2, e)
            login(client, username='haslogs')
            r = client.get('/leaderboard')
            assert b'haslogs' in r.data
            assert b'nologs' not in r.data


# ===========================================================================
# 7. Profile route
# ===========================================================================

class TestProfileRoute:

    def test_profile_page_loads(self, client, db, app):
        with app.app_context():
            create_user(db)
            login(client)
            r = client.get('/profile')
            assert r.status_code == 200
            assert b'Profile' in r.data

    def test_profile_update_username(self, client, db, app):
        with app.app_context():
            create_user(db)
            login(client)
            r = client.post('/profile',
                            data={'username': 'updatedname', 'firstname': '',
                                  'lastname': '', 'bio': ''},
                            follow_redirects=True)
            assert r.status_code == 200
            from models import User
            u = User.query.filter_by(username='updatedname').first()
            assert u is not None


# ===========================================================================
# 8. summarize_user_performance helper
# ===========================================================================

class TestSummarizeUserPerformance:

    def test_no_logs_returns_zero_score(self, app, db):
        with app.app_context():
            u = create_user(db)
            from app import summarize_user_performance
            result = summarize_user_performance(u)
            assert result['overall_score'] == 0
            assert result['has_logs'] is False

    def test_single_log_returns_score(self, app, db):
        with app.app_context():
            u = create_user(db)
            e = create_exercise(db, mean=100.0, stdev=20.0)
            create_log(db, u, e, stat_value=100.0)  # z=0 → 50th percentile
            from app import summarize_user_performance
            result = summarize_user_performance(u)
            assert result['has_logs'] is True
            assert result['overall_score'] == 50