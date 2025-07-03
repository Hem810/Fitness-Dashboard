"""
Database management module for the Fitness Dashboard application.
Handles SQLite database operations, connection management, and data persistence.
"""

import sqlite3
import os
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Tuple
import logging
import pandas as pd
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages database connections and operations for the fitness dashboard."""

    def __init__(self, db_path: str = "database/fitness_app.db"):
        """
        Initialize the database manager.
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.ensure_database_exists()

    def ensure_database_exists(self) -> None:
        """Create the database and tables if they don't exist."""
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            with self.get_connection() as conn:
                # Read and execute schema
                schema_path = "database/schema.sql"
                if os.path.exists(schema_path):
                    with open(schema_path, 'r') as f:
                        schema = f.read()
                    conn.executescript(schema)
                    logger.info("Database schema created successfully")
                else:
                    logger.warning(f"Schema file not found: {schema_path}")
                    self._create_default_schema(conn)
        except Exception as e:
            logger.error(f"Error creating database: {e}")
            raise

    def _create_default_schema(self, conn):
        """Create default schema if schema.sql is not found."""
        default_schema = """
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
        """
        conn.executescript(default_schema)

    def get_connection(self) -> sqlite3.Connection:
        """
        Get a database connection with row factory enabled.
        Returns:
            SQLite connection object
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def hash_password(self, password: str) -> str:
        """
        Hash a password using SHA-256 with salt.
        Args:
            password: Plain text password
        Returns:
            Hashed password string
        """
        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return f"{salt}:{password_hash}"

    def verify_password(self, password: str, stored_hash: str) -> bool:
        """
        Verify a password against a stored hash.
        Args:
            password: Plain text password to verify
            stored_hash: Stored password hash
        Returns:
            True if password matches, False otherwise
        """
        try:
            salt, password_hash = stored_hash.split(':')
            return hashlib.sha256((password + salt).encode()).hexdigest() == password_hash
        except ValueError:
            return False

    def create_user(self, username: str, email: str, password: str,
                    user_data: Optional[Dict[str, Any]] = None) -> Optional[int]:
        """
        Create a new user account.
        Args:
            username: Unique username
            email: User email address
            password: Plain text password
            user_data: Optional additional user data
        Returns:
            User ID if successful, None otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if user already exists
                cursor.execute(
                    "SELECT id FROM users WHERE username = ? OR email = ?",
                    (username, email)
                )
                
                if cursor.fetchone():
                    logger.warning(f"User already exists: {username} or {email}")
                    return None

                # Create user
                password_hash = self.hash_password(password)
                user_data = user_data or {}
                
                cursor.execute("""
                    INSERT INTO users (username, email, password_hash, first_name,
                                     last_name, age, gender, height_cm, weight_kg,
                                     activity_level, fitness_goals, injuries, experience_level)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    username, email, password_hash,
                    user_data.get('first_name'),
                    user_data.get('last_name'),
                    user_data.get('age'),
                    user_data.get('gender'),
                    user_data.get('height_cm'),
                    user_data.get('weight_kg'),
                    user_data.get('activity_level'),
                    user_data.get('fitness_goals'),
                    user_data.get('injuries'),
                    user_data.get('experience_level')
                ))

                user_id = cursor.lastrowid
                logger.info(f"User created successfully: {username} (ID: {user_id})")
                return user_id

        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return None

    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate a user with username and password.
        Args:
            username: Username or email
            password: Plain text password
        Returns:
            User data dict if successful, None otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM users WHERE username = ? OR email = ?",
                    (username, username)
                )

                user = cursor.fetchone()
                if user and self.verify_password(password, user['password_hash']):
                    logger.info(f"User authenticated: {username}")
                    return dict(user)
                else:
                    logger.warning(f"Authentication failed: {username}")
                    return None

        except Exception as e:
            logger.error(f"Error authenticating user: {e}")
            return None

    def create_session(self, user_id: int, duration_hours: int = 24) -> Optional[str]:
        """
        Create a user session.
        Args:
            user_id: User ID
            duration_hours: Session duration in hours
        Returns:
            Session token if successful, None otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                session_token = secrets.token_urlsafe(32)
                expires_at = datetime.now() + timedelta(hours=duration_hours)

                cursor.execute("""
                    INSERT INTO user_sessions (user_id, session_token, expires_at)
                    VALUES (?, ?, ?)
                """, (user_id, session_token, expires_at))

                logger.info(f"Session created for user {user_id}")
                return session_token

        except Exception as e:
            logger.error(f"Error creating session: {e}")
            return None

    def validate_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """
        Validate a session token.
        Args:
            session_token: Session token to validate
        Returns:
            User data if session is valid, None otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT u.* FROM users u
                    JOIN user_sessions s ON u.id = s.user_id
                    WHERE s.session_token = ? AND s.expires_at > ?
                """, (session_token, datetime.now()))

                user = cursor.fetchone()
                if user:
                    return dict(user)
                return None

        except Exception as e:
            logger.error(f"Error validating session: {e}")
            return None

    def save_workout_plan(self, user_id: int, plan_data: Dict[str, Any]) -> Optional[int]:
        """
        Save a workout plan to the database.
        Args:
            user_id: User ID
            plan_data: Workout plan data
        Returns:
            Workout plan ID if successful, None otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Insert workout plan
                cursor.execute("""
                    INSERT INTO workout_plans (user_id, name, description, duration_weeks,
                                             ai_generated, gemini_prompt)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    user_id,
                    plan_data.get('name'),
                    plan_data.get('description'),
                    plan_data.get('duration_weeks'),
                    plan_data.get('ai_generated', True),
                    plan_data.get('gemini_prompt')
                ))

                workout_plan_id = cursor.lastrowid

                # Insert workout days and exercises
                for day_data in plan_data.get('days', []):
                    cursor.execute("""
                        INSERT INTO workout_days (workout_plan_id, day_number, day_name, focus_area)
                        VALUES (?, ?, ?, ?)
                    """, (
                        workout_plan_id,
                        day_data.get('day_number'),
                        day_data.get('day_name'),
                        day_data.get('focus_area')
                    ))

                    day_id = cursor.lastrowid

                    for exercise_data in day_data.get('exercises', []):
                        # Insert or get exercise
                        cursor.execute("""
                            INSERT OR IGNORE INTO exercises (name, category, muscle_groups,
                                                           equipment, difficulty_level, instructions)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (
                            exercise_data.get('name'),
                            exercise_data.get('category'),
                            exercise_data.get('muscle_groups'),
                            exercise_data.get('equipment'),
                            exercise_data.get('difficulty_level'),
                            exercise_data.get('instructions')
                        ))

                        cursor.execute("SELECT id FROM exercises WHERE name = ?",
                                     (exercise_data.get('name'),))
                        exercise_id = cursor.fetchone()['id']

                        # Link exercise to workout day
                        cursor.execute("""
                            INSERT INTO workout_exercises (workout_day_id, exercise_id, sets,
                                                         reps, weight_kg, rest_seconds, notes)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (
                            day_id,
                            exercise_id,
                            exercise_data.get('sets'),
                            exercise_data.get('reps'),
                            exercise_data.get('weight_kg'),
                            exercise_data.get('rest_seconds'),
                            exercise_data.get('notes')
                        ))

                logger.info(f"Workout plan saved: {plan_data.get('name')} (ID: {workout_plan_id})")
                return workout_plan_id

        except Exception as e:
            logger.error(f"Error saving workout plan: {e}")
            return None

    def save_diet_plan(self, user_id: int, diet_data: Dict[str, Any]) -> Optional[int]:
        """
        Save a diet plan to the database.
        Args:
            user_id: User ID
            diet_data: Diet plan data
        Returns:
            Diet plan ID if successful, None otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Insert diet plan
                cursor.execute("""
                    INSERT INTO diet_plans (user_id, name, calorie_target, protein_target_g,
                                          carb_target_g, fat_target_g, dietary_restrictions,
                                          ai_generated, gemini_prompt)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id,
                    diet_data.get('name'),
                    diet_data.get('calorie_target'),
                    diet_data.get('protein_target_g'),
                    diet_data.get('carb_target_g'),
                    diet_data.get('fat_target_g'),
                    diet_data.get('dietary_restrictions'),
                    diet_data.get('ai_generated', True),
                    diet_data.get('gemini_prompt')
                ))

                diet_plan_id = cursor.lastrowid

                # Insert meal plans
                for meal_data in diet_data.get('meals', []):
                    cursor.execute("""
                        INSERT INTO meal_plans (diet_plan_id, day_number, meal_type,
                                              recipe_name, ingredients, instructions,
                                              calories_per_serving, protein_g, carbs_g,
                                              fat_g, servings)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        diet_plan_id,
                        meal_data.get('day_number'),
                        meal_data.get('meal_type'),
                        meal_data.get('recipe_name'),
                        meal_data.get('ingredients'),
                        meal_data.get('instructions'),
                        meal_data.get('calories_per_serving'),
                        meal_data.get('protein_g'),
                        meal_data.get('carbs_g'),
                        meal_data.get('fat_g'),
                        meal_data.get('servings', 1)
                    ))

                # Insert shopping list items
                for item_data in diet_data.get('shopping_list', []):
                    cursor.execute("""
                        INSERT INTO shopping_lists (user_id, diet_plan_id, item_name,
                                                   quantity, unit, category)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        user_id,
                        diet_plan_id,
                        item_data.get('item_name'),
                        item_data.get('quantity'),
                        item_data.get('unit'),
                        item_data.get('category')
                    ))

                logger.info(f"Diet plan saved: {diet_data.get('name')} (ID: {diet_plan_id})")
                return diet_plan_id

        except Exception as e:
            logger.error(f"Error saving diet plan: {e}")
            return None

    def get_user_workout_plans(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all workout plans for a user."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM workout_plans
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                """, (user_id,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting workout plans: {e}")
            return []

    def get_user_diet_plans(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all diet plans for a user."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM diet_plans
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                """, (user_id,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting diet plans: {e}")
            return []

    def get_user_foods(self, user_id: int) -> List[str]:
        """Retrieve the list of foods available for the user from the database."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT food_name FROM food_inventory WHERE user_id = ?
                """, (user_id,))
                foods = [row[0] for row in cursor.fetchall()]
                return foods
        except Exception as e:
            logger.error(f"Error retrieving user foods: {e}")
            return []

    def add_food_to_inventory(self, user_id: int, food_name: str) -> bool:
        """Add a food item to user's inventory."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR IGNORE INTO food_inventory (user_id, food_name)
                    VALUES (?, ?)
                """, (user_id, food_name))
                return True
        except Exception as e:
            logger.error(f"Error adding food to inventory: {e}")
            return False

    def log_meal_consumption(self, user_id: int, meal_type: str, description: str, 
                           calories: float, protein: float, carbs: float, fat: float) -> bool:
        """Log a meal as eaten by the user with nutritional details."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO meal_logs
                    (user_id, meal_type, food_items, calories_consumed, protein_g, carbs_g, fat_g)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (user_id, meal_type, description, calories, protein, carbs, fat))
                return True
        except Exception as e:
            logger.error(f"Error logging meal consumption: {e}")
            return False

    def get_nutrition_logs(self, user_id: int, date_range: str) -> pd.DataFrame:
        """Retrieve daily nutrition logs for a user."""
        days_map = {
            "1 Week": 7,
            "2 Weeks": 14,
            "1 Month": 30,
            "3 Months": 90,
            "6 Months": 180,
            "1 Year": 365
        }
        days = days_map.get(date_range, 30)
        
        try:
            with self.get_connection() as conn:
                start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

                # Get most recent calorie target
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT calorie_target
                    FROM diet_plans
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                    LIMIT 1
                """, (user_id,))
                target_row = cursor.fetchone()
                target_calories = target_row[0] if target_row else None

                # Get daily nutrition logs
                query = """
                    SELECT
                        DATE(ml.logged_at) AS date,
                        SUM(ml.calories_consumed) AS calories,
                        SUM(ml.protein_g) AS protein,
                        SUM(ml.carbs_g) AS carbs,
                        SUM(ml.fat_g) AS fats
                    FROM meal_logs ml
                    WHERE ml.user_id = ? AND DATE(ml.logged_at) >= ?
                    GROUP BY DATE(ml.logged_at)
                    ORDER BY DATE(ml.logged_at) ASC
                """
                
                df = pd.read_sql_query(query, conn, params=(user_id, start_date))
                if not df.empty and target_calories is not None:
                    df['target_calories'] = target_calories
                return df

        except Exception as e:
            logger.error(f"Error retrieving nutrition logs: {e}")
            return pd.DataFrame()

    def get_workout_history(self, user_id: int, date_range: str) -> pd.DataFrame:
        """Retrieve workout history for a user filtered by date range."""
        days_map = {
            "1 Week": 7,
            "2 Weeks": 14,
            "1 Month": 30,
            "3 Months": 90,
            "6 Months": 180,
            "1 Year": 365
        }
        days = days_map.get(date_range, 30)

        try:
            with self.get_connection() as conn:
                start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
                query = """
                    SELECT
                        wl.completed_at AS date,
                        wl.plan_name AS name,
                        wd.day_number AS day_number,
                        SUM(el.sets_completed * CAST(el.reps_completed AS INTEGER) * el.weight_used_kg) AS volume,
                        COUNT(DISTINCT wl.id) AS sessions,
                        AVG(wl.duration_minutes) AS duration,
                        1.0 AS completion_rate
                    FROM workout_logs wl
                    JOIN exercise_logs el ON wl.id = el.workout_log_id
                    JOIN workout_days wd ON wl.workout_day_id = wd.id
                    WHERE wl.user_id = ? AND DATE(wl.completed_at) >= ?
                    GROUP BY DATE(wl.completed_at), wl.plan_name, wd.day_number
                    ORDER BY DATE(wl.completed_at) ASC
                """
                return pd.read_sql_query(query, conn, params=(user_id, start_date))
        except Exception as e:
            logger.error(f"Error retrieving workout history: {e}")
            return pd.DataFrame()


    def get_body_metrics(self, user_id: int) -> List[Dict[str, Any]]:
        """Retrieve body composition metrics for a user ordered by date."""
        try:
            with self.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT height_cm, weight_kg, date
                    FROM progress_tracking
                    WHERE user_id = ?
                    ORDER BY date ASC
                """, (user_id,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error retrieving body metrics: {e}")
            return []

    def add_progress_entry(self, user_id: int, weight_kg: float, height_cm: float,date) -> bool:
        """Add a progress tracking entry."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO progress_tracking (user_id, weight_kg, height_cm,date)
                    VALUES (?, ?, ?,?)
                """, (user_id, weight_kg, height_cm,date))
                return True
        except Exception as e:
            logger.error(f"Error adding progress entry: {e}")
            return False

    def update_user_profile(self, user_id: int, profile_data: Dict[str, Any]) -> bool:
        """Update user profile information."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Build dynamic update query
                update_fields = []
                values = []
                
                for field in ['first_name', 'last_name', 'age', 'gender', 'height_cm', 
                             'weight_kg', 'activity_level', 'fitness_goals', 'injuries', 
                             'experience_level']:
                    if field in profile_data:
                        update_fields.append(f"{field} = ?")
                        values.append(profile_data[field])
                
                if update_fields:
                    values.append(user_id)
                    query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = ?"
                    cursor.execute(query, values)
                    return True
                return False
                
        except Exception as e:
            logger.error(f"Error updating user profile: {e}")
            return False

# Create a global database instance
db = DatabaseManager()
