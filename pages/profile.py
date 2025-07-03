"""
Profile page for the Fitness Dashboard.
Handles user profile management and editing.
"""
import streamlit as st
from modules.auth import AuthManager
from modules.database import db
import logging

logger = logging.getLogger(__name__)

def render_profile_content():
    """Render the profile page content."""
    st.markdown('<div class="main-header">', unsafe_allow_html=True)
    st.title("👤 User Profile")
    st.markdown("Manage your personal information and fitness preferences")
    st.markdown('</div>', unsafe_allow_html=True)

    user = AuthManager.get_current_user()
    if not user:
        st.error("User data not found")
        return

    # Create tabs for different profile sections
    profile_tab, settings_tab = st.tabs(["Profile Information", "Account Settings"])
    
    with profile_tab:
        render_profile_info(user)
    
    with settings_tab:
        render_account_settings(user)

def render_profile_info(user):
    """Render profile information form."""
    st.subheader("Personal Information")
    
    with st.form("profile_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            first_name = st.text_input("First Name", value=user.get('first_name', ''))
            username = st.text_input("Username", value=user.get('username', ''), disabled=True)
            age = st.number_input("Age", min_value=13, max_value=120, value=int(user.get('age', 25)))
            height_cm = st.number_input("Height (cm)", min_value=100.0, max_value=250.0, 
                                       value=float(user.get('height_cm', 170)))
            activity_level = st.selectbox(
                "Activity Level",
                ["Sedentary", "Lightly Active", "Moderately Active", "Very Active", "Extremely Active"],
                index=["Sedentary", "Lightly Active", "Moderately Active", "Very Active", "Extremely Active"]
                     .index(user.get('activity_level', 'Moderately Active')) if user.get('activity_level') in 
                     ["Sedentary", "Lightly Active", "Moderately Active", "Very Active", "Extremely Active"] else 2
            )
            
        with col2:
            last_name = st.text_input("Last Name", value=user.get('last_name', ''))
            email = st.text_input("Email", value=user.get('email', ''), disabled=True)
            gender = st.selectbox("Gender", ["Male", "Female", "Other", "Prefer not to say"],
                                 index=["Male", "Female", "Other", "Prefer not to say"]
                                      .index(user.get('gender', 'Male')) if user.get('gender') in 
                                      ["Male", "Female", "Other", "Prefer not to say"] else 0)
            weight_kg = st.number_input("Weight (kg)", min_value=30.0, max_value=300.0, 
                                       value=float(user.get('weight_kg', 70.0)))
            experience_level = st.selectbox(
                "Fitness Experience",
                ["Beginner", "Intermediate", "Advanced"],
                index=["Beginner", "Intermediate", "Advanced"]
                     .index(user.get('experience_level', 'Beginner')) if user.get('experience_level') in 
                     ["Beginner", "Intermediate", "Advanced"] else 0
            )
        
        fitness_goals = st.text_area("Fitness Goals", value=user.get('fitness_goals', ''),
                                    help="Describe your fitness objectives")
        injuries = st.text_area("Injuries/Limitations", value=user.get('injuries', ''),
                               help="Any injuries or physical limitations to consider")
        
        if st.form_submit_button("Update Profile", type="primary"):
            profile_data = {
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
            
            if db.update_user_profile(user['id'], profile_data):
                st.success("Profile updated successfully!")
                # Update session state
                updated_user = {**user, **profile_data}
                st.session_state.user_data = updated_user
                st.rerun()
            else:
                st.error("Failed to update profile")

def render_account_settings(user):
    """Render account settings."""
    st.subheader("Account Settings")
    
    # Account information display
    st.info(f"**Account Created:** {user.get('created_at', 'Unknown')}")
    st.info(f"**User ID:** {user.get('id')}")
    
    # Quick stats
    col1, col2, col3 = st.columns(3)
    
    with col1:
        workout_plans = db.get_user_workout_plans(user['id'])
        st.metric("Workout Plans", len(workout_plans))
    
    with col2:
        diet_plans = db.get_user_diet_plans(user['id'])
        st.metric("Diet Plans", len(diet_plans))
    
    with col3:
        foods = db.get_user_foods(user['id'])
        st.metric("Food Items", len(foods))
    
    st.markdown("---")
    
    # Data management
    st.subheader("Data Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Export My Data", help="Download your profile and fitness data"):
            try:
                # Create export data
                export_data = {
                    'profile': dict(user),
                    'workout_plans': workout_plans,
                    'diet_plans': diet_plans,
                    'food_inventory': foods
                }
                
                st.download_button(
                    label="Download Data (JSON)",
                    data=str(export_data),
                    file_name=f"fittrack_data_{user['username']}.json",
                    mime="application/json"
                )
            except Exception as e:
                st.error(f"Error exporting data: {e}")
    
    with col2:
        if st.button("Reset All Data", help="Clear all workout and diet plans"):
            st.warning("This feature is not yet implemented for safety reasons")
