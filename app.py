"""
FitTrack: AI-Powered Fitness Dashboard
Main Streamlit application entry point.
"""
import streamlit as st
import sys
import os

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.auth import AuthManager, require_auth
from modules.database import db
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Streamlit page
st.set_page_config(
    page_title="FitTrack Dashboard",
    page_icon="🏋️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        padding: 1rem 0;
        border-bottom: 2px solid #f0f2f6;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
    }
    .nav-button {
        width: 100%;
        margin: 0.25rem 0;
        text-align: left;
    }
    .user-info {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """Main application entry point."""
    try:
        # Initialize session state
        AuthManager.initialize_session_state()
        
        # Check if user is authenticated
        if not AuthManager.is_authenticated():
            AuthManager.render_auth_form()
            return
        
        # User is authenticated, show main dashboard
        render_main_dashboard()
        
    except Exception as e:
        logger.error(f"Error in main application: {e}")
        st.error("An error occurred. Please refresh the page.")

def render_main_dashboard():
    """Render the main dashboard for authenticated users."""
    try:
        # Sidebar navigation
        render_sidebar()
        
        # Main content area
        current_page = st.session_state.get('current_page', 'profile')
        
        if current_page == 'profile':
            render_profile_page()
        elif current_page == 'workouts':
            render_workouts_page()
        elif current_page == 'diet':
            render_diet_page()
        elif current_page == 'progress':
            render_progress_page()
        else:
            render_profile_page()
            
    except Exception as e:
        logger.error(f"Error rendering dashboard: {e}")
        st.error("Error loading dashboard content")

def render_sidebar():
    """Render the sidebar with navigation and user info."""
    user = AuthManager.get_current_user()
    
    with st.sidebar:
        st.markdown('<div class="sidebar-content">', unsafe_allow_html=True)
        
        # User greeting
        st.markdown(f"### Welcome, {user.get('first_name', user.get('username'))}! 👋")
        
        # Navigation menu
        st.markdown("---")
        st.markdown("### 📊 Navigation")
        
        # Navigation buttons
        if st.button("👤 Profile", use_container_width=True, 
                    type="primary" if st.session_state.get('current_page') == 'profile' else "secondary"):
            st.session_state.current_page = 'profile'
            st.rerun()
        
        if st.button("💪 Workouts", use_container_width=True,
                    type="primary" if st.session_state.get('current_page') == 'workouts' else "secondary"):
            st.session_state.current_page = 'workouts'
            st.rerun()
        
        if st.button("🥗 Diet & Nutrition", use_container_width=True,
                    type="primary" if st.session_state.get('current_page') == 'diet' else "secondary"):
            st.session_state.current_page = 'diet'
            st.rerun()
        
        if st.button("📈 Progress", use_container_width=True,
                    type="primary" if st.session_state.get('current_page') == 'progress' else "secondary"):
            st.session_state.current_page = 'progress'
            st.rerun()
        
        st.markdown("---")
        
        # Logout button
        if st.button("🚪 Logout", key="nav_logout", help="Sign out of your account"):
            AuthManager.logout_user()
            st.rerun()

def render_profile_page():
    """Render the user profile page."""
    try:
        from pages.profile import render_profile_content
        render_profile_content()
    except Exception as e:
        logger.error(f"Error rendering profile page: {e}")
        st.error("Error loading profile page")

def render_workouts_page():
    """Render the workouts page."""
    try:
        from pages.workouts import render_workouts_content
        render_workouts_content()
    except Exception as e:
        logger.error(f"Error rendering workouts page: {e}")
        st.error("Error loading workouts page")

def render_diet_page():
    """Render the diet and nutrition page."""
    try:
        from pages.diet import render_diet_content
        render_diet_content()
    except Exception as e:
        logger.error(f"Error rendering diet page: {e}")
        st.error("Error loading diet page")

def render_progress_page():
    """Render the progress tracking page."""
    try:
        from pages.progress import render_progress_content
        render_progress_content()
    except Exception as e:
        logger.error(f"Error rendering progress page: {e}")
        st.error("Error loading progress page")

if __name__ == "__main__":
    main()
