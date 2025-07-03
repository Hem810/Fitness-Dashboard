# Fitness-Dashboard
LLM based personal workout and diet plan generator
## Table of Contents
1. [About](#about)
2. [Features](#features)
3. [Setup](#setup)
4. [Run](#run)

## About
Fitness Dashboard is an AI-powered web application that leverages Large Language Models (LLMs) to generate personalized workout routines and diet plans. The platform is designed to help users achieve their fitness goals efficiently by providing tailored recommendations based on individual preferences, goals, and constraints.
## Features
Personalized Workout Plans: Generate custom exercise routines based on user input such as fitness goals, experience level, available equipment, and time constraints.
Diet Plan Generator: Receive meal suggestions and nutrition plans tailored to dietary preferences, restrictions, and caloric goals.
LLM Integration: Utilizes advanced language models to interpret user requirements and generate actionable fitness and nutrition advice.
User-Friendly Interface: Simple and intuitive dashboard for entering preferences and viewing generated plans.
Progress Tracking: Monitors the change in body metrices over time

## Setup
 1. git clone repo
      ```
      >>https://github.com/Hem810/Fitness-Dashboard
      ```
   2. Create virtual environment
      ```
      >> python -m virtual_env venv
      ```
   3. Activate virtual environment
      ```
      >> venv\Scripts\activate 
      ```
   4. Install dependencies
      ```
      >> pip install -r requirements.txt
      ```
   5. Add your Google Gemini key in the .env file

## Run
To run the application
```
streamlit run app.py
```

