"""
Workouts page for the Fitness Dashboard.
Handles workout plan generation, viewing, and logging.
"""
import streamlit as st
import json
from datetime import datetime, timedelta
from modules.auth import AuthManager
from modules.database import db
from modules.ai_integration import gemini_client
import logging

logger = logging.getLogger(__name__)

def render_workouts_content():
    """Render the workouts page content."""
    st.markdown('<div class="main-header">', unsafe_allow_html=True)
    st.title("💪 Workout Plans")
    st.markdown("AI-powered personalized workout planning and tracking")
    st.markdown('</div>', unsafe_allow_html=True)

    user = AuthManager.get_current_user()
    if not user:
        st.error("Please log in to access workouts")
        return

    # Create tabs for different workout sections
    generate_tab, my_plans_tab, logging_tab ,ai_coach= st.tabs(["Generate Plan", "My Plans", "Log Workout", "AI Coach"])
    
    with generate_tab:
        render_workout_generator()
    
    with my_plans_tab:
        render_my_workout_plans()
    
    with logging_tab:
        render_workout_logging()
    with ai_coach:
        render_ai_coach(user)

def render_workout_generator():
    """Render workout plan generator."""
    st.subheader("🤖 AI Workout Plan Generator")
    user = AuthManager.get_current_user()
    
    if not gemini_client.is_available():
        st.warning("AI integration is not available. Please configure GEMINI_API_KEY in your environment.")
        return
    
    with st.form("workout_generator_form"):
        st.markdown("**Customize Your Workout Plan**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            days_per_week = st.slider("Days per week", 2, 7, 4)
            session_duration = st.selectbox(
                "Session duration", 
                ["30-45 minutes", "45-60 minutes", "60-90 minutes", "90+ minutes"]
            )
            workout_type = st.selectbox(
                "Primary focus",
                ["Balanced strength and cardio", "Strength building", "Weight loss", 
                 "Endurance", "Muscle building", "Athletic performance"]
            )
            name = st.text_input("Workout name", 
                                        placeholder="workout 1")
        
        with col2:
            equipment = st.selectbox(
                "Available equipment",
                ["Full gym access", "Home gym basics", "Bodyweight only", 
                 "Dumbbells only", "Resistance bands"]
            )
            intensity = st.selectbox(
                "Preferred intensity",
                ["Low", "Moderate", "High", "Variable"]
            )
            special_focus = st.text_input("Special focus areas (optional)", 
                                        placeholder="e.g., core strength, flexibility")
        
        if st.form_submit_button("Generate Workout Plan", type="primary"):
            with st.spinner("Creating your personalized workout plan..."):
                try:
                    # Prepare user profile and preferences
                    user_profile = {
                        'age': user.get('age'),
                        'gender': user.get('gender'),
                        'height_cm': user.get('height_cm'),
                        'weight_kg': user.get('weight_kg'),
                        'activity_level': user.get('activity_level'),
                        'experience_level': user.get('experience_level'),
                        'fitness_goals': user.get('fitness_goals'),
                        'injuries': user.get('injuries')
                    }
                    
                    preferences = {
                        'name':name,
                        'days_per_week': days_per_week,
                        'session_duration': session_duration,
                        'equipment': equipment,
                        'workout_type': workout_type,
                        'intensity': intensity,
                        'special_focus': special_focus
                    }
                    
                    # Generate workout plan
                    workout_plan = gemini_client.generate_workout_plan(user_profile, preferences)
                    
                    if workout_plan:
                        # Save to database
                        plan_id = db.save_workout_plan(user['id'], workout_plan)
                        if plan_id:
                            st.success("🎉 Workout plan generated and saved successfully!")
                            st.session_state.generated_workout = workout_plan
                            display_workout_plan(workout_plan)
                        else:
                            st.error("Failed to save workout plan")
                    else:
                        st.error("Failed to generate workout plan")
                        
                except Exception as e:
                    logger.error(f"Error generating workout plan: {e}")
                    st.error(f"Error generating workout plan: {str(e)}")

def render_my_workout_plans():
    """Render saved workout plans."""
    user_id = AuthManager.get_current_user_id()
    
    st.subheader("Your Workout Plans")
    
    workout_plans = db.get_user_workout_plans(user_id)
    
    if not workout_plans:
        st.info("You don't have any workout plans yet. Generate your first plan in the 'Generate New Plan' tab!")
        return
    
    # Display workout plans
    for plan in workout_plans:
        with st.container():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**Plan:** {plan.get('name')}")
                st.write(f"**Description:** {plan.get('description', 'No description')}")
                st.write(f"**Duration:** {plan.get('duration_weeks', 'N/A')} weeks")
                st.write(f"**Created:** {plan.get('created_at', 'N/A')}")
                if plan.get('ai_generated'):
                    st.success("🤖 AI Generated")
            
            with col2:
                if st.button(f"View Details", key=f"view_{plan['id']}"):
                    current_state = st.session_state.get(f"show_plan_{plan['id']}", False)
                    st.session_state[f"show_plan_{plan['id']}"] = not current_state
                
                if st.button(f"Delete Plan", key=f"delete_{plan['id']}", type="secondary"):
                    if delete_workout_plan(plan['id']):
                        st.success("Plan deleted successfully!")
                        st.rerun()
            
            # Show plan details if requested (outside the main container)
            if st.session_state.get(f"show_plan_{plan['id']}", False):
                show_workout_plan_details(plan['id'])
        

def render_workout_logging():
    """Render workout logging interface."""    
    user_id = AuthManager.get_current_user_id()
    st.subheader("Log Your Workout")
    
    # Get user's workout plans
    workout_plans = db.get_user_workout_plans(user_id)
    
    if not workout_plans:
        st.info("Create a workout plan first to log your workouts!")
        return
    
    # Select workout plan and day
    plan_names = [f"{plan['name']} (Created: {plan['created_at'][:10]})" for plan in workout_plans]
    selected_plan_idx = st.selectbox("Select workout plan", range(len(plan_names)), 
                                   format_func=lambda x: plan_names[x])
    
    selected_plan = workout_plans[selected_plan_idx]
    
    # Get workout days for selected plan
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM workout_days WHERE workout_plan_id = ? ORDER BY day_number
            """, (selected_plan['id'],))
            workout_days = [dict(row) for row in cursor.fetchall()]
        
        if workout_days:
            day_names = [f"Day {day['day_number']}: {day['day_name']}" for day in workout_days]
            selected_day_idx = st.selectbox("Select workout day", range(len(day_names)),
                                          format_func=lambda x: day_names[x])
            
            selected_day = workout_days[selected_day_idx]
            
            # Log workout form
            with st.form("log_workout"):
                st.markdown(f"### Logging: {selected_day['day_name']}")
                st.write(f"**Focus:** {selected_day['focus_area']}")
                
                duration = st.number_input("Workout duration (minutes)", min_value=1, value=45)
                notes = st.text_area("Workout notes")
                
                # Get exercises for this day
                cursor.execute("""
                    SELECT e.*, we.sets, we.reps, we.weight_kg, we.rest_seconds, we.notes as exercise_notes
                    FROM exercises e
                    JOIN workout_exercises we ON e.id = we.exercise_id
                    WHERE we.workout_day_id = ?
                """, (selected_day['id'],))
                exercises = [dict(row) for row in cursor.fetchall()]
                
                st.markdown("#### Exercise Performance")
                exercise_logs = []
                
                for i, exercise in enumerate(exercises):
                    st.markdown(f"**{exercise['name']}**")
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        sets_completed = st.number_input(
                            f"Sets", min_value=0, value=exercise['sets'] or 3, 
                            key=f"sets_{i}")
                    with col2:
                        reps_completed = st.text_input(
                            f"Reps", value=exercise['reps'] or "10", 
                            key=f"reps_{i}")
                    with col3:
                        weight_used = st.number_input(
                            f"Weight (kg)", min_value=0.0, value=float(exercise['weight_kg'] or 0), 
                            key=f"weight_{i}")
                    with col4:
                        perceived_exertion = st.selectbox(
                            f"Effort (1-10)", range(1, 11), index=6, 
                            key=f"effort_{i}")
                    
                    exercise_notes = st.text_input(f"Notes for {exercise['name']}", key=f"ex_notes_{i}")
                    
                    exercise_logs.append({
                        'exercise_id': exercise['id'],
                        'sets_completed': sets_completed,
                        'reps_completed': reps_completed,
                        'weight_used_kg': weight_used,
                        'perceived_exertion': perceived_exertion,
                        'notes': exercise_notes
                    })
                
                if st.form_submit_button("Log Workout", use_container_width=True):
                    # Save workout log
                    try:
                        cursor.execute("""
                            INSERT INTO workout_logs (user_id, workout_day_id, duration_minutes, notes)
                            VALUES (?, ?, ?, ?)
                        """, (user_id, selected_day['id'], duration, notes))
                        
                        workout_log_id = cursor.lastrowid
                        
                        # Save exercise logs
                        for exercise_log in exercise_logs:
                            cursor.execute("""
                                INSERT INTO exercise_logs (workout_log_id, exercise_id, sets_completed,
                                                         reps_completed, weight_used_kg, perceived_exertion, notes)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            """, (workout_log_id, exercise_log['exercise_id'], 
                                 exercise_log['sets_completed'], exercise_log['reps_completed'],
                                 exercise_log['weight_used_kg'], exercise_log['perceived_exertion'],
                                 exercise_log['notes']))
                        
                        conn.commit()
                        st.success("Workout logged successfully! 🎉")
                        
                        # Log progress metrics
                        db.log_progress(user_id, 'workout_completed', 1, 'count', 
                                      f"Completed: {selected_day['day_name']}")
                        
                    except Exception as e:
                        st.error(f"Error logging workout: {e}")
        
        else:
            st.warning("No workout days found for this plan")
            
    except Exception as e:
        st.error(f"Error loading workout data: {e}")


def display_workout_plan(plan):
    """Display a generated workout plan."""
    st.markdown("### 📋 Your Generated Workout Plan")
    
    st.markdown(f"**Plan Name:** {plan.get('name')}")
    st.markdown(f"**Description:** {plan.get('description')}")
    st.markdown(f"**Duration:** {plan.get('duration_weeks')} weeks")
    
    # Display workout days
    for day in plan.get('days', []):
        with st.expander(f"Day {day.get('day_number')}: {day.get('day_name')}"):
            st.markdown(f"**Focus:** {day.get('focus_area')}")
            
            # Display exercises
            for exercise in day.get('exercises', []):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**{exercise.get('name')}**")
                    st.markdown(f"*{exercise.get('instructions', 'No instructions')}*")
                    if exercise.get('notes'):
                        st.info(exercise.get('notes'))
                
                with col2:
                    st.markdown(f"Sets: {exercise.get('sets')}")
                    st.markdown(f"Reps: {exercise.get('reps')}")
                    if exercise.get('rest_seconds'):
                        st.markdown(f"Rest: {exercise.get('rest_seconds')}s")
def render_ai_coach(user):
    """Render AI coaching interface."""
    st.subheader("🤖 AI Fitness Coach")
    
    if not gemini_client.is_available():
        st.warning("AI Coach is not available. Please configure GEMINI_API_KEY.")
        return
    
    st.markdown("Ask your AI fitness coach anything about workouts, nutrition, or fitness goals!")
    
    # Chat interface
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    # Display chat history
    for i, message in enumerate(st.session_state.chat_history):
        if message["role"] == "user":
            st.markdown(f"**You:** {message['content']}")
        else:
            st.markdown(f"**AI Coach:** {message['content']}")
    
    # Input for new question
    question = st.text_input("Ask your AI coach:", key="coach_question")
    
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("Ask Coach", type="primary"):
            if question:
                # Add user question to history
                st.session_state.chat_history.append({
                    "role": "user",
                    "content": question
                })
                
                # Get AI response
                user_context = {
                    'fitness_goals': user.get('fitness_goals'),
                    'experience_level': user.get('experience_level'),
                    'current_focus': 'General fitness coaching'
                }
                
                with st.spinner("AI Coach is thinking..."):
                    response = gemini_client.get_fitness_advice(question, user_context)
                
                if response:
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": response
                    })
                
                st.rerun()
    
    with col2:
        if st.button("Clear Chat"):
            st.session_state.chat_history = []
            st.rerun()
    
    # Quick question buttons
    st.markdown("#### Quick Questions")
    quick_questions = [
        "How can I improve my bench press?",
        "What's the best way to lose weight?",
        "How often should I workout?",
        "Should I do cardio before or after weights?",
        "How do I avoid workout plateaus?"
    ]
    
    cols = st.columns(2)
    for i, q in enumerate(quick_questions):
        with cols[i % 2]:
            if st.button(q, key=f"quick_{i}"):
                st.session_state.chat_history.append({
                    "role": "user",
                    "content": q
                })
                
                user_context = {
                    'fitness_goals': user.get('fitness_goals'),
                    'experience_level': user.get('experience_level'),
                    'current_focus': 'General fitness coaching'
                }
                
                with st.spinner("AI Coach is thinking..."):
                    response = gemini_client.get_fitness_advice(q, user_context)
                
                if response:
                    st.session_state.chat_history.append({
                        "role": "assistant", 
                        "content": response
                    })
                
                st.rerun()
def show_workout_plan_details(plan_id):
    """Show detailed view of a workout plan (styled like display_workout_plan)."""
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()

            # Get plan metadata (optional, if you want to show plan name/desc)
            cursor.execute("""
                SELECT * FROM workout_plans WHERE id = ?
            """, (plan_id,))
            plan = cursor.fetchone()
            if plan:
                plan = dict(plan)
                st.markdown("### 📋 Your Workout Plan")
                st.markdown(f"**Plan Name:** {plan.get('name')}")
                st.markdown(f"**Description:** {plan.get('description')}")
                st.markdown(f"**Duration:** {plan.get('duration_weeks')} weeks")
                st.markdown("---")

            # Get workout days
            cursor.execute("""
                SELECT * FROM workout_days WHERE workout_plan_id = ?
            """, (plan_id,))
            workout_days = [dict(row) for row in cursor.fetchall()]

            # Get exercises for each day
            day_exercise_data = []
            for day in workout_days:
                cursor.execute("""
                    SELECT e.*, we.sets, we.reps, we.weight_kg, we.rest_seconds, we.notes
                    FROM exercises e
                    JOIN workout_exercises we ON e.id = we.exercise_id
                    WHERE we.workout_day_id = ?
                """, (day['id'],))
                exercises = [dict(row) for row in cursor.fetchall()]
                day['exercises'] = exercises
                day_exercise_data.append(day)

        # Display workout days with expanders and two-column exercise layout
        for day in day_exercise_data:
            with st.expander(f"Day {day.get('day_number')}: {day.get('day_name')}"):
                st.markdown(f"**Focus:** {day.get('focus_area')}")
                if day['exercises']:
                    for exercise in day['exercises']:
                        col1, col2 = st.columns([2, 1])
                        with col1:
                            st.markdown(f"**{exercise.get('name')}**")
                            st.markdown(f"*{exercise.get('instructions', 'No instructions')}*")
                            if exercise.get('notes'):
                                st.info(exercise.get('notes'))
                        with col2:
                            st.markdown(f"Sets: {exercise.get('sets')}")
                            st.markdown(f"Reps: {exercise.get('reps')}")
                            if exercise.get('rest_seconds'):
                                st.markdown(f"Rest: {exercise.get('rest_seconds')}s")
                else:
                    st.info("No exercises found for this day.")

    except Exception as e:
        st.error(f"Error loading workout details: {e}")


        
def delete_workout_plan(plan_id):
    """Delete a workout plan and all related data."""
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Delete in correct order due to foreign key constraints
            cursor.execute("DELETE FROM exercise_logs WHERE workout_log_id IN (SELECT id FROM workout_logs WHERE workout_day_id IN (SELECT id FROM workout_days WHERE workout_plan_id = ?))", (plan_id,))
            cursor.execute("DELETE FROM workout_logs WHERE workout_day_id IN (SELECT id FROM workout_days WHERE workout_plan_id = ?)", (plan_id,))
            cursor.execute("DELETE FROM workout_exercises WHERE workout_day_id IN (SELECT id FROM workout_days WHERE workout_plan_id = ?)", (plan_id,))
            cursor.execute("DELETE FROM workout_days WHERE workout_plan_id = ?", (plan_id,))
            cursor.execute("DELETE FROM workout_plans WHERE id = ?", (plan_id,))
            
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"Error deleting workout plan: {e}")
        return False
