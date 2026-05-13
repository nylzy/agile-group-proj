from app import app
from extensions import db
from models import Exercise

with app.app_context():
    db.create_all()

    exercises = [
        # Cardio - (negative values for time-based)
        Exercise(exercise_name="400m Run",      exercise_type="Cardio",  units="seconds", mean_statistic=-65.0,   stdev_statistic=8.0),
        Exercise(exercise_name="5k Run",        exercise_type="Cardio",  units="seconds", mean_statistic=-1500.0, stdev_statistic=180.0),
        Exercise(exercise_name="10k Run",       exercise_type="Cardio",  units="seconds", mean_statistic=-3240.0, stdev_statistic=360.0),
    ]

    db.session.add_all(exercises)
    db.session.commit()
    print("Done!")