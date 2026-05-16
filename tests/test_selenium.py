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

import sys
import os
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

    def test_landing_has_get_started_button(self, driver, live_server):
        driver.get(live_server)
        btn = driver.find_element(By.PARTIAL_LINK_TEXT, 'Get Started')
        assert btn.is_displayed()

    def test_landing_navbar_brand(self, driver, live_server):
        driver.get(live_server)
        brand = driver.find_element(By.CLASS_NAME, 'navbar-brand')
        assert 'FitScore' in brand.text


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

    def test_invalid_login_shows_error(self, driver, live_server):
        driver.get(f'{live_server}/login')
        driver.find_element(By.ID, 'user').send_keys('selenium_user')
        driver.find_element(By.ID, 'password').send_keys('wrongpassword')
        driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        error = wait_for(driver, By.CLASS_NAME, 'field-error')
        assert 'Invalid' in error.text

    def test_logout_redirects(self, driver, live_server):
        login(driver, live_server)
        driver.get(f'{live_server}/logout')
        time.sleep(0.5)
        assert '/login' in driver.current_url or live_server == driver.current_url.rstrip('/')

    def test_protected_route_redirects_to_login(self, driver, live_server):
        driver.get(f'{live_server}/home')
        assert 'login' in driver.current_url


# ===========================================================================
# 3. Registration
# ===========================================================================

class TestRegistration:

    def test_register_page_loads(self, driver, live_server):
        driver.get(f'{live_server}/register')
        assert 'FitScore' in driver.title

    def test_register_shows_step_1(self, driver, live_server):
        driver.get(f'{live_server}/register')
        assert driver.find_element(By.ID, 'username').is_displayed()
        assert driver.find_element(By.ID, 'email').is_displayed()

    def test_register_step1_validation_short_username(self, driver, live_server):
        driver.get(f'{live_server}/register')
        driver.find_element(By.ID, 'username').send_keys('ab')
        driver.find_element(By.ID, 'email').send_keys('valid@email.com')
        driver.find_element(By.ID, 'next-btn').click()
        time.sleep(0.3)
        error = driver.find_element(By.ID, 'error-username')
        assert 'active' in error.get_attribute('class')

    def test_register_step1_validation_bad_email(self, driver, live_server):
        driver.get(f'{live_server}/register')
        driver.find_element(By.ID, 'username').send_keys('validuser')
        driver.find_element(By.ID, 'email').send_keys('notanemail')
        driver.find_element(By.ID, 'next-btn').click()
        time.sleep(0.3)
        error = driver.find_element(By.ID, 'error-email')
        assert 'active' in error.get_attribute('class')

    def test_register_full_flow(self, driver, live_server):
        """Complete two-step registration creates an account and lands on home."""
        driver.get(f'{live_server}/register')

        # Step 1
        driver.find_element(By.ID, 'username').send_keys('brand_new_user')
        driver.find_element(By.ID, 'email').send_keys('brandnew@test.com')
        driver.find_element(By.ID, 'next-btn').click()

        # Wait for step 2 to appear
        wait_for(driver, By.ID, 'password')

        # Step 2
        driver.find_element(By.ID, 'password').send_keys('Secure123!')
        driver.find_element(By.ID, 'confirm-password').send_keys('Secure123!')
        driver.find_element(By.ID, 'next-btn').click()

        # Should end up on home page
        wait_for(driver, By.CLASS_NAME, 'display-4')
        assert 'Welcome to FitScore' in driver.page_source


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

    def test_home_log_exercise_button_navigates(self, driver, live_server):
        login(driver, live_server)
        driver.get(f'{live_server}/home')
        driver.find_element(By.PARTIAL_LINK_TEXT, 'Log Your Exercise').click()
        wait_for(driver, By.CLASS_NAME, 'display-4')
        assert '/log' in driver.current_url

    def test_home_navbar_links_present(self, driver, live_server):
        login(driver, live_server)
        driver.get(f'{live_server}/home')
        links = [a.text for a in driver.find_elements(By.CLASS_NAME, 'navbar-link')]
        assert 'Home' in links
        assert 'Social' in links
        assert 'Leaderboard' in links

    def test_home_friend_activity_score_is_percentile(self, driver, live_server):
        """
        The seeded friend (friend_user) has z=0.5 → ~69th percentile.
        The page must not show the raw z-score.
        """
        login(driver, live_server)
        driver.get(f'{live_server}/home')
        source = driver.page_source
        # Raw z-score "0.5" should not appear as the displayed score
        assert 'Score: 0.5' not in source


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

    def test_clicking_lifting_shows_form(self, driver, live_server):
        login(driver, live_server)
        driver.get(f'{live_server}/log')
        driver.find_element(By.CSS_SELECTOR, '[data-sport="lifting"]').click()
        time.sleep(0.3)
        form = driver.find_element(By.CSS_SELECTOR, '.log-sport-form[data-sport="lifting"]')
        assert form.is_displayed()

    def test_clicking_running_shows_form(self, driver, live_server):
        login(driver, live_server)
        driver.get(f'{live_server}/log')
        driver.find_element(By.CSS_SELECTOR, '[data-sport="running"]').click()
        time.sleep(0.3)
        form = driver.find_element(By.CSS_SELECTOR, '.log-sport-form[data-sport="running"]')
        assert form.is_displayed()


# ===========================================================================
# 6. Social page
# ===========================================================================

class TestSocialPage:

    def test_social_page_loads(self, driver, live_server):
        login(driver, live_server)
        driver.get(f'{live_server}/social')
        assert 'Recent Friend Activity' in driver.page_source

    def test_social_shows_add_friend_form(self, driver, live_server):
        login(driver, live_server)
        driver.get(f'{live_server}/social')
        inp = driver.find_element(By.CSS_SELECTOR, 'input[name="username"]')
        assert inp.is_displayed()

    def test_social_shows_friend_activity(self, driver, live_server):
        """friend_user's Bench Press log should appear in the activity feed."""
        login(driver, live_server)
        driver.get(f'{live_server}/social')
        assert 'friend_user' in driver.page_source
        assert 'Bench Press' in driver.page_source

    def test_social_score_shown_as_percentile(self, driver, live_server):
        """Score displayed for friend activity must be a 0-100 integer, not raw z."""
        login(driver, live_server)
        driver.get(f'{live_server}/social')
        source = driver.page_source
        # friend_user: z=0.5 → 69; raw z-score "0.5" must not be the score shown
        assert 'Score: 0.5' not in source

    def test_social_ongoing_events_section(self, driver, live_server):
        login(driver, live_server)
        driver.get(f'{live_server}/social')
        assert 'Ongoing Events' in driver.page_source

    def test_social_friends_leaderboard_section(self, driver, live_server):
        login(driver, live_server)
        driver.get(f'{live_server}/social')
        assert "Friend" in driver.page_source and "Leaderboard" in driver.page_source

    def test_add_friend_nonexistent(self, driver, live_server):
        login(driver, live_server)
        driver.get(f'{live_server}/social')
        driver.find_element(By.CSS_SELECTOR, 'input[name="username"]').send_keys('ghost_user_xyz')
        driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        wait_for(driver, By.CLASS_NAME, 'alert')
        assert 'not found' in driver.page_source.lower() or 'User not found' in driver.page_source


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

    def test_leaderboard_filter_buttons_present(self, driver, live_server):
        login(driver, live_server)
        driver.get(f'{live_server}/leaderboard')
        btns = driver.find_elements(By.CLASS_NAME, 'lb-filter-btn')
        assert len(btns) >= 2

    def test_leaderboard_table_has_rows(self, driver, live_server):
        login(driver, live_server)
        driver.get(f'{live_server}/leaderboard')
        rows = driver.find_elements(By.CSS_SELECTOR, '.lb-table tbody tr')
        assert len(rows) >= 1


# ===========================================================================
# 8. Profile
# ===========================================================================

class TestProfile:

    def test_profile_page_loads(self, driver, live_server):
        login(driver, live_server)
        driver.get(f'{live_server}/profile')
        assert 'Profile' in driver.page_source

    def test_profile_shows_username(self, driver, live_server):
        login(driver, live_server)
        driver.get(f'{live_server}/profile')
        assert 'selenium_user' in driver.page_source

    def test_profile_nav_tabs_present(self, driver, live_server):
        login(driver, live_server)
        driver.get(f'{live_server}/profile')
        nav_links = driver.find_elements(By.CSS_SELECTOR, '.panel-nav a')
        labels = [a.text for a in nav_links]
        assert any('Profile' in l for l in labels)
        assert any('Security' in l for l in labels)
        assert any('Activity' in l for l in labels)

    def test_profile_activity_section_shows_logs(self, driver, live_server):
        login(driver, live_server)
        driver.get(f'{live_server}/profile?section=activity')
        assert 'Bench Press' in driver.page_source