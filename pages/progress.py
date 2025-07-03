"""Progress tracking page for the Fitness Dashboard."""
import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from modules.database import db
from modules.auth import AuthManager
from typing import Dict, List, Any
import logging

# Configure logging
logger = logging.getLogger(__name__)

def render_progress_content():
    """Render the progress tracking page content."""
    st.markdown('<div class="main-header">', unsafe_allow_html=True)
    st.title("📊 Progress Tracking")
    st.markdown("Monitor your fitness journey with detailed analytics")
    st.markdown('</div>', unsafe_allow_html=True)

    user_id = AuthManager.get_current_user_id()
    if not user_id:
        st.error("Please log in to view progress")
        return

    # Create tabs for different progress sections
    overview_tab, body_tab = st.tabs([
        "Overview", "Body Metrics"
    ])
    
    with overview_tab:
        render_progress_overview()
    
    with body_tab:
        render_body_metrics()
    
def render_progress_overview():
    """Render progress overview dashboard."""
    st.subheader("🎯 Progress Overview")
    user_id = AuthManager.get_current_user_id()
    user = AuthManager.get_current_user()
    
    # Current stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Current Weight", f"{user.get('weight_kg', 0)} kg")
    
    with col2:
        st.metric("Height", f"{user.get('height_cm', 0)} cm")
    
    with col3:
        bmi = calculate_bmi(user.get('weight_kg', 0), user.get('height_cm', 0))
        st.metric("BMI", f"{bmi:.1f}" if bmi else "N/A")
    
    with col4:
        workout_plans = db.get_user_workout_plans(user_id)
        st.metric("Workout Plans", len(workout_plans))
    
    # Quick insights
    st.markdown("### 💡 Quick Insights")
    
    # Get recent progress data
    body_metrics = db.get_body_metrics(user_id)
    workout_history = db.get_workout_history(user_id, "1 Month")
    nutrition_logs = db.get_nutrition_logs(user_id, "1 Week")
    
    insights = generate_insights(body_metrics, workout_history, nutrition_logs, user)
    
    for insight in insights:
        st.info(insight)

def render_body_metrics():
    """Render body metrics tracking."""
    st.subheader("⚖️ Body Metrics")
    user_id = AuthManager.get_current_user_id()
    
    # Add new measurement
    st.markdown("**Log New Measurement**")
    with st.form("body_metrics_form"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            weight_kg = st.number_input("Weight (kg)", min_value=30.0, max_value=300.0, value=70.0, step=0.1)
        
        with col2:
            height_cm = st.number_input("Height (cm)", min_value=100.0, max_value=250.0, value=170.0, step=0.1)
        
        with col3:
            measurement_date = st.date_input("Date", value=datetime.now().date())
        
        if st.form_submit_button("Log Measurement", type="primary"):
            if db.add_progress_entry(user_id, weight_kg, height_cm,measurement_date):
                st.success("Measurement logged successfully!")
                st.rerun()
            else:
                st.error("Failed to log measurement")
    
    # Display progress charts
    body_metrics = db.get_body_metrics(user_id)
    
    if body_metrics:
        df = pd.DataFrame(body_metrics)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        # Weight progress chart
        st.markdown("**Weight Progress**")
        if len(df) > 1:
            fig, ax = plt.subplots(figsize=(10, 4))
            ax.plot(df['date'], df['weight_kg'], marker='o', linewidth=2)
            ax.set_xlabel("Date")
            ax.set_ylabel("Weight (kg)")
            ax.set_title("Weight Trend")
            ax.grid(True, alpha=0.3)
            st.pyplot(fig)
            
            # Weight change summary
            weight_change = df['weight_kg'].iloc[-1] - df['weight_kg'].iloc[0]
            change_color = "green" if weight_change < 0 else "red"
            st.markdown(f"**Total change:** <span style='color:{change_color}'>{weight_change:+.1f} kg</span>", 
                       unsafe_allow_html=True)
        else:
            st.info("Log at least 2 measurements to see progress trends")
        
        # BMI tracking
        if 'height_cm' in df.columns:
            df['bmi'] = df.apply(lambda row: calculate_bmi(row['weight_kg'], row['height_cm']), axis=1)
            
            st.markdown("**BMI Progress**")
            if len(df) > 1:
                fig, ax = plt.subplots(figsize=(10, 4))
                ax.plot(df['date'], df['bmi'], marker='o', linewidth=2, color='orange')
                ax.set_xlabel("Date")
                ax.set_ylabel("BMI")
                ax.set_title("BMI Trend")
                ax.grid(True, alpha=0.3)
                
                # Add BMI categories
                ax.axhline(y=18.5, color='blue', linestyle='--', alpha=0.5, label='Underweight')
                ax.axhline(y=25, color='green', linestyle='--', alpha=0.5, label='Normal')
                ax.axhline(y=30, color='orange', linestyle='--', alpha=0.5, label='Overweight')
                ax.legend()
                
                st.pyplot(fig)
    else:
        st.info("No body measurements recorded yet. Log your first measurement above!")



def calculate_bmi(weight_kg: float, height_cm: float) -> float:
    """Calculate BMI from weight and height."""
    if weight_kg and height_cm:
        height_m = height_cm / 100
        return weight_kg / (height_m ** 2)
    return 0

def generate_insights(body_metrics: List[Dict], workout_data: pd.DataFrame, 
                     nutrition_data: pd.DataFrame, user: Dict) -> List[str]:
    """Generate personalized insights based on user data."""
    insights = []
    
    # Body metrics insights
    if len(body_metrics) >= 2:
        df = pd.DataFrame(body_metrics)
        weight_trend = df['weight_kg'].iloc[-1] - df['weight_kg'].iloc[0]
        
        if weight_trend < -1:
            insights.append(f"🎉 Great progress! You've lost {abs(weight_trend):.1f} kg since you started tracking.")
        elif weight_trend > 1:
            insights.append(f"📈 You've gained {weight_trend:.1f} kg. Check if this aligns with your fitness goals.")
        else:
            insights.append("⚖️ Your weight has remained stable, which is great for maintenance goals.")
    
    # Workout insights
    if not workout_data.empty:
        avg_sessions = workout_data['sessions'].mean()
        if avg_sessions >= 4:
            insights.append("💪 Excellent workout consistency! You're averaging 4+ sessions per week.")
        elif avg_sessions >= 2:
            insights.append("👍 Good workout frequency. Consider adding 1-2 more sessions for faster progress.")
        else:
            insights.append("🎯 Try to increase your workout frequency for better results.")
    
    # Nutrition insights
    if not nutrition_data.empty and 'target_calories' in nutrition_data.columns:
        target = nutrition_data['target_calories'].iloc[0]
        avg_intake = nutrition_data['calories'].mean()
        adherence = (avg_intake / target) * 100
        
        if 90 <= adherence <= 110:
            insights.append("🎯 Excellent nutrition adherence! You're hitting your calorie targets consistently.")
        elif adherence < 90:
            insights.append("📉 You're consistently under your calorie target. Consider increasing intake if needed.")
        else:
            insights.append("📈 You're exceeding your calorie targets. Review portion sizes if weight loss is your goal.")
    
    # Goal-based insights
    goals = user.get('fitness_goals', '').lower()
    if 'weight loss' in goals or 'lose weight' in goals:
        insights.append("🔥 Focus on maintaining a consistent calorie deficit and regular cardio for weight loss.")
    elif 'muscle' in goals or 'strength' in goals:
        insights.append("💪 Prioritize protein intake and progressive overload in your workouts for muscle building.")
    
    return insights if insights else ["📊 Keep logging your data to receive personalized insights!"]
