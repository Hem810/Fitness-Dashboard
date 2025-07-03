"""
Diet and nutrition page for the Fitness Dashboard.
Handles meal planning, nutrition tracking, and food inventory management.
"""
import streamlit as st
import requests
from datetime import datetime
from modules.database import db
from modules.auth import AuthManager
from dotenv import load_dotenv
from modules.ai_integration import gemini_client
from typing import List
import logging
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

def render_diet_content():
    """Render the diet and nutrition page content."""
    st.markdown('<div class="main-header">', unsafe_allow_html=True)
    st.title("🥗 Diet & Nutrition")
    st.markdown("AI-powered meal planning and nutrition tracking")
    st.markdown('</div>', unsafe_allow_html=True)

    user_id = AuthManager.get_current_user_id()
    if not user_id:
        st.error("Please log in to access diet planning")
        return

    # Create tabs for different diet sections
    generate_tab, my_plans_tab, food_tab, logging_tab = st.tabs([
        "Generate Plan", "My Plans", "Food Inventory", "Log Meals"
    ])
    
    with generate_tab:
        render_diet_generator()
    
    with my_plans_tab:
        render_my_diet_plans()
    
    with food_tab:
        render_food_inventory()
    
    with logging_tab:
        render_meal_logging()

def render_diet_generator():
    """Render diet plan generator."""
    st.subheader("🤖 AI Meal Plan Generator")
    user = AuthManager.get_current_user()
    
    if not gemini_client.is_available():
        st.warning("AI integration is not available. Please configure GEMINI_API_KEY in your environment.")
        return
    
    with st.form("diet_generator_form"):
        st.markdown("**Customize Your Meal Plan**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            calorie_target = st.number_input("Daily calorie target", min_value=1000, max_value=5000, value=2000)
            protein_target = st.number_input("Protein target (g)", min_value=50, max_value=300, value=120)
            meals_per_day = st.slider("Meals per day", 2, 6, 3)
            name = st.text_input("Diet name", 
                                        placeholder="diet 1")
            
        with col2:
            carb_target = st.number_input("Carb target (g)", min_value=50, max_value=500, value=250)
            fat_target = st.number_input("Fat target (g)", min_value=30, max_value=200, value=67)
            snacks_per_day = st.slider("Snacks per day", 0, 3, 1)
        
        dietary_restrictions = st.text_area(
            "Dietary restrictions/preferences",
            placeholder="e.g., vegetarian, gluten-free, no dairy, keto..."
        )
        
        cooking_time = st.selectbox(
            "Preferred cooking time",
            ["Quick (15-30 min)", "Moderate (30-60 min)", "Elaborate (60+ min)", "Mixed"]
        )
        
        cuisine_preference = st.text_input(
            "Cuisine preferences (optional)",
            placeholder="e.g., Mediterranean, Asian, American..."
        )
        
        if st.form_submit_button("Generate Meal Plan", type="primary"):
            with st.spinner("Creating your personalized meal plan..."):
                try:
                    # Get user's food inventory
                    available_foods = db.get_user_foods(user['id'])
                    if not available_foods:
                        st.info("No foods in your inventory. Using standard ingredients.")
                        available_foods = ["chicken breast", "rice", "broccoli", "eggs", "oats", 
                                         "salmon", "sweet potato", "spinach", "almonds", "Greek yogurt"]
                    
                    # Prepare user profile and dietary goals
                    user_profile = {
                        'age': user.get('age'),
                        'gender': user.get('gender'),
                        'height_cm': user.get('height_cm'),
                        'weight_kg': user.get('weight_kg'),
                        'activity_level': user.get('activity_level'),
                        'fitness_goals': user.get('fitness_goals')
                    }
                    
                    dietary_goals = {
                        'name':name,
                        'calorie_target': calorie_target,
                        'protein_target': protein_target,
                        'carb_target': carb_target,
                        'fat_target': fat_target,
                        'restrictions': dietary_restrictions,
                        'meals_per_day': meals_per_day,
                        'snacks_per_day': snacks_per_day,
                        'cooking_time': cooking_time,
                        'cuisine_preference': cuisine_preference
                    }
                    
                    # Generate diet plan
                    diet_plan = gemini_client.generate_diet_plan(user_profile, available_foods, dietary_goals)
                    
                    if diet_plan:
                        # Save to database
                        plan_id = db.save_diet_plan(user['id'], diet_plan)
                        if plan_id:
                            st.success("🎉 Meal plan generated and saved successfully!")
                            st.session_state.generated_diet = diet_plan
                            display_diet_plan(diet_plan)
                        else:
                            st.error("Failed to save meal plan")
                    else:
                        st.error("Failed to generate meal plan")
                        
                except Exception as e:
                    logger.error(f"Error generating diet plan: {e}")
                    st.error(f"Error generating diet plan: {str(e)}")

def render_my_diet_plans():
    """Render saved diet plans."""
    st.subheader("📋 My Meal Plans")
    user_id = AuthManager.get_current_user_id()
    
    diet_plans = db.get_user_diet_plans(user_id)
    
    if not diet_plans:
        st.info("No meal plans found. Generate your first plan in the 'Generate Plan' tab!")
        return
    detail_button=[False,0]
    for plan in diet_plans:
        with st.expander(f"🍽️ {plan['name']} - {plan.get('calorie_target', 'N/A')} cal/day"):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**Calorie Target:** {plan.get('calorie_target', 'N/A')} calories")
                st.markdown(f"**Protein:** {plan.get('protein_target_g', 'N/A')}g | "
                           f"**Carbs:** {plan.get('carb_target_g', 'N/A')}g | "
                           f"**Fat:** {plan.get('fat_target_g', 'N/A')}g")
                st.markdown(f"**Created:** {plan.get('created_at', 'Unknown')}")
                if plan.get('dietary_restrictions'):
                    st.markdown(f"**Restrictions:** {plan.get('dietary_restrictions')}")
                if plan.get('ai_generated'):
                    st.success("🤖 AI Generated")
            
            with col2:
                if st.button(f"View Details", key=f"view_diet_{plan['id']}"):
                    st.session_state.selected_diet_plan = plan['id']
                    detail_button=[True,plan['id']]
                
                if st.button(f"Delete Plan", key=f"delete_diet_{plan['id']}", type="secondary"):
                    if delete_diet_plan(plan['id']):
                        st.success("Plan deleted successfully!")
                        st.rerun()
        if(detail_button[0]):
            show_diet_plan_details(detail_button[1])
def render_food_inventory():
    """Render food inventory management."""
    st.subheader("🛒 Food Inventory")
    user_id = AuthManager.get_current_user_id()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("**Add New Food Item**")
        with st.form("add_food_form"):
            new_food = st.text_input("Food name", placeholder="e.g., chicken breast, broccoli, quinoa")
            if st.form_submit_button("Add Food"):
                if new_food:
                    if db.add_food_to_inventory(user_id, new_food):
                        st.success(f"Added {new_food} to your inventory!")
                        st.rerun()
                    else:
                        st.error("Failed to add food item")
                else:
                    st.error("Please enter a food name")
    
    with col2:
        st.markdown("**Quick Add**")
        common_foods = ["Eggs", "Milk", "Bread", "Rice", "Pasta", "Chicken", "Beef", "Fish"]
        for food in common_foods:
            if st.button(food, key=f"quick_{food}"):
                if db.add_food_to_inventory(user_id, food):
                    st.success(f"Added {food}!")
                    st.rerun()
    
    # Display current inventory
    st.markdown("**Your Food Inventory**")
    foods = db.get_user_foods(user_id)
    
    if foods:
        # Display in columns
        cols = st.columns(4)
        for i, food in enumerate(foods):
            with cols[i % 4]:
                st.markdown(f"• {food}")
        
        st.markdown(f"**Total items:** {len(foods)}")
    else:
        st.info("Your food inventory is empty. Add some items to get personalized meal plans!")

def render_meal_logging():
    """Render meal logging interface."""
    st.subheader("📝 Log Today's Meals")
    
    user_id = AuthManager.get_current_user_id()
    
    with st.form("meal_log_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            meal_type = st.selectbox("Meal type", ["Breakfast", "Lunch", "Dinner", "Snack"])
            meal_description = st.text_area("Meal description", 
                                          placeholder="Describe what you ate...")
            
        with col2:
            calories = st.number_input("Calories", min_value=0, value=0)
            protein = st.number_input("Protein (g)", min_value=0.0, value=0.0, step=0.1)
            carbs = st.number_input("Carbs (g)", min_value=0.0, value=0.0, step=0.1)
            fat = st.number_input("Fat (g)", min_value=0.0, value=0.0, step=0.1)
        
        if st.form_submit_button("Log Meal", type="primary"):
            if meal_description and calories > 0:
                if db.log_meal_consumption(user_id, meal_type, meal_description, 
                                         calories, protein, carbs, fat):
                    st.success("Meal logged successfully!")
                    st.balloons()
                else:
                    st.error("Failed to log meal")
            else:
                st.error("Please provide meal description and calories")
    
    # Display today's nutrition summary
    render_daily_nutrition_summary(user_id)

def render_daily_nutrition_summary(user_id: int):
    """Display today's nutrition summary."""
    st.markdown("### 📊 Today's Nutrition Summary")
    
    try:
        # Get today's nutrition data
        nutrition_df = db.get_nutrition_logs(user_id, "1 Week")
        
        if not nutrition_df.empty:
            today = datetime.now().strftime('%Y-%m-%d')
            today_data = nutrition_df[nutrition_df['date'] == today]
            
            if not today_data.empty:
                today_nutrition = today_data.iloc[0]
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Calories", f"{int(today_nutrition['calories'])}")
                
                with col2:
                    st.metric("Protein", f"{int(today_nutrition['protein'])}g")
                
                with col3:
                    st.metric("Carbs", f"{int(today_nutrition['carbs'])}g")
                
                with col4:
                    st.metric("Fat", f"{int(today_nutrition['fats'])}g")
                
                # Progress bars if targets are available
                if 'target_calories' in today_nutrition:
                    target = today_nutrition['target_calories']
                    actual = today_nutrition['calories']
                    progress = min(actual / target, 1.0) if target > 0 else 0
                    st.progress(progress, text=f"Calorie Goal: {int(actual)}/{int(target)}")
            else:
                st.info("No meals logged today yet.")
        else:
            st.info("No nutrition data available.")
            
    except Exception as e:
        logger.error(f"Error displaying nutrition summary: {e}")
        st.error("Error loading nutrition summary")

def display_diet_plan(plan):
    """Display a generated diet plan."""
    st.markdown("### 🍽️ Your Generated Meal Plan")
    
    st.markdown(f"**Plan Name:** {plan.get('name')}")
    st.markdown(f"**Daily Targets:** {plan.get('calorie_target')} cal | "
               f"{plan.get('protein_target_g')}g protein | "
               f"{plan.get('carb_target_g')}g carbs | "
               f"{plan.get('fat_target_g')}g fat")
    
    if plan.get('dietary_restrictions'):
        st.markdown(f"**Dietary Restrictions:** {plan.get('dietary_restrictions')}")
    
    # Group meals by day
    meals_by_day = {}
    for meal in plan.get('meals', []):
        day = meal.get('day_number', 1)
        if day not in meals_by_day:
            meals_by_day[day] = []
        meals_by_day[day].append(meal)
    
    # Display meals by day
    for day in sorted(meals_by_day.keys()):
        with st.expander(f"Day {day}"):
            day_meals = meals_by_day[day]
            
            for meal in day_meals:
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**{meal.get('meal_type')}: {meal.get('recipe_name')}**")
                    st.markdown(f"*Ingredients:* {meal.get('ingredients')}")
                    st.markdown(f"*Instructions:* {meal.get('instructions')}")
                
                with col2:
                    st.markdown(f"**Nutrition (per serving)**")
                    st.markdown(f"Calories: {meal.get('calories_per_serving', 0)}")
                    st.markdown(f"Protein: {meal.get('protein_g', 0)}g")
                    st.markdown(f"Carbs: {meal.get('carbs_g', 0)}g")
                    st.markdown(f"Fat: {meal.get('fat_g', 0)}g")
                
                st.markdown("---")
    
    # Display shopping list if available
    if plan.get('shopping_list'):
        st.markdown("### 🛒 Shopping List")
        shopping_items = plan.get('shopping_list', [])
        
        # Group by category
        by_category = {}
        for item in shopping_items:
            category = item.get('category', 'Other')
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(item)
        
        for category, items in by_category.items():
            st.markdown(f"**{category}:**")
            for item in items:
                quantity = item.get('quantity', '')
                unit = item.get('unit', '')
                name = item.get('item_name', '')
                st.markdown(f"• {quantity} {unit} {name}".strip())
def show_diet_plan_details(plan_id: int):
    """Display detailed information for a specific diet plan."""
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()

            # Get plan metadata
            cursor.execute("""
                SELECT * FROM diet_plans
                WHERE id = ?
            """, (plan_id,))
            plan = cursor.fetchone()
            if not plan:
                st.error("Diet plan not found")
                return

            st.header(f"🍲 {plan['name']}")
            st.write(f"**Calorie Target:** {plan['calorie_target']}")
            st.write(f"**Protein Target:** {plan['protein_target_g']}g")
            st.write(f"**Carbs Target:** {plan['carb_target_g']}g")
            st.write(f"**Fat Target:** {plan['fat_target_g']}g")
            st.write(f"**Dietary Restrictions:** {plan['dietary_restrictions'] or 'None'}")
            st.write(f"**Created:** {plan['created_at']}")
            if plan['ai_generated']:
                st.success("🤖 AI Generated")

            # Get meal plan details
            cursor.execute("""
                SELECT day_number, meal_type, recipe_name, ingredients,
                       instructions, calories_per_serving, protein_g, carbs_g,
                       fat_g, servings
                FROM meal_plans
                WHERE diet_plan_id = ?
                ORDER BY day_number, meal_type
            """, (plan_id,))
            meal_plans = [dict(row) for row in cursor.fetchall()]

            if not meal_plans:
                st.info("No meal details found for this plan.")
                return

            # Group meals by day
            days = {}
            for meal in meal_plans:
                day = meal['day_number']
                if day not in days:
                    days[day] = []
                days[day].append(meal)

            # Display each day's meals in tabs
            day_tabs = st.tabs([f"Day {day}" for day in sorted(days.keys())])
            for i, (day, meals) in enumerate(sorted(days.items())):
                with day_tabs[i]:
                    st.markdown(f"### Day {day}")
                    for meal in meals:
                        with st.expander(f"{meal['meal_type']}: {meal['recipe_name']}", expanded=False):
                            st.write(f"**Ingredients:**")
                            st.write(meal['ingredients'])
                            st.write(f"**Instructions:**")
                            st.write(meal['instructions'])
                            st.write(f"**Servings:** {meal['servings']}")
                            st.write(f"**Calories per serving:** {meal['calories_per_serving']}")
                            st.write(f"**Protein:** {meal['protein_g']}g")
                            st.write(f"**Carbs:** {meal['carbs_g']}g")
                            st.write(f"**Fat:** {meal['fat_g']}g")

            # Display shopping list if available
            cursor.execute("""
                SELECT item_name, quantity, unit, category
                FROM shopping_lists
                WHERE diet_plan_id = ?
                ORDER BY category, item_name
            """, (plan_id,))
            shopping_list = [dict(row) for row in cursor.fetchall()]

            if shopping_list:
                with st.expander("🛒 Shopping List", expanded=False):
                    categories = {}
                    for item in shopping_list:
                        cat = item['category']
                        if cat not in categories:
                            categories[cat] = []
                        categories[cat].append(item)
                    for category, items in categories.items():
                        st.markdown(f"**{category}**")
                        for item in items:
                            st.write(f"- {item['item_name']}: {item['quantity']} {item['unit']}")
    except Exception as e:
        st.error(f"Error loading diet plan details: {e}")

def delete_diet_plan(plan_id: int) -> bool:
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            # Delete related meal plans
            cursor.execute("DELETE FROM meal_plans WHERE diet_plan_id = ?", (plan_id,))
            # Delete related shopping list items
            cursor.execute("DELETE FROM shopping_lists WHERE diet_plan_id = ?", (plan_id,))
            # Delete the diet plan itself
            cursor.execute("DELETE FROM diet_plans WHERE id = ?", (plan_id,))
            conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error deleting diet plan {plan_id}: {e}")
        return False
