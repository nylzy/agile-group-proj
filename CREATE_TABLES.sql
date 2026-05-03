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

