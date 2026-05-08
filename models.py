from app import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'Users'
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    logs = db.relationship('Log', backref='user', lazy=True)

class Exercise(db.Model):
    __tablename__ = 'Exercises'
    exercise_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    exercise_name = db.Column(db.String(50), nullable=False)
    exercise_type = db.Column(db.String(50), nullable=False)
    units = db.Column(db.String(50), nullable=False)
    mean_statistic = db.Column(db.Float, nullable=False) # use negative value for time-based exercises
    stdev_statistic = db.Column(db.Float, nullable=False)

    logs = db.relationship('Log', backref='exercise', lazy=True)

class Log(db.Model):
    __tablename__ = 'Logs'
    log_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    exercise_id = db.Column(db.Integer, db.ForeignKey('Exercises.exercise_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('Users.user_id'), nullable=False)
    stat_value = db.Column(db.Float, nullable=False) # use negative value for time-based exercises
    standardised_score = db.Column(db.Float, nullable=True)
    completed_on = db.Column(db.DateTime, default=datetime.utcnow)

class Friendship(db.Model):
    __tablename__ = 'Friendships'
    friendship_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id_1 = db.Column(db.Integer, db.ForeignKey('Users.user_id'), nullable=False)
    user_id_2 = db.Column(db.Integer, db.ForeignKey('Users.user_id'), nullable=False)
