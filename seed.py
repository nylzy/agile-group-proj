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

        # Swimming - (negative values for time-based, sourced from recreational adult population averages)
        Exercise(exercise_name="50m Freestyle",    exercise_type="Swimming", units="seconds", mean_statistic=-90.0,   stdev_statistic=20.0),
        Exercise(exercise_name="100m Freestyle",   exercise_type="Swimming", units="seconds", mean_statistic=-120.0,  stdev_statistic=28.0),
        Exercise(exercise_name="200m Freestyle",   exercise_type="Swimming", units="seconds", mean_statistic=-265.0,  stdev_statistic=55.0),
        Exercise(exercise_name="400m Freestyle",   exercise_type="Swimming", units="seconds", mean_statistic=-540.0,  stdev_statistic=115.0),
        Exercise(exercise_name="800m Freestyle",   exercise_type="Swimming", units="seconds", mean_statistic=-1110.0, stdev_statistic=245.0),
        Exercise(exercise_name="1500m Freestyle",  exercise_type="Swimming", units="seconds", mean_statistic=-2100.0, stdev_statistic=475.0),
        Exercise(exercise_name="50m Backstroke",   exercise_type="Swimming", units="seconds", mean_statistic=-100.0,  stdev_statistic=22.0),
        Exercise(exercise_name="100m Backstroke",  exercise_type="Swimming", units="seconds", mean_statistic=-210.0,  stdev_statistic=45.0),
        Exercise(exercise_name="200m Backstroke",  exercise_type="Swimming", units="seconds", mean_statistic=-440.0,  stdev_statistic=95.0),
        Exercise(exercise_name="50m Breaststroke", exercise_type="Swimming", units="seconds", mean_statistic=-120.0,  stdev_statistic=27.0),
        Exercise(exercise_name="100m Breaststroke",exercise_type="Swimming", units="seconds", mean_statistic=-255.0,  stdev_statistic=57.0),
        Exercise(exercise_name="200m Breaststroke",exercise_type="Swimming", units="seconds", mean_statistic=-530.0,  stdev_statistic=120.0),
        Exercise(exercise_name="50m Butterfly",    exercise_type="Swimming", units="seconds", mean_statistic=-95.0,   stdev_statistic=21.0),
        Exercise(exercise_name="100m Butterfly",   exercise_type="Swimming", units="seconds", mean_statistic=-200.0,  stdev_statistic=45.0),
        Exercise(exercise_name="200m Butterfly",   exercise_type="Swimming", units="seconds", mean_statistic=-430.0,  stdev_statistic=110.0),

        # Cycling - (negative values for time-based, recreational adult averages)
        Exercise(exercise_name="10km Cycling",   exercise_type="Cycling", units="seconds", mean_statistic=-1200.0,  stdev_statistic=180.0),
        Exercise(exercise_name="20km Cycling",   exercise_type="Cycling", units="seconds", mean_statistic=-2700.0,  stdev_statistic=360.0),
        Exercise(exercise_name="40km Cycling",   exercise_type="Cycling", units="seconds", mean_statistic=-5400.0,  stdev_statistic=720.0),
        Exercise(exercise_name="100km Cycling",  exercise_type="Cycling", units="seconds", mean_statistic=-14400.0, stdev_statistic=1800.0),
        Exercise(exercise_name="160km Cycling",  exercise_type="Cycling", units="seconds", mean_statistic=-25200.0, stdev_statistic=3600.0),
    ]

    for exercise in exercises:
        existing_exercise = Exercise.query.filter_by(exercise_name=exercise.exercise_name).first()
        if not existing_exercise:
            db.session.add(exercise)
            
    db.session.commit()
    print("Done!")