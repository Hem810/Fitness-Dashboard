
-- Create database schema for fitness dashboard
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    first_name TEXT,
    last_name TEXT,
    age INTEGER,
    gender TEXT,
    height_cm REAL,
    weight_kg REAL,
    activity_level TEXT,
    fitness_goals TEXT,
    injuries TEXT,
    experience_level TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    session_token TEXT UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE IF NOT EXISTS workout_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    duration_weeks INTEGER,
    ai_generated BOOLEAN DEFAULT TRUE,
    gemini_prompt TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE IF NOT EXISTS workout_days (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workout_plan_id INTEGER NOT NULL,
    day_number INTEGER NOT NULL,
    day_name TEXT,
    focus_area TEXT,
    FOREIGN KEY (workout_plan_id) REFERENCES workout_plans (id)
);

CREATE TABLE IF NOT EXISTS exercises (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT,
    muscle_groups TEXT,
    equipment TEXT,
    difficulty_level TEXT,
    instructions TEXT
);

CREATE TABLE IF NOT EXISTS workout_exercises (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workout_day_id INTEGER NOT NULL,
    exercise_id INTEGER NOT NULL,
    sets INTEGER,
    reps TEXT,
    weight_kg REAL,
    rest_seconds INTEGER,
    notes TEXT,
    FOREIGN KEY (workout_day_id) REFERENCES workout_days (id),
    FOREIGN KEY (exercise_id) REFERENCES exercises (id)
);

CREATE TABLE IF NOT EXISTS workout_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    plan_name TEXT NOT NULL,
    workout_day_id INTEGER NOT NULL,
    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    duration_minutes INTEGER,
    notes TEXT,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (plan_name) REFERENCES workout_plans (name),
    FOREIGN KEY (workout_day_id) REFERENCES workout_days (id)
);

CREATE TABLE IF NOT EXISTS exercise_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workout_log_id INTEGER NOT NULL,
    exercise_id INTEGER NOT NULL,
    sets_completed INTEGER,
    reps_completed TEXT,
    weight_used_kg REAL,
    perceived_exertion INTEGER,
    notes TEXT,
    FOREIGN KEY (workout_log_id) REFERENCES workout_logs (id),
    FOREIGN KEY (exercise_id) REFERENCES exercises (id)
);

CREATE TABLE IF NOT EXISTS progress_tracking (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    height_cm FLOAT NOT NULL,
    weight_kg FLOAT NOT NULL,
    date DATE DEFAULT CURRENT_DATE,
    FOREIGN KEY (user_id) REFERENCES users (id)
);


CREATE TABLE IF NOT EXISTS diet_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    calorie_target INTEGER,
    protein_target_g INTEGER,
    carb_target_g INTEGER,
    fat_target_g INTEGER,
    dietary_restrictions TEXT,
    ai_generated BOOLEAN DEFAULT TRUE,
    gemini_prompt TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE IF NOT EXISTS food_inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    food_name TEXT NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
CREATE TABLE IF NOT EXISTS meal_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    diet_plan_id INTEGER NOT NULL,
    day_number INTEGER NOT NULL,
    meal_type TEXT NOT NULL,
    recipe_name TEXT,
    ingredients TEXT,
    instructions TEXT,
    calories_per_serving INTEGER,
    protein_g REAL,
    carbs_g REAL,
    fat_g REAL,
    servings INTEGER DEFAULT 1,
    FOREIGN KEY (diet_plan_id) REFERENCES diet_plans (id)
);

CREATE TABLE IF NOT EXISTS meal_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    meal_plan_id INTEGER,
    meal_type TEXT NOT NULL,
    food_items TEXT,
    calories_consumed INTEGER,
    protein_g REAL,
    carbs_g REAL,
    fat_g REAL,
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (meal_plan_id) REFERENCES meal_plans (id)
);

CREATE TABLE IF NOT EXISTS shopping_lists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    diet_plan_id INTEGER,
    item_name TEXT NOT NULL,
    quantity REAL,
    unit TEXT,
    category TEXT,
    purchased BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (diet_plan_id) REFERENCES diet_plans (id)
);

