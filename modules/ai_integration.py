
import os
import json
import logging
from typing import Dict, Any, Optional, List
from google import genai
from google.genai import types
import streamlit as st
from dotenv import load_dotenv
load_dotenv()
logger = logging.getLogger(__name__)

class GeminiClient:
    """Handles Gemini API interactions for fitness and nutrition planning."""
    
    def __init__(self):
        """Initialize the Gemini client."""
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not found in environment variables")
            return
            
        try:
            self.client = genai.Client(api_key=self.api_key)
            logger.info("Gemini client initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Gemini client: {e}")
            self.client = None
    
    def is_available(self) -> bool:
        """Check if Gemini API is available."""
        return self.client is not None and self.api_key is not None
    
    def generate_workout_plan(self, user_profile: Dict[str, Any], 
                            preferences: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """
        Generate a personalized workout plan using Gemini.
        
        Args:
            user_profile: User's physical and fitness profile
            preferences: Additional workout preferences
            
        Returns:
            Generated workout plan or None if failed
        """
        if not self.is_available():
            logger.error("Gemini API not available")
            return None
        
        try:
            prompt = self._create_workout_prompt(user_profile, preferences)
            
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    top_p=0.9,
                )
            )
            # Parse the response
            workout_plan = self._parse_workout_response(response.text)
            if workout_plan:
                workout_plan['gemini_prompt'] = prompt[:500]  # Store truncated prompt
                logger.info("Workout plan generated successfully")
                workout_plan['name']=preferences['name']
                return workout_plan
            else:
                logger.error("Failed to parse workout plan response")
                return None
                
        except Exception as e:
            logger.error(f"Error generating workout plan: {e}")
            return None
    
    def generate_diet_plan(self, user_profile: Dict[str, Any], 
                          available_foods: List[str], 
                          dietary_goals: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Generate a personalized diet plan using Gemini.
        
        Args:
            user_profile: User's profile information
            available_foods: List of available food items
            dietary_goals: Dietary goals and restrictions
            
        Returns:
            Generated diet plan or None if failed
        """
        if not self.is_available():
            logger.error("Gemini API not available")
            return None
        
        try:
            prompt = self._create_diet_prompt(user_profile, available_foods, dietary_goals)
            
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    top_p=0.9,
                )
            )
            
            # Parse the response
            diet_plan = self._parse_diet_response(response.text)
            if diet_plan:
                diet_plan['gemini_prompt'] = prompt[:500]
                diet_plan['name']=dietary_goals['name']
                logger.info("Diet plan generated successfully")
                return diet_plan
            else:
                logger.error("Failed to parse diet plan response")
                return None
                
        except Exception as e:
            logger.error(f"Error generating diet plan: {e}")
            return None
    
    def get_fitness_advice(self, question: str, user_context: Dict[str, Any] = None) -> Optional[str]:
        """
        Get fitness advice using Gemini.
        
        Args:
            question: User's fitness question
            user_context: Optional user context for personalized advice
            
        Returns:
            AI-generated advice or None if failed
        """
        if not self.is_available():
            return "Gemini API is not available. Please configure GEMINI_API_KEY."
        
        try:
            prompt = self._create_advice_prompt(question, user_context)
            
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.8,
                    top_p=0.9,
                )
            )
            
            return response.text
            
        except Exception as e:
            logger.error(f"Error getting fitness advice: {e}")
            return f"Error getting advice: {str(e)}"
    
    def _create_workout_prompt(self, user_profile: Dict[str, Any], 
                              preferences: Dict[str, Any] = None) -> str:
        """Create a detailed workout generation prompt."""
        preferences = preferences or {}
        
        prompt = f"""
You are a certified personal trainer and exercise physiologist with over 15 years of experience. 
Create a comprehensive, personalized 4-week workout plan for the following client:

USER PROFILE:
- Age: {user_profile.get('age', 'Unknown')}
- Gender: {user_profile.get('gender', 'Unknown')}
- Height: {user_profile.get('height_cm', 'Unknown')} cm
- Weight: {user_profile.get('weight_kg', 'Unknown')} kg
- Activity Level: {user_profile.get('activity_level', 'Unknown')}
- Experience Level: {user_profile.get('experience_level', 'Beginner')}
- Fitness Goals: {user_profile.get('fitness_goals', 'General fitness')}
- Injuries/Limitations: {user_profile.get('injuries', 'None specified')}

WORKOUT PREFERENCES:
- Days per week: {preferences.get('days_per_week', 4)}
- Session duration: {preferences.get('session_duration', '45-60 minutes')}
- Preferred equipment: {preferences.get('equipment', 'Full gym access')}
- Workout type focus: {preferences.get('workout_type', 'Balanced strength and cardio')}

REQUIREMENTS:
1. Create a 4-week progressive program with weekly variations
2. Include 4-6 workouts per week (adjust based on experience level)
3. Provide specific exercises, sets, reps, and rest periods
4. Include proper warm-up and cool-down for each session
5. Consider the user's limitations and experience level
6. Progress difficulty appropriately over the 4 weeks
7. Include alternative exercises for accessibility

FORMAT YOUR RESPONSE AS JSON:
{{
    "name": "Personalized 4-Week Training Plan",
    "description": "Brief description of the plan approach",
    "duration_weeks": 4,
    "days": [
        {{
            "day_number": 1,
            "day_name": "Day 1: Upper Body Strength",
            "focus_area": "Upper body strength and muscle building",
            "exercises": [
                {{
                    "name": "Push-ups",
                    "category": "Strength",
                    "muscle_groups": "Chest, shoulders, triceps",
                    "equipment": "Bodyweight",
                    "difficulty_level": "Beginner",
                    "instructions": "Detailed step-by-step instructions",
                    "sets": 3,
                    "reps": "8-12",
                    "rest_seconds": 60,
                    "notes": "Modify on knees if needed"
                }}
            ]
        }}
    ]
}}

Provide a complete, detailed plan that follows these specifications exactly.
"""
        return prompt
    
    def _create_diet_prompt(self, user_profile: Dict[str, Any], 
                           available_foods: List[str], 
                           dietary_goals: Dict[str, Any]) -> str:
        """Create a detailed diet planning prompt."""
        
        prompt = f"""
        You are a registered dietitian and sports nutritionist with expertise in meal planning. 
        Create a comprehensive 7-day meal plan for the following client:

        USER PROFILE:
        - Age: {user_profile.get('age', 'Unknown')}
        - Gender: {user_profile.get('gender', 'Unknown')}
        - Height: {user_profile.get('height_cm', 'Unknown')} cm
        - Weight: {user_profile.get('weight_kg', 'Unknown')} kg
        - Activity Level: {user_profile.get('activity_level', 'Unknown')}
        - Fitness Goals: {user_profile.get('fitness_goals', 'General health')}

        AVAILABLE FOODS:
        {', '.join(available_foods) if available_foods else 'Standard grocery items'}

        DIETARY GOALS:
        - Calorie Target: {dietary_goals.get('calorie_target', 'Calculate based on profile')}
        - Protein Goal: {dietary_goals.get('protein_target', 'Calculate based on goals')}g
        - Carb Goal: {dietary_goals.get('carb_target', 'Balanced')}g
        - Fat Goal: {dietary_goals.get('fat_target', 'Balanced')}g
        - Dietary Restrictions: {dietary_goals.get('restrictions', 'None')}
        - Meal Frequency: {dietary_goals.get('meals_per_day', 3)} meals + {dietary_goals.get('snacks_per_day', 1)} snacks

        REQUIREMENTS:
        1. Create 7 days of complete meal plans
        2. Use primarily the available foods listed
        3. Include breakfast, lunch, dinner, and 1-2 snacks per day
        4. Provide detailed recipes with ingredients and portions
        5. Calculate nutritional information for each meal
        6. Create a shopping list for missing ingredients
        7. Ensure meals align with fitness goals
        8. Consider dietary restrictions

        FORMAT YOUR RESPONSE AS JSON:
        {{
            "name": "Personalized 7-Day Meal Plan",
            "calorie_target": 2000,
            "protein_target_g": 120,
            "carb_target_g": 250,
            "fat_target_g": 67,
            "dietary_restrictions": "None",
            "meals": [
                {{
                    "day_number": 1,
                    "meal_type": "Breakfast",
                    "recipe_name": "Protein Oatmeal Bowl",
                    "ingredients": "1 cup oats, 1 scoop protein powder, 1 banana, 2 tbsp almond butter",
                    "instructions": "Cook oats, mix in protein powder, top with sliced banana and almond butter",
                    "calories_per_serving": 450,
                    "protein_g": 25,
                    "carbs_g": 55,
                    "fat_g": 12,
                    "servings": 1
                }}
            ],
            "shopping_list": [
                {{
                    "item_name": "Quinoa",
                    "quantity": 2,
                    "unit": "cups",
                    "category": "Grains"
                }}
            ]
        }}

        Provide a complete, nutritionally balanced plan that maximizes the use of available foods.
        """
        return prompt
    
    def _create_advice_prompt(self, question: str, user_context: Dict[str, Any] = None) -> str:
        """Create a prompt for general fitness advice."""
        context_str = ""
        if user_context:
            context_str = f"""
USER CONTEXT:
- Goals: {user_context.get('fitness_goals', 'General fitness')}
- Experience: {user_context.get('experience_level', 'Beginner')}
- Current focus: {user_context.get('current_focus', 'Overall health')}
"""
        
        prompt = f"""
You are a certified personal trainer, nutritionist, and wellness coach. Provide helpful, 
evidence-based advice for the following fitness question. Be supportive, encouraging, 
and provide actionable recommendations.

{context_str}

QUESTION: {question}

Please provide a comprehensive answer that includes:
1. Direct response to the question
2. Practical tips and recommendations
3. Safety considerations if applicable
4. Encouragement and motivation

Keep your response informative but conversational and supportive.
"""
        return prompt
    
    def _parse_workout_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Parse the workout plan response from Gemini."""
            # Try to extract JSON from the response
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1
        
        if start_idx != -1 and end_idx != -1:
            json_str = response_text[start_idx:end_idx]
            workout_plan = json.loads(json_str)
            
            # Validate structure
            required_fields = ['name', 'description', 'days']
            if all(field in workout_plan for field in required_fields):
                return workout_plan
            
            # If JSON parsing fails, create a structured plan from text
            logger.warning("JSON parsing failed, creating fallback workout plan")
            return self._create_fallback_workout_plan(response_text)
            
    
    def _parse_diet_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Parse the diet plan response from Gemini."""
        try:
            # Try to extract JSON from the response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response_text[start_idx:end_idx]
                diet_plan = json.loads(json_str)
                
                # Validate structure
                required_fields = ['name', 'meals']
                if all(field in diet_plan for field in required_fields):
                    return diet_plan
            
            # If JSON parsing fails, create a structured plan from text
            logger.warning("JSON parsing failed, creating fallback diet plan")
            return self._create_fallback_diet_plan(response_text)
            
        except Exception as e:
            logger.error(f"Error parsing diet response: {e}")
            return None
    
    def _create_fallback_workout_plan(self, response_text: str) -> Dict[str, Any]:
        """Create a fallback workout plan when JSON parsing fails."""
        return {
            "name": "AI-Generated Workout Plan",
            "description": "Custom workout plan generated by AI",
            "duration_weeks": 4,
            "ai_generated": True,
            "days": [
                {
                    "day_number": 1,
                    "day_name": "Full Body Workout",
                    "focus_area": "General fitness",
                    "exercises": [
                        {
                            "name": "Push-ups",
                            "category": "Strength",
                            "muscle_groups": "Chest, shoulders, triceps",
                            "equipment": "Bodyweight",
                            "difficulty_level": "Beginner",
                            "instructions": "Standard push-up form",
                            "sets": 3,
                            "reps": "8-12",
                            "rest_seconds": 60,
                            "notes": "Modify as needed"
                        }
                    ]
                }
            ],
            "raw_response": response_text[:1000]  # Store part of original response
        }
    
    def _create_fallback_diet_plan(self, response_text: str) -> Dict[str, Any]:
        """Create a fallback diet plan when JSON parsing fails."""
        return {
            "name": "AI-Generated Meal Plan",
            "calorie_target": 2000,
            "protein_target_g": 120,
            "carb_target_g": 250,
            "fat_target_g": 67,
            "dietary_restrictions": "None specified",
            "ai_generated": True,
            "meals": [
                {
                    "day_number": 1,
                    "meal_type": "Breakfast",
                    "recipe_name": "Balanced Breakfast",
                    "ingredients": "Oats, protein powder, banana, berries",
                    "instructions": "Combine ingredients for a nutritious start",
                    "calories_per_serving": 400,
                    "protein_g": 25,
                    "carbs_g": 45,
                    "fat_g": 8,
                    "servings": 1
                }
            ],
            "shopping_list": [],
            "raw_response": response_text[:1000]  # Store part of original response
        }


# Create a global Gemini client instance
gemini_client = GeminiClient()
