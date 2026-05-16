from datetime import datetime
import math
import re
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user
from config import Config
from extensions import db, migrate
import os

app = Flask(__name__)

if os.environ.get("TESTING") == "1":
    from tests.test_config import TestConfig
    app.config.from_object(TestConfig)
else:
    app.config.from_object(Config)

db.init_app(app)
migrate.init_app(app, db)

from models import User, Exercise, Log, Friendship, Event

# flask login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' 

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def z_to_percentile(z):
    """Convert a z-score to a 0-100 percentile score."""
    return round(0.5 * (1 + math.erf(z / math.sqrt(2))) * 100)


def summarize_user_performance(user):
    user_logs = Log.query.filter_by(user_id=user.user_id).order_by(Log.completed_on.desc()).all()
    latest_logs_per_exercise = {}
    for log in user_logs:
        if log.exercise_id not in latest_logs_per_exercise:
            latest_logs_per_exercise[log.exercise_id] = log

    category_scores = {}
    for log in latest_logs_per_exercise.values():
        exercise_type = log.exercise.exercise_type
        category_scores.setdefault(exercise_type, [])
        if log.standardised_score is not None:
            category_scores[exercise_type].append(log.standardised_score)

    averaged_scores = {}
    for etype, scores in category_scores.items():
        if scores:
            avg_z = sum(scores) / len(scores)
            averaged_scores[etype] = z_to_percentile(avg_z)
        else:
            averaged_scores[etype] = 0

    if averaged_scores:
        overall_score = sum(averaged_scores.values()) / len(averaged_scores)
        primary_category = max(averaged_scores, key=averaged_scores.get)
    else:
        overall_score = 0
        primary_category = 'N/A'

    return {
        'user_id': user.user_id,
        'username': user.username,
        'overall_score': round(overall_score, 2),
        'category_scores': averaged_scores,
        'total_sessions': len(user_logs),
        'primary_category': primary_category,
        'has_logs': bool(user_logs)
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/home')
@login_required
def home():
    recent_log = Log.query.filter_by(user_id=current_user.user_id).order_by(Log.completed_on.desc()).first()
    # if recent_log and recent_log.standardised_score is not None:
    #     cdf = 0.5 * (1 + math.erf(recent_log.standardised_score / math.sqrt(2)))
    #     recent_log.standardised_score = round(cdf * 100)

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
            # Use raw z-scores here, not converted percentiles
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
    highest_score = round(0.5 * (1 + math.erf(highest_z / math.sqrt(2))) * 100) if highest_z is not None else None


    friendships = Friendship.query.filter_by(user_id_1=current_user.user_id).all()
    friend_ids = [f.user_id_2 for f in friendships]

    stats = {
        'total_workouts':   len(user_logs),
        'unique_exercises': len(set(log.exercise_id for log in user_logs)),
        'highest_score':    highest_score,
        'total_friends':    len(friend_ids)
    }
    
    # Get 2 recent logs from friends
    recent_friend_logs = []
    friend_log_scores = {}
    if friend_ids:
        recent_friend_logs = Log.query.filter(Log.user_id.in_(friend_ids)).order_by(Log.completed_on.desc()).limit(2).all()
        friend_log_scores = {
            log.log_id: z_to_percentile(log.standardised_score)
            for log in recent_friend_logs
            if log.standardised_score is not None
        }

    # Calculate friends leaderboard (current user + friends)
    users_to_check = [current_user]
    if friend_ids:
        friends = User.query.filter(User.user_id.in_(friend_ids)).all()
        users_to_check.extend(friends)

    friends_leaderboard = [entry for user in users_to_check
                           if (entry := summarize_user_performance(user))['has_logs']]
    friends_leaderboard.sort(key=lambda x: x['overall_score'], reverse=True)
    friends_leaderboard = friends_leaderboard[:5]

    recent_log_score = z_to_percentile(recent_log.standardised_score) if recent_log and recent_log.standardised_score is not None else None

    return render_template('home.html',
                           recent_log=recent_log,
                           recent_log_score=recent_log_score,
                           performance_labels=performance_labels,
                           performance_data=performance_data,
                           stats=stats,
                           recent_friend_logs=recent_friend_logs,
                           friend_log_scores=friend_log_scores,
                           friends_leaderboard=friends_leaderboard)

@app.route('/leaderboard')
@login_required
def leaderboard():
    users = User.query.all()
    leaderboard_data = [entry for user in users
                        if (entry := summarize_user_performance(user))['has_logs']]
    leaderboard_data.sort(key=lambda x: x['overall_score'], reverse=True)
    return render_template('leaderboard.html', leaderboard=leaderboard_data)

@app.route('/log', methods=['GET', 'POST'])
@login_required
def log():
    if request.method == 'POST':
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data received'}), 400

        exercise_id = data.get('exercise_id')
        stat_value  = data.get('stat_value')

        if exercise_id is None or stat_value is None:
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

    lifting     = Exercise.query.filter_by(exercise_type="Lifting").all()
    cardio      = Exercise.query.filter_by(exercise_type="Cardio").all()
    swimming    = Exercise.query.filter_by(exercise_type="Swimming").all()
    cycling     = Exercise.query.filter_by(exercise_type="Cycling").all()
    plyometrics = Exercise.query.filter_by(exercise_type="Plyometrics").all()
    return render_template('log.html', lifting=lifting, cardio=cardio, swimming=swimming, cycling=cycling, plyometrics=plyometrics)

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
    
    data = request.get_json(silent=True) or {}
    username = data.get('username', '').strip()
    email    = data.get('email', '').strip()
    password = data.get('password', '').strip()

    if User.query.filter_by(username=username).first():
        return {'field': 'username', 'success': False, 'message': 'Username already exists'}, 409

    if User.query.filter_by(email=email).first():
        return {'field': 'email', 'success': False, 'message': 'Email already exists'}, 409

    # Create new user
    new_user = User(username=username, email=email)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    login_user(new_user)
    return {}, 200

@app.route('/register/check', methods=['POST'])
def check_registration_account():
    data = request.get_json(silent=True) or {}
    username = data.get('username', '').strip()
    email    = data.get('email', '').strip()

    if User.query.filter_by(username=username).first():
        return {'field': 'username', 'success': False, 'message': 'Username already exists'}, 409

    if User.query.filter_by(email=email).first():
        return {'field': 'email', 'success': False, 'message': 'Email already exists'}, 409

    return {'success': True}, 200

@app.route('/social')
@login_required
def social():
    friendships = Friendship.query.filter_by(user_id_1=current_user.user_id).all()
    friend_ids  = [f.user_id_2 for f in friendships]
    recent_friend_logs = Log.query.filter(Log.user_id.in_(friend_ids)).order_by(Log.completed_on.desc()).limit(10).all()

    # Calculate friends leaderboard (current user + friends)
    users_to_check = [current_user]
    if friend_ids:
        friends = User.query.filter(User.user_id.in_(friend_ids)).all()
        users_to_check.extend(friends)

    friends_leaderboard = [entry for user in users_to_check
                           if (entry := summarize_user_performance(user))['has_logs']]
    friends_leaderboard.sort(key=lambda x: x['overall_score'], reverse=True)
    friends_leaderboard = friends_leaderboard[:5]

    # Fetch active events
    current_time = datetime.utcnow()
    active_events = Event.query.filter(Event.start_date <= current_time, Event.end_date >= current_time).all()
    
    event_data = []
    for event in active_events:
        # Calculate progress
        completed_sessions = Log.query.join(Exercise).filter(
            Log.user_id == current_user.user_id,
            Exercise.exercise_type == event.target_exercise_type,
            Log.completed_on >= event.start_date,
            Log.completed_on <= event.end_date
        ).count()
        
        # Calculate true participants count
        active_participants = db.session.query(Log.user_id).join(Exercise).filter(
            Exercise.exercise_type == event.target_exercise_type,
            Log.completed_on >= event.start_date,
            Log.completed_on <= event.end_date
        ).distinct().count()
        
        progress_percentage = min(100, int((completed_sessions / event.target_sessions) * 100)) if event.target_sessions > 0 else 0
        days_left = (event.end_date - current_time).days
        
        event_data.append({
            'title': event.title,
            'participants_count': active_participants,
            'progress_percentage': progress_percentage,
            'days_left': days_left
        })

        friend_log_scores = {
            log.log_id: z_to_percentile(log.standardised_score)
            for log in recent_friend_logs
            if log.standardised_score is not None
        }

    return render_template('social.html', recent_friend_logs=recent_friend_logs, friends_leaderboard=friends_leaderboard, events=event_data, friend_log_scores=friend_log_scores)

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
        
    existing_friendship = Friendship.query.filter_by(user_id_1=current_user.user_id, user_id_2=friend.user_id).first()
    if existing_friendship:
        flash('You are already friends with this user.', 'info')
        return redirect(url_for('social'))
        
    new_friendship = Friendship(user_id_1=current_user.user_id, user_id_2=friend.user_id)
    db.session.add(new_friendship)
    db.session.commit()
    
    flash(f'Successfully added {friend.username} as a friend!', 'success')
    return redirect(url_for('social'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        form_action = request.form.get('form_action')

        if form_action == 'update_email':
            current_email = request.form.get('current_email', '').strip()
            new_email = request.form.get('new_email', '').strip()
            confirm_email = request.form.get('confirm_email', '').strip()
            email_pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'

            if current_email.lower() != current_user.email.lower():
                flash('Current email does not match your account email.', 'security-danger')
                return redirect(url_for('profile', section='security'))

            if not re.match(email_pattern, new_email):
                flash('Please enter a valid new email address.', 'security-danger')
                return redirect(url_for('profile', section='security'))

            if new_email.lower() != confirm_email.lower():
                flash('New email addresses do not match.', 'security-danger')
                return redirect(url_for('profile', section='security'))

            existing_user = User.query.filter(
                User.email == new_email,
                User.user_id != current_user.user_id
            ).first()
            if existing_user:
                flash('Email is already in use.', 'security-danger')
                return redirect(url_for('profile', section='security'))

            current_user.email = new_email
            db.session.commit()

            flash('Email updated successfully.', 'security-success')
            return redirect(url_for('profile', section='security'))

        if form_action == 'update_password':
            current_password = request.form.get('current_password', '')
            new_password = request.form.get('new_password', '')
            confirm_password = request.form.get('confirm_password', '')

            if not current_user.check_password(current_password):
                flash('Current password is incorrect.', 'security-danger')
                return redirect(url_for('profile', section='security'))

            if len(new_password) < 8:
                flash('New password must be at least 8 characters.', 'security-danger')
                return redirect(url_for('profile', section='security'))

            if new_password != confirm_password:
                flash('New passwords do not match.', 'security-danger')
                return redirect(url_for('profile', section='security'))

            current_user.set_password(new_password)
            db.session.commit()

            flash('Password updated successfully.', 'security-success')
            return redirect(url_for('profile', section='security'))

        username = request.form.get('username', '').strip()
        firstname = request.form.get('firstname', '').strip()
        lastname = request.form.get('lastname', '').strip()
        bio = request.form.get('bio', '').strip()

        if not username:
            flash('Username cannot be empty.', 'profile-danger')
            return redirect(url_for('profile'))

        existing_user = User.query.filter(
            User.username == username,
            User.user_id != current_user.user_id
        ).first()
        if existing_user:
            flash('Username is already taken.', 'profile-danger')
            return redirect(url_for('profile'))

        current_user.username = username
        current_user.firstname = firstname or None
        current_user.lastname = lastname or None
        current_user.bio = bio[:500] or None
        db.session.commit()

        flash('Profile details updated.', 'profile-success')
        return redirect(url_for('profile'))

    activity_logs = Log.query.filter_by(
        user_id=current_user.user_id
    ).order_by(Log.completed_on.desc()).all()
    activity_logs = [log for log in activity_logs if log.exercise is not None]
    activity_scores = {
        log.log_id: z_to_percentile(log.standardised_score)
        for log in activity_logs
        if log.standardised_score is not None
    }
    activity_types = sorted({
        log.exercise.exercise_type
        for log in activity_logs
    })

    return render_template(
        'profile.html',
        activity_logs=activity_logs,
        activity_scores=activity_scores,
        activity_types=activity_types
    )

if __name__ == '__main__':
    app.run(debug=True, port=5000)
