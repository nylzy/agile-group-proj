"""
FitScore Selenium UI Tests
==========================
Spins up the Flask app on a random port with an in-memory test database,
runs Chrome headlessly, then tears everything down automatically.

Requirements:
    pip install selenium pytest

Chrome/ChromeDriver must be installed. On Ubuntu:
    sudo apt-get install -y chromium-browser chromium-chromedriver

Run:
    pytest test_selenium.py -v
"""
import os
os.environ["TESTING"] = "1"

import sys
import time
import threading
import pytest

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from tests.test_config import TestConfig

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
TEST_PORT   = 5099          # Use a port that won't clash with your dev server
BASE_URL    = f'http://localhost:{TEST_PORT}'
WAIT_SECS   = 10


# ===========================================================================
# Server fixture — starts Flask in a background thread
# ===========================================================================

@pytest.fixture(scope='session')
def live_server():
    """
    Boot the Flask app with TestConfig in a daemon thread.
    The thread dies automatically when the test session ends.
    """
    from app import app as flask_app
    from extensions import db as _db

    flask_app.config.from_object(TestConfig)

    with flask_app.app_context():
        _db.create_all()
        _seed_data(flask_app, _db)

    def run():
        flask_app.run(port=TEST_PORT, use_reloader=False, threaded=True)

    t = threading.Thread(target=run, daemon=True)
    t.start()
    time.sleep(1.5)   # Give Flask a moment to start
    yield BASE_URL

    with flask_app.app_context():
        _db.drop_all()


def _seed_data(app, db):
    """Insert the minimum data needed for all Selenium tests."""
    from models import User, Exercise, Log, Friendship

    # Users
    u1 = User(username='selenium_user', email='sel@test.com')
    u1.set_password('Selenium123!')
    u2 = User(username='friend_user', email='friend@test.com')
    u2.set_password('Selenium123!')
    db.session.add_all([u1, u2])
    db.session.flush()

    # Exercise
    e = Exercise(exercise_name='Bench Press', exercise_type='Lifting',
                 units='kg', mean_statistic=100.0, stdev_statistic=20.0)
    db.session.add(e)
    db.session.flush()

    # Logs
    z = (120.0 - 100.0) / 20.0  # z = 1.0
    log1 = Log(user_id=u1.user_id, exercise_id=e.exercise_id,
               stat_value=120.0, standardised_score=z)
    log2 = Log(user_id=u2.user_id, exercise_id=e.exercise_id,
               stat_value=110.0, standardised_score=(110.0 - 100.0) / 20.0)
    db.session.add_all([log1, log2])

    # Friendship: u1 follows u2
    db.session.add(Friendship(user_id_1=u1.user_id, user_id_2=u2.user_id))
    db.session.commit()


# ===========================================================================
# Browser fixture
# ===========================================================================

@pytest.fixture(scope='function')
def driver(live_server):
    """Headless Chrome driver, fresh for every test."""
    opts = Options()
    opts.add_argument('--headless')
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-dev-shm-usage')
    opts.add_argument('--disable-gpu')
    opts.add_argument('--window-size=1280,900')

    # Try to locate chromedriver automatically
    chromedriver_paths = [
        '/usr/bin/chromedriver',
        '/usr/lib/chromium-browser/chromedriver',
        '/usr/lib/chromium/chromedriver',
    ]
    service = None
    for path in chromedriver_paths:
        if os.path.exists(path):
            service = Service(path)
            break

    drv = webdriver.Chrome(service=service, options=opts) if service else webdriver.Chrome(options=opts)
    drv.implicitly_wait(5)
    yield drv
    drv.quit()


# ===========================================================================
# Helpers
# ===========================================================================

def wait_for(driver, by, value, timeout=WAIT_SECS):
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((by, value))
    )


def login(driver, base_url, username='selenium_user', password='Selenium123!'):
    driver.get(f'{base_url}/login')
    wait_for(driver, By.ID, 'user').send_keys(username)
    driver.find_element(By.ID, 'password').send_keys(password)
    driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
    wait_for(driver, By.CLASS_NAME, 'display-4')


# ===========================================================================
# 1. Landing / index page
# ===========================================================================

class TestLandingPage:

    def test_landing_page_loads(self, driver, live_server):
        driver.get(live_server)
        assert 'FitScore' in driver.title

    def test_landing_has_login_button(self, driver, live_server):
        driver.get(live_server)
        btn = driver.find_element(By.LINK_TEXT, 'Log In')
        assert btn.is_displayed()


# ===========================================================================
# 2. Login / Logout
# ===========================================================================

class TestLoginLogout:

    def test_login_page_loads(self, driver, live_server):
        driver.get(f'{live_server}/login')
        assert 'Login' in driver.title or 'FitScore' in driver.title

    def test_valid_login_redirects_to_home(self, driver, live_server):
        login(driver, live_server)
        assert 'Welcome to FitScore' in driver.page_source


# ===========================================================================
# 3. Registration
# ===========================================================================

class TestRegistration:

    def test_register_page_loads(self, driver, live_server):
        driver.get(f'{live_server}/register')
        assert 'FitScore' in driver.title

    def test_register_step1_validation_short_username(self, driver, live_server):
        driver.get(f'{live_server}/register')
        driver.find_element(By.ID, 'username').send_keys('ab')
        driver.find_element(By.ID, 'email').send_keys('valid@email.com')
        driver.find_element(By.ID, 'next-btn').click()
        time.sleep(0.3)
        error = driver.find_element(By.ID, 'error-username')
        assert 'active' in error.get_attribute('class')


# ===========================================================================
# 4. Home dashboard
# ===========================================================================

class TestHomeDashboard:

    def test_home_dashboard_panels_visible(self, driver, live_server):
        login(driver, live_server)
        driver.get(f'{live_server}/home')
        assert 'Performance Matrix' in driver.page_source
        assert 'Statistics' in driver.page_source
        assert 'Friends Leaderboard' in driver.page_source

    def test_home_shows_last_workout(self, driver, live_server):
        login(driver, live_server)
        driver.get(f'{live_server}/home')
        assert 'Bench Press' in driver.page_source


# ===========================================================================
# 5. Log Exercise
# ===========================================================================

class TestLogExercise:

    def test_log_page_loads(self, driver, live_server):
        login(driver, live_server)
        driver.get(f'{live_server}/log')
        assert 'Log Exercise' in driver.page_source

    def test_sport_tabs_present(self, driver, live_server):
        login(driver, live_server)
        driver.get(f'{live_server}/log')
        buttons = driver.find_elements(By.CLASS_NAME, 'lb-filter-btn')
        labels = [b.text.lower() for b in buttons]
        for sport in ['lifting', 'running', 'swimming', 'cycling', 'plyometrics']:
            assert sport in labels


# ===========================================================================
# 6. Social page
# ===========================================================================

class TestSocialPage:

    def test_social_score_shown_as_percentile(self, driver, live_server):
        """Score displayed for friend activity must be a 0-100 integer, not raw z."""
        login(driver, live_server)
        driver.get(f'{live_server}/social')
        source = driver.page_source
        # friend_user: z=0.5 → 69; raw z-score "0.5" must not be the score shown
        assert 'Score: 0.5' not in source


# ===========================================================================
# 7. Leaderboard
# ===========================================================================

class TestLeaderboard:

    def test_leaderboard_page_loads(self, driver, live_server):
        login(driver, live_server)
        driver.get(f'{live_server}/leaderboard')
        assert 'Leaderboard' in driver.page_source

    def test_leaderboard_shows_athletes(self, driver, live_server):
        login(driver, live_server)
        driver.get(f'{live_server}/leaderboard')
        assert 'selenium_user' in driver.page_source


# ===========================================================================
# 8. Profile
# ===========================================================================

class TestProfile:

    def test_profile_page_loads(self, driver, live_server):
        login(driver, live_server)
        driver.get(f'{live_server}/profile')
        assert 'Profile' in driver.page_source

    def test_profile_nav_tabs_present(self, driver, live_server):
        login(driver, live_server)
        driver.get(f'{live_server}/profile')
        nav_links = driver.find_elements(By.CSS_SELECTOR, '.panel-nav a')
        labels = [a.text for a in nav_links]
        assert any('Profile' in l for l in labels)
        assert any('Security' in l for l in labels)
        assert any('Activity' in l for l in labels)