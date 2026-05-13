from app import app, db
from models import User, Exercise, Log

def demonstrate_log_creation():
    # We must run database operations inside the Flask app context
    with app.app_context():
        print("--- Setting up demo data ---")
        
        # 1. Get or create a User
        user = User.query.filter_by(username="admin").first()
        if not user:
            user = User(username="admin", email="admin@admin.com", password="admin")
            db.session.add(user)
            db.session.commit()
            print(f"Created new user: {user.username}")
        else:
            print(f"Found existing user: {user.username}")

        # Create second user
        user2 = User.query.filter_by(username="user").first()
        if not user2:
            user2 = User(username="user", email="user@user.com", password="user")
            db.session.add(user2)
            db.session.commit()
            print(f"Created new user: {user2.username}")
        else:
            print(f"Found existing user: {user2.username}")

        # 2. Get or create an Exercise
        # Let's say we are tracking a 5km run. 
        # The models note says "use negative value for time-based exercises", meaning a lower time is better.
        # For example, mean time is -1500 seconds (25 mins), stdev is 180 seconds (3 mins).
        exercise = Exercise.query.filter_by(exercise_name="5km Run").first()
        if not exercise:
            exercise = Exercise(
                exercise_name="5km Run",
                exercise_type="Cardio",
                units="seconds",
                mean_statistic=-1500.0, 
                stdev_statistic=180.0
            )
            db.session.add(exercise)
            db.session.commit()
            print(f"Created new exercise: {exercise.exercise_name}")

        # 3. Create a Log and calculate the standardised score
        # Let's say the user ran it in 22 minutes (1320 seconds).
        # We store it as -1320 because lower time is better, which makes the standardised score calculation work correctly.
        user_stat_value = -1320.0 
        
        # Calculate the Standardised Score (Z-Score)
        # Formula: (Value - Mean) / Standard Deviation
        z_score = (user_stat_value - exercise.mean_statistic) / exercise.stdev_statistic
        
        new_log = Log(
            user_id=user.user_id,
            exercise_id=exercise.exercise_id,
            stat_value=user_stat_value,
            standardised_score=z_score
        )
        
        db.session.add(new_log)

        new_log = Log(
            user_id=user2.user_id,
            exercise_id=exercise.exercise_id,
            stat_value=user_stat_value,
            standardised_score=z_score
        )
        
        db.session.add(new_log)

        db.session.commit()

        print("\n--- Log Successfully Created ---")
        print(f"Athlete: {user.username}")
        print(f"Exercise: {exercise.exercise_name}")
        print(f"Stat Value Recorded: {user_stat_value} {exercise.units}")
        print(f"Calculated Standardised Score: +{z_score:.2f}")
        print("Note: A positive score here means they performed better than the mean!")

        

if __name__ == "__main__":
    demonstrate_log_creation()
