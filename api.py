import os
from dotenv import load_dotenv
from fastapi import FastAPI

from schemas import WorkoutPlan, WorkoutPlanResponse
from main import generate_workout_plan

load_dotenv()

app = FastAPI(title="Workout Plan")

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise RuntimeError("Missing GROQ_API_KEY in environment")


@app.get("/")
def home() -> dict:
    return {"message": "Welcome to your workout planning"}


@app.post("/workout", response_model=WorkoutPlanResponse)
def generate_workout(plan: WorkoutPlan) -> WorkoutPlanResponse:
    """Receive the user's inputs and return a generated weekly plan."""
    return generate_workout_plan(
        fitness_goal=plan.fitness_goal,
        experience=plan.experience,
        days_available=plan.days_available,
        equipment_access=plan.equipment_access,
        limitations=plan.optional,
    )
