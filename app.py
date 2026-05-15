from datetime import datetime
import math
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user
from config import Config
from extensions import db, migrate
app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
migrate.init_app(app, db)

from models import User, Exercise, Log, Friendship

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
    
    # Calculate Performance Matrix Scores
    exercise_types = [r[0] for r in db.session.query(Exercise.exercise_type).distinct().all()]
    
    user_logs = Log.query.filter_by(user_id=current_user.user_id).order_by(Log.completed_on.desc()).all()
    latest_logs_per_exercise = {}
    for log in user_logs:
        if log.exercise_id not in latest_logs_per_exercise:
            latest_logs_per_exercise[log.exercise_id] = log
            
    performance_scores = {}
    for etype in exercise_types:
        type_logs = [log for log in latest_logs_per_exercise.values() if log.exercise.exercise_type == etype]
        if not type_logs:
            performance_scores[etype] = 0
        else:
            valid_scores = [log.standardised_score for log in type_logs if log.standardised_score is not None]
            if not valid_scores:
                performance_scores[etype] = 0
            else:
                avg_z = sum(valid_scores) / len(valid_scores)
                cdf = 0.5 * (1 + math.erf(avg_z / math.sqrt(2)))
                performance_scores[etype] = round(cdf * 100)
                
    performance_labels = list(performance_scores.keys())
    performance_data = list(performance_scores.values())
    
    # Calculate Statistics
    valid_logs = [log for log in user_logs if log.standardised_score is not None]    
    highest_z = max((log.standardised_score for log in valid_logs), default=None)
    cdf = 0.5 * (1 + math.erf(highest_z / math.sqrt(2)))
    highest_score = round(cdf * 100)


    stats = {
        'total_workouts': len(user_logs),
        'unique_exercises': len(set(log.exercise_id for log in user_logs)),
        'highest_score': highest_score,
        'total_friends': Friendship.query.filter_by(user_id_1=current_user.user_id).count()
    }
    
    # Get 2 recent logs from friends
    friendships = Friendship.query.filter_by(user_id_1=current_user.user_id).all()
    friend_ids = [f.user_id_2 for f in friendships]
    recent_friend_logs = Log.query.filter(Log.user_id.in_(friend_ids)).order_by(Log.completed_on.desc()).limit(2).all()
    
    for log in recent_friend_logs:
        cdf = 0.5 * (1 + math.erf(log.standardised_score / math.sqrt(2)))
        log.standardised_score = round(cdf * 100)
    
    return render_template('home.html', 
                           recent_log=recent_log,
                           performance_labels=performance_labels,
                           performance_data=performance_data,
                           stats=stats,
                           recent_friend_logs=recent_friend_logs)

@app.route('/leaderboard')
@login_required
def leaderboard():
    return render_template('leaderboard.html')

@app.route('/log', methods=['GET', 'POST'])
@login_required
def log():
    if request.method == 'POST':
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data received'}), 400

        exercise_id = data.get('exercise_id')
        stat_value = data.get('stat_value')

        if not exercise_id or stat_value is None:
            return jsonify({'error': 'Missing exercise or value'}), 400

        exercise = Exercise.query.get(exercise_id)
        if not exercise:
            return jsonify({'error': 'Exercise not found'}), 404

        z_score = None
        if exercise.stdev_statistic:
            z_score = (stat_value - exercise.mean_statistic) / exercise.stdev_statistic

        log_entry = Log(
            exercise_id=exercise.exercise_id,
            user_id=current_user.user_id,
            stat_value=stat_value,
            standardised_score=z_score,
            completed_on=datetime.utcnow()
        )
        db.session.add(log_entry)
        db.session.commit()

        return jsonify({'success': True, 'exercise': exercise.exercise_name, 'score': z_score})

    lifting = Exercise.query.filter_by(exercise_type="Lifting").all()
    cardio = Exercise.query.filter_by(exercise_type="Cardio").all()
    swimming = Exercise.query.filter_by(exercise_type="Swimming").all()
    cycling = Exercise.query.filter_by(exercise_type="Cycling").all()
    return render_template('log.html', lifting=lifting, cardio=cardio, swimming=swimming, cycling=cycling)

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