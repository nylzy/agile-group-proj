from flask import render_template, request, redirect, url_for, flash
from flask import Flask, render_template
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user
from config import Config
from extensions import db, migrate

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
migrate.init_app(app, db)

from models import User, Exercise

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
    lifting = Exercise.query.filter_by(exercise_type="Lifting").all()
    cardio = Exercise.query.filter_by(exercise_type="Cardio").all()
    swimming = Exercise.query.filter_by(exercise_type="Swimming").all()
    return render_template('log.html', lifting=lifting, cardio=cardio, swimming=swimming)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    
    data = request.get_json()
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '').strip()

    # Duplicated username
    if User.query.filter_by(username=username).first():
        return {'field': 'username', 'success': False, 'message': 'Username already exists'}, 409

    # Duplicated email
    if User.query.filter_by(email=email).first():
        return {'field': 'email', 'success': False, 'message': 'Email already exists'}, 409

    # Create new user
    new_user = User(username=username, email=email, password=password)
    db.session.add(new_user)
    db.session.commit()

    login_user(new_user)

    return {}, 200

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