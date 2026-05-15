from app import app, db
from models import User, Exercise, Log

def demonstrate_log_creation():
    # We must run database operations inside the Flask app context
    with app.app_context():
        print("--- Setting up demo data ---")
        
        # 1. Get or create a User
        user = User.query.filter_by(username="admin").first()
        if not user:
            user = User(username="admin", email="admin@admin.com")
            user.set_password("admin")
            db.session.add(user)
            db.session.commit()
            print(f"Created new user: {user.username}")
        else:
            print(f"Found existing user: {user.username}")

        # Create second user
        user2 = User.query.filter_by(username="user").first()
        if not user2:
            user2 = User(username="user", email="user@user.com")
            user2.set_password("user")
            db.session.add(user2)
            db.session.commit()
            print(f"Created new user: {user2.username}")
        else:
            print(f"Found existing user: {user2.username}")


        def create_log(user, exercise_name, stat_value):
            exercise_id = Exercise.query.filter_by(exercise_name=exercise_name).first().exercise_id
            
            exercise_mean = Exercise.query.filter_by(exercise_id=exercise_id).first().mean_statistic
            exercise_stdev = Exercise.query.filter_by(exercise_id=exercise_id).first().stdev_statistic
            
            z_score = (stat_value - exercise_mean) / exercise_stdev
            
            new_log = Log(
                user_id=user.user_id,
                exercise_id=exercise_id,
                stat_value=stat_value,
                standardised_score=z_score
            )
            db.session.add(new_log)
            db.session.commit()

        create_log(user, "200m Breaststroke", -520.0)
        create_log(user, "5k Run", -1200.0)
        create_log(user, "Bench Press", 60.0)
        create_log(user, "10km Cycling", -900.0)

        db.session.commit()
        

if __name__ == "__main__":
    demonstrate_log_creation()
