from app import app
from extensions import db
from models import Exercise

with app.app_context():
    db.create_all()

    exercises = [
        # Lifting
        Exercise(exercise_name="Bench Press", exercise_type="Lifting", units="kg", mean_statistic=60.0, stdev_statistic=10.0),
        Exercise(exercise_name="Squat", exercise_type="Lifting", units="kg", mean_statistic=80.0, stdev_statistic=15.0),
        Exercise(exercise_name="Deadlift", exercise_type="Lifting", units="kg", mean_statistic=100.0, stdev_statistic=20.0),

        # Cardio - (negative values for time-based)
        Exercise(exercise_name="400m Run", exercise_type="Cardio",  units="seconds", mean_statistic=-65.0, stdev_statistic=8.0),
        Exercise(exercise_name="5k Run", exercise_type="Cardio",  units="seconds", mean_statistic=-1500.0, stdev_statistic=180.0),
        Exercise(exercise_name="10k Run", exercise_type="Cardio",  units="seconds", mean_statistic=-3240.0, stdev_statistic=360.0),
    ]

    for exercise in exercises:
        existing_exercise = Exercise.query.filter_by(exercise_name=exercise.exercise_name).first()
        if not existing_exercise:
            db.session.add(exercise)
            
    db.session.commit()
    print("Done!")