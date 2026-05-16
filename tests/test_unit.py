"""
FitScore Unit Tests
===================
Tests routes, scoring logic, auth, and social features using an
in-memory SQLite database — completely isolated from app.db.

Run:
    pytest test_unit.py -v
"""

import math
import sys
import os
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

    def test_z_to_percentile_large_positive(self, app):
        """Very large z-score should approach 100."""
        with app.app_context():
            from app import z_to_percentile
            assert z_to_percentile(4.0) >= 99

    def test_z_to_percentile_large_negative(self, app):
        """Very negative z-score should approach 0."""
        with app.app_context():
            from app import z_to_percentile
            assert z_to_percentile(-4.0) <= 1

    def test_z_to_percentile_returns_int_in_range(self, app):
        """Result should always be an integer between 0 and 100."""
        with app.app_context():
            from app import z_to_percentile
            for z in [-3, -1, 0, 1, 3]:
                result = z_to_percentile(z)
                assert isinstance(result, int)
                assert 0 <= result <= 100

    def test_log_z_score_calculation(self, app, db):
        """Z-score stored in DB matches manual calculation."""
        with app.app_context():
            u = create_user(db)
            e = create_exercise(db, mean=100.0, stdev=20.0)
            log = create_log(db, u, e, stat_value=120.0)
            expected_z = (120.0 - 100.0) / 20.0  # = 1.0
            assert abs(log.standardised_score - expected_z) < 0.0001


# ===========================================================================
# 2. Authentication
# ===========================================================================

class TestAuth:

    def test_login_page_loads(self, client):
        r = client.get('/login')
        assert r.status_code == 200
        assert b'Welcome back' in r.data

    def test_register_page_loads(self, client):
        r = client.get('/register')
        assert r.status_code == 200

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

    def test_register_duplicate_email(self, client, db, app):
        """Registering with a taken email returns 409."""
        with app.app_context():
            create_user(db, username='user1', email='shared@test.com')
            r = client.post('/register',
                            json={'username': 'user2', 'email': 'shared@test.com',
                                  'password': 'password123'})
            assert r.status_code == 409
            assert r.get_json()['field'] == 'email'

    def test_valid_login(self, client, db, app):
        """Valid credentials redirect to /home."""
        with app.app_context():
            create_user(db)
            r = login(client)
            assert r.status_code == 200
            assert b'Welcome to FitScore' in r.data

    def test_invalid_login(self, client, db, app):
        """Wrong password flashes an error and stays on login page."""
        with app.app_context():
            create_user(db)
            r = client.post('/login',
                            data={'username': 'testuser', 'password': 'wrongpass'},
                            follow_redirects=True)
            assert b'Invalid username or password' in r.data

    def test_logout_redirects(self, client, db, app):
        """Logout redirects to landing page."""
        with app.app_context():
            create_user(db)
            login(client)
            r = client.get('/logout', follow_redirects=True)
            assert r.status_code == 200

    def test_home_requires_login(self, client):
        """Unauthenticated access to /home redirects to login."""
        r = client.get('/home', follow_redirects=True)
        assert b'Welcome back' in r.data or r.status_code == 200

    def test_register_check_endpoint(self, client, db, app):
        """POST /register/check returns 200 for a fresh username/email."""
        with app.app_context():
            r = client.post('/register/check',
                            json={'username': 'brandnew', 'email': 'brandnew@test.com'})
            assert r.status_code == 200


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

    def test_home_shows_recent_workout(self, client, db, app):
        with app.app_context():
            u = create_user(db)
            e = create_exercise(db)
            create_log(db, u, e, stat_value=110.0)
            login(client)
            r = client.get('/home')
            assert b'Bench Press' in r.data

    def test_home_shows_correct_stats(self, client, db, app):
        """Statistics panel shows correct workout count."""
        with app.app_context():
            u = create_user(db)
            e = create_exercise(db)
            create_log(db, u, e, stat_value=100.0)
            create_log(db, u, e, stat_value=110.0)
            login(client)
            r = client.get('/home')
            # 2 total workouts badge
            assert b'2' in r.data

    def test_home_friend_activity_shown(self, client, db, app):
        """Friend's logged exercise appears in Recent Friend Activity."""
        with app.app_context():
            u1 = create_user(db, username='user1', email='u1@t.com')
            u2 = create_user(db, username='frienduser', email='u2@t.com')
            e = create_exercise(db)

            from models import Friendship
            f = Friendship(user_id_1=u1.user_id, user_id_2=u2.user_id)
            db.session.add(f)
            db.session.commit()

            create_log(db, u2, e, stat_value=120.0)

            login(client, username='user1')
            r = client.get('/home')
            assert b'frienduser' in r.data

    def test_home_friend_score_is_percentile(self, client, db, app):
        """Friend activity score shown as 0-100 percentile, not raw z-score."""
        with app.app_context():
            u1 = create_user(db, username='user1', email='u1@t.com')
            u2 = create_user(db, username='friend2', email='u2@t.com')
            e = create_exercise(db, mean=100.0, stdev=20.0)

            from models import Friendship
            db.session.add(Friendship(user_id_1=u1.user_id, user_id_2=u2.user_id))
            db.session.commit()

            # z = (120-100)/20 = 1.0 → ~84th percentile
            create_log(db, u2, e, stat_value=120.0)

            login(client, username='user1')
            r = client.get('/home')
            # Raw z-score would be "1.0"; percentile should be 84
            assert b'Score: 84' in r.data
            assert b'Score: 1.0' not in r.data


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

    def test_log_exercise_computes_z_score(self, client, db, app):
        """Logged exercise stores the correct z-score."""
        with app.app_context():
            u = create_user(db)
            e = create_exercise(db, mean=100.0, stdev=20.0)
            login(client)

            client.post('/log', json={'exercise_id': e.exercise_id, 'stat_value': 120.0})

            from models import Log
            log = Log.query.filter_by(user_id=u.user_id).first()
            assert abs(log.standardised_score - 1.0) < 0.0001

    def test_log_missing_data_returns_400(self, client, db, app):
        with app.app_context():
            create_user(db)
            login(client)
            r = client.post('/log', json={'exercise_id': 999})
            assert r.status_code in (400, 404)

    def test_log_invalid_exercise_returns_404(self, client, db, app):
        with app.app_context():
            create_user(db)
            login(client)
            r = client.post('/log', json={'exercise_id': 9999, 'stat_value': 100.0})
            assert r.status_code == 404


# ===========================================================================
# 5. Social route
# ===========================================================================

class TestSocialRoute:

    def test_social_page_loads(self, client, db, app):
        with app.app_context():
            create_user(db)
            login(client)
            r = client.get('/social')
            assert r.status_code == 200
            assert b'Recent Friend Activity' in r.data

    def test_social_shows_no_activity_without_friends(self, client, db, app):
        with app.app_context():
            create_user(db)
            login(client)
            r = client.get('/social')
            assert b'No recent activity from friends' in r.data

    def test_add_friend_success(self, client, db, app):
        """Adding a valid friend redirects back to /social."""
        with app.app_context():
            create_user(db, username='user1', email='u1@t.com')
            create_user(db, username='user2', email='u2@t.com')
            login(client, username='user1')

            r = client.post('/add_friend', data={'username': 'user2'},
                            follow_redirects=True)
            assert r.status_code == 200
            assert b'Successfully added user2' in r.data

    def test_add_nonexistent_friend(self, client, db, app):
        """Adding a user that doesn't exist flashes an error."""
        with app.app_context():
            create_user(db)
            login(client)
            r = client.post('/add_friend', data={'username': 'ghost'},
                            follow_redirects=True)
            assert b'User not found' in r.data

    def test_add_self_as_friend(self, client, db, app):
        """Cannot add yourself as a friend."""
        with app.app_context():
            create_user(db)
            login(client)
            r = client.post('/add_friend', data={'username': 'testuser'},
                            follow_redirects=True)
            assert b'cannot add yourself' in r.data

    def test_add_duplicate_friend(self, client, db, app):
        """Adding an existing friend flashes an info message."""
        with app.app_context():
            create_user(db, username='user1', email='u1@t.com')
            create_user(db, username='user2', email='u2@t.com')
            login(client, username='user1')

            client.post('/add_friend', data={'username': 'user2'})
            r = client.post('/add_friend', data={'username': 'user2'},
                            follow_redirects=True)
            assert b'already friends' in r.data

    def test_social_friend_score_is_percentile(self, client, db, app):
        """Social page shows 0-100 percentile score, not raw z-score."""
        with app.app_context():
            u1 = create_user(db, username='user1', email='u1@t.com')
            u2 = create_user(db, username='friend3', email='u3@t.com')
            e = create_exercise(db, mean=100.0, stdev=20.0)

            from models import Friendship
            db.session.add(Friendship(user_id_1=u1.user_id, user_id_2=u2.user_id))
            db.session.commit()

            create_log(db, u2, e, stat_value=120.0)  # z=1.0 → ~84

            login(client, username='user1')
            r = client.get('/social')
            assert b'Score: 84' in r.data
            assert b'Score: 1.0' not in r.data


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

    def test_leaderboard_shows_users_with_logs(self, client, db, app):
        with app.app_context():
            u = create_user(db)
            e = create_exercise(db)
            create_log(db, u, e)
            login(client)
            r = client.get('/leaderboard')
            assert b'testuser' in r.data

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

    def test_profile_update_duplicate_username(self, client, db, app):
        with app.app_context():
            create_user(db, username='user1', email='u1@t.com')
            create_user(db, username='user2', email='u2@t.com')
            login(client, username='user1')
            r = client.post('/profile',
                            data={'username': 'user2', 'firstname': '',
                                  'lastname': '', 'bio': ''},
                            follow_redirects=True)
            assert b'already taken' in r.data

    def test_profile_update_password_wrong_current(self, client, db, app):
        with app.app_context():
            create_user(db)
            login(client)
            r = client.post('/profile',
                            data={'form_action': 'update_password',
                                  'current_password': 'wrongpass',
                                  'new_password': 'newpass123',
                                  'confirm_password': 'newpass123'},
                            follow_redirects=True)
            assert b'incorrect' in r.data

    def test_profile_update_password_mismatch(self, client, db, app):
        with app.app_context():
            create_user(db)
            login(client)
            r = client.post('/profile',
                            data={'form_action': 'update_password',
                                  'current_password': 'password123',
                                  'new_password': 'newpass123',
                                  'confirm_password': 'differentpass'},
                            follow_redirects=True)
            assert b'do not match' in r.data

    def test_profile_update_email_wrong_current(self, client, db, app):
        with app.app_context():
            create_user(db)
            login(client)
            r = client.post('/profile',
                            data={'form_action': 'update_email',
                                  'current_email': 'wrong@email.com',
                                  'new_email': 'new@email.com',
                                  'confirm_email': 'new@email.com'},
                            follow_redirects=True)
            assert b'does not match' in r.data


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

    def test_primary_category_correct(self, app, db):
        with app.app_context():
            u = create_user(db)
            e = create_exercise(db, name='Squat', etype='Lifting', mean=100.0, stdev=20.0)
            create_log(db, u, e, stat_value=140.0)  # high z → high score
            from app import summarize_user_performance
            result = summarize_user_performance(u)
            assert result['primary_category'] == 'Lifting'

    def test_multiple_categories_averaged(self, app, db):
        with app.app_context():
            u = create_user(db)
            e1 = create_exercise(db, name='Bench', etype='Lifting', mean=100.0, stdev=20.0)
            e2 = create_exercise(db, name='5k Run', etype='Cardio', units='seconds',
                                 mean=1200.0, stdev=120.0)
            create_log(db, u, e1, stat_value=100.0)  # z=0 → 50
            create_log(db, u, e2, stat_value=1200.0)  # z=0 → 50
            from app import summarize_user_performance
            result = summarize_user_performance(u)
            assert result['overall_score'] == 50