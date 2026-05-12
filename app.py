from flask import render_template, request, redirect, url_for, flash
from flask import Flask, render_template
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user
from config import Config
from extensions import db, migrate

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
migrate.init_app(app, db)

from models import User

# flask login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' 

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/home')
@login_required
def home():
    return render_template('home.html')

@app.route('/leaderboard')
@login_required
def leaderboard():
    return render_template('leaderboard.html')

@app.route('/log')
@login_required
def log():
    return render_template('log.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    # If a user is already logged in, send them to the dashboard
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Find the user in the SQLAlchemy database
        user = User.query.filter_by(username=username).first()

        # Check if user exists and the password matches the hash
        if user and user.check_password(password):
            login_user(user) # This logs the user in!
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password')

    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/social')
@login_required
def social():
    return render_template('social.html')

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
