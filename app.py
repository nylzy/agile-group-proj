from flask import render_template, request, redirect, url_for, flash
from flask import Flask, render_template
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

from models import User, Log, Friendship

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
    recent_log = Log.query.filter_by(user_id=current_user.user_id).order_by(Log.completed_on.desc()).first()
    return render_template('home.html', recent_log=recent_log)

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
    # Get all friends of the current user
    friendships = Friendship.query.filter_by(user_id_1=current_user.user_id).all()
    friend_ids = [f.user_id_2 for f in friendships]
    
    # Get the last 10 logs from those friends
    recent_friend_logs = Log.query.filter(Log.user_id.in_(friend_ids)).order_by(Log.completed_on.desc()).limit(10).all()
    
    return render_template('social.html', recent_friend_logs=recent_friend_logs)

@app.route('/add_friend', methods=['POST'])
@login_required
def add_friend():
    friend_username = request.form.get('username')
    if not friend_username:
        flash('Please enter a username.', 'warning')
        return redirect(url_for('social'))
    
    friend = User.query.filter_by(username=friend_username).first()
    
    if not friend:
        flash('User not found.', 'danger')
        return redirect(url_for('social'))
        
    if friend.user_id == current_user.user_id:
        flash('You cannot add yourself as a friend.', 'warning')
        return redirect(url_for('social'))
        
    # Check if already friends
    existing_friendship = Friendship.query.filter_by(user_id_1=current_user.user_id, user_id_2=friend.user_id).first()
    if existing_friendship:
        flash('You are already friends with this user.', 'info')
        return redirect(url_for('social'))
        
    # Create friendship
    new_friendship = Friendship(user_id_1=current_user.user_id, user_id_2=friend.user_id)
    db.session.add(new_friendship)
    db.session.commit()
    
    flash(f'Successfully added {friend.username} as a friend!', 'success')
    return redirect(url_for('social'))

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
