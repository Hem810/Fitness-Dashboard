import streamlit as st
from typing import Optional, Dict, Any
import logging
from modules.database import db

logger = logging.getLogger(__name__)

class AuthManager:
    """Manages user authentication and session state."""

    @staticmethod
    def initialize_session_state():
        """Initialize session state variables."""
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        if 'user_data' not in st.session_state:
            st.session_state.user_data = None
        if 'session_token' not in st.session_state:
            st.session_state.session_token = None
        if 'current_page' not in st.session_state:
            st.session_state.current_page = 'profile'

    @staticmethod
    def is_authenticated() -> bool:
        """Check if user is authenticated."""
        return st.session_state.get('authenticated', False)

    @staticmethod
    def get_current_user() -> Optional[Dict[str, Any]]:
        """Get current authenticated user data."""
        return st.session_state.get('user_data')

    @staticmethod
    def get_current_user_id() -> Optional[int]:
        """Get current authenticated user ID."""
        user_data = AuthManager.get_current_user()
        return user_data.get('id') if user_data else None

    @staticmethod
    def login_user(user_data: Dict[str, Any], session_token: str):
        """Login user and set session state."""
        st.session_state.authenticated = True
        st.session_state.user_data = user_data
        st.session_state.session_token = session_token
        logger.info(f"User logged in: {user_data.get('username')}")

    @staticmethod
    def logout_user():
        """Logout user and clear session state."""
        st.session_state.authenticated = False
        st.session_state.user_data = None
        st.session_state.session_token = None
        st.session_state.current_page = 'profile'
        logger.info("User logged out")

    @staticmethod
    def render_auth_form():
        """Render authentication form."""
        st.title("🏋️ FitTrack Dashboard")
        st.markdown("### Welcome to your AI-Powered Fitness Companion")

        # Create tabs for login and registration
        login_tab, register_tab = st.tabs(["Login", "Register"])

        with login_tab:
            AuthManager._render_login_form()

        with register_tab:
            AuthManager._render_register_form()

    @staticmethod
    def _render_login_form():
        """Render login form."""
        st.subheader("Login to Your Account")

        with st.form("login_form"):
            username = st.text_input("Username or Email")
            password = st.text_input("Password", type="password")
            submit_button = st.form_submit_button("Login")

            if submit_button:
                if not username or not password:
                    st.error("Please enter both username and password")
                    return

                # Authenticate user
                user_data = db.authenticate_user(username, password)
                if user_data:
                    # Create session
                    session_token = db.create_session(user_data['id'])
                    if session_token:
                        AuthManager.login_user(user_data, session_token)
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Failed to create session")
                else:
                    st.error("Invalid username or password")

    @staticmethod
    def _render_register_form():
        """Render registration form."""
        st.subheader("Create New Account")

        with st.form("register_form"):
            col1, col2 = st.columns(2)

            with col1:
                first_name = st.text_input("First Name")
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                age = st.number_input("Age", min_value=13, max_value=120, value=25)
                height_cm = st.number_input("Height (cm)", min_value=100, max_value=250, value=170)

            with col2:
                last_name = st.text_input("Last Name")
                email = st.text_input("Email")
                confirm_password = st.text_input("Confirm Password", type="password")
                gender = st.selectbox("Gender", ["Male", "Female", "Other", "Prefer not to say"])
                weight_kg = st.number_input("Weight (kg)", min_value=30, max_value=300, value=70)

            activity_level = st.selectbox(
                "Activity Level",
                ["Sedentary", "Lightly Active", "Moderately Active", "Very Active", "Extremely Active"]
            )

            experience_level = st.selectbox(
                "Fitness Experience",
                ["Beginner", "Intermediate", "Advanced"]
            )

            fitness_goals = st.text_area("Fitness Goals", placeholder="e.g., Lose weight, build muscle, improve endurance...")
            injuries = st.text_area("Injuries/Limitations", placeholder="Any injuries or physical limitations to consider...")

            submit_button = st.form_submit_button("Create Account")

            if submit_button:
                # Validate form
                if not all([first_name, last_name, username, email, password, confirm_password]):
                    st.error("Please fill in all required fields")
                    return

                if password != confirm_password:
                    st.error("Passwords do not match")
                    return

                if len(password) < 6:
                    st.error("Password must be at least 6 characters long")
                    return

                # Create user data
                user_data = {
                    'first_name': first_name,
                    'last_name': last_name,
                    'age': age,
                    'gender': gender,
                    'height_cm': height_cm,
                    'weight_kg': weight_kg,
                    'activity_level': activity_level,
                    'fitness_goals': fitness_goals,
                    'injuries': injuries,
                    'experience_level': experience_level
                }

                # Create user
                user_id = db.create_user(username, email, password, user_data)
                if user_id:
                    st.success("Account created successfully! Please login.")
                    st.balloons()
                else:
                    st.error("Failed to create account. Username or email may already exist.")

def require_auth(func):
    """Decorator to require authentication for a function."""
    def wrapper(*args, **kwargs):
        if not AuthManager.is_authenticated():
            st.error("Please login to access this page")
            st.stop()
        return func(*args, **kwargs)
    return wrapper