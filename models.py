from extensions import db
from datetime import datetime

from flask_login import UserMixin

class User(UserMixin, db.Model):
    __tablename__ = 'Users'
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    logs = db.relationship('Log', backref='user', lazy=True)

    def get_id(self):
        return str(self.user_id)

    def check_password(self, password):
        return self.password == password

class Exercise(db.Model):
    __tablename__ = 'Exercises'
    exercise_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    exercise_name = db.Column(db.String(50), nullable=False, unique=True)
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


def get_duplicate_exercise_names():
    """Return exercise names that appear more than once in the database."""
    from sqlalchemy import func

    duplicates = db.session.query(
        Exercise.exercise_name,
        func.count(Exercise.exercise_id).label('count')
    ).group_by(Exercise.exercise_name).having(func.count(Exercise.exercise_id) > 1).all()

    return [name for name, count in duplicates]


def remove_exact_duplicate_exercises():
    """Remove exact duplicate Exercise rows by exercise_name, keeping the oldest entry."""
    from sqlalchemy import func

    subq = db.session.query(
        Exercise.exercise_name,
        func.min(Exercise.exercise_id).label('keep_id')
    ).group_by(Exercise.exercise_name).having(func.count(Exercise.exercise_id) > 1).subquery()

    duplicates = db.session.query(Exercise, subq.c.keep_id).join(
        subq,
        Exercise.exercise_name == subq.c.exercise_name
    ).filter(Exercise.exercise_id != subq.c.keep_id).all()

    for duplicate, keep_id in duplicates:
        # Preserve any existing logs by re-pointing them to the kept exercise row.
        db.session.query(Log).filter_by(exercise_id=duplicate.exercise_id).update(
            {'exercise_id': keep_id}
        )
        db.session.delete(duplicate)

    db.session.commit()
    return len(duplicates)


def merge_exercises(name_to_remove, name_to_keep):
    """
    Merge two exercises that are duplicates but have different names
    (e.g. '5km Run' -> '5k Run').

    Re-points all logs from name_to_remove to name_to_keep, then
    deletes the unwanted exercise row.

    Returns True on success, False if either exercise is not found.

    Usage:
        merge_exercises('5km Run', '5k Run')
    """
    exercise_to_remove = Exercise.query.filter_by(exercise_name=name_to_remove).first()
    exercise_to_keep   = Exercise.query.filter_by(exercise_name=name_to_keep).first()

    if not exercise_to_remove or not exercise_to_keep:
        return False

    # Re-point every log that references the exercise being removed.
    db.session.query(Log).filter_by(exercise_id=exercise_to_remove.exercise_id).update(
        {'exercise_id': exercise_to_keep.exercise_id}
    )

    db.session.delete(exercise_to_remove)
    db.session.commit()
    return True


def delete_exercise_by_name(exercise_name):
    """
    Delete a single exercise by exact exercise_name.
    Any logs referencing this exercise will also be deleted (cascade).
    If you want to preserve logs, use merge_exercises() instead.
    """
    exercise = Exercise.query.filter_by(exercise_name=exercise_name).first()
    if not exercise:
        return False

    # Delete associated logs first to avoid FK constraint violations.
    db.session.query(Log).filter_by(exercise_id=exercise.exercise_id).delete()
    db.session.delete(exercise)
    db.session.commit()
    return True




"""
CREATE TABLE IF NOT EXISTS Users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) NOT NULL,
    password VARCHAR(50) NOT NULL,
    email VARCHAR(50) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Trigger to handle updated_at for Users table automatically
CREATE TRIGGER IF NOT EXISTS trg_users_updated_at 
AFTER UPDATE ON Users
BEGIN
    UPDATE Users SET updated_at = CURRENT_TIMESTAMP WHERE user_id = NEW.user_id;
END;

CREATE TABLE IF NOT EXISTS Exercises (
    exercise_id INTEGER PRIMARY KEY AUTOINCREMENT,
    exercise_name VARCHAR(50) NOT NULL,
    exercise_type VARCHAR(50) NOT NULL,
    units VARCHAR(50) NOT NULL,
    mean_statistic FLOAT NOT NULL, -- use negative value for time-based exercises
    stdev_statistic FLOAT NOT NULL
);

CREATE TABLE IF NOT EXISTS Logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    exercise_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    stat_value FLOAT NOT NULL, -- use negative value for time-based exercises
    standardised_score FLOAT, -- Allow NULL so the trigger can calculate and set it
    completed_on DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (exercise_id) REFERENCES Exercises(exercise_id),
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
);

-- Trigger to calculate and update standardised_score after a log is inserted
CREATE TRIGGER IF NOT EXISTS trg_calculate_z_score 
AFTER INSERT ON Logs
BEGIN
    UPDATE Logs
    SET standardised_score = (
        SELECT (NEW.stat_value - mean_statistic) / stdev_statistic 
        FROM Exercises 
        WHERE exercise_id = NEW.exercise_id
    )
    WHERE log_id = NEW.log_id;
END;

CREATE TABLE IF NOT EXISTS Friendships (
    friendship_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id_1 INTEGER NOT NULL,
    user_id_2 INTEGER NOT NULL,
    FOREIGN KEY (user_id_1) REFERENCES Users(user_id),
    FOREIGN KEY (user_id_2) REFERENCES Users(user_id)
);
"""