import json
import os
import re
from dotenv import load_dotenv
from pydantic import ValidationError
from groq import (Groq, GroqError,
    AuthenticationError, RateLimitError,
    APIConnectionError, APITimeoutError, BadRequestError,
)

from schemas import WorkoutPlan, WorkoutPlanResponse, strict_json_schema

load_dotenv()


class PlanGenerationError(Exception):
    """Something stopped us returning a plan. str(error) is a friendly message for the UI."""


class InvalidInputError(PlanGenerationError):
    """The user's inputs are invalid. str(error) is a friendly message for the UI."""


api_key = os.getenv("GROQ_API_KEY")
# Created only when a key exists, so a missing key shows a friendly message instead of crashing the page.
client = Groq(api_key=api_key) if api_key else None
model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

# "strict" = Groq Structured Outputs with strict: true (the model can only produce JSON matching
#            the schema). Supported by openai/gpt-oss-20b and openai/gpt-oss-120b.
# "json_object" = older JSON mode (valid JSON, but the schema is only described in the prompt).
RESPONSE_MODE = os.getenv("GROQ_RESPONSE_MODE", "strict")

# Room for the model's reasoning plus a full 7-day plan. Without it, gpt-oss-20b often ran out of tokens
# mid-plan. Set GROQ_MAX_COMPLETION_TOKENS=none to use Groq's default instead.
_tokens = os.getenv("GROQ_MAX_COMPLETION_TOKENS", "8192")
MAX_COMPLETION_TOKENS: int | None = None if _tokens.lower() == "none" else int(_tokens)


def build_response_format() -> dict:
    """Return the response_format for the Groq call, based on RESPONSE_MODE."""
    if RESPONSE_MODE == "json_object":
        return {"type": "json_object"}
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "workout_plan",
            "schema": strict_json_schema(WorkoutPlanResponse),
            "strict": True,
        },
    }

SYSTEM_PROMPT = """You are a professional fitness coach creating personalized weekly workout plans.

Rules:
- Use ONLY the equipment the user lists, in exercises AND in safety_notes.
  "No equipment" = bodyweight only: no machines, barbells, dumbbells, kettlebells, bands, or added weight.
  Household items (chair, wall, step) are allowed for no-equipment plans.
  "Home dumbbells" = dumbbells and bodyweight only, no barbells or machines.
- Never include exercises that load a reported injury or limitation; substitute safer alternatives.
- Every workout day has a warm-up and cool-down (5-10 min each).
- Balance push/pull movements; match volume and difficulty to experience level.
- Schedule exactly the number of workout and rest days requested, spreading rest days for recovery.
- You are not a medical professional: no diagnoses, treatment advice, or medical claims.
- If the user reports any injuries or limitations, safety_notes MUST begin with:
  "Consult a doctor or physiotherapist before starting this plan, given your reported limitations."

Output: return ONLY a single JSON object (no wrapper key) with these top-level keys:
- safety_notes: string
- plan_name: string
- fitness_goal: string
- experience: "beginner" | "intermediate" | "advanced"
- workout_days: integer
- rest_days: integer
- weekly_schedule: list of 7 objects, one per day Monday-Sunday, each with:
    - day: "Monday" ... "Sunday" (each exactly once)
    - type: "workout" | "rest"
    - warmup: string
    - exercises: list of {name: string, sets: int >= 1, reps: string, rest_seconds: int >= 0}
      (empty list on rest days; at least one exercise on workout days)
    - cooldown: string
"""


# Words that must NOT appear in a plan, per equipment choice.
BANNED_EQUIPMENT_WORDS = {
    "No equipment": [
        "machine", "leg press", "barbell", "dumbbell", "cable",
        "kettlebell", "band", "smith", "weighted", "plate",
    ],
    "Home dumbbells": [
        "machine", "leg press", "barbell", "cable", "smith",
    ],
}


def find_equipment_violations(plan: WorkoutPlan, workout: WorkoutPlanResponse) -> list[str]:
    """Return banned equipment words found in the generated plan."""
    # "Full gym" allows everything, so no check.
    if "Full gym" in plan.equipment_access:
        return []

    # Only words banned under EVERY selected option are disallowed
    # (e.g. "No equipment" + "Home dumbbells" still allows dumbbells).
    banned_sets = [set(BANNED_EQUIPMENT_WORDS[e]) for e in plan.equipment_access]
    banned = set.intersection(*banned_sets)

    texts = [workout.safety_notes]
    for day in workout.weekly_schedule:
        texts += [day.warmup, day.cooldown]
        texts += [exercise.name for exercise in day.exercises]
    # Treat hyphens (incl. non-breaking ones) as spaces so "leg-press" matches "leg press".
    combined = re.sub(r"[-\u2010\u2011\u2012\u2013]", " ", " ".join(texts).lower())

    return sorted(
        word for word in banned
        if re.search(rf"\b{re.escape(word)}(?:s|es)?\b", combined)
    )


def create_workout_plan(plan: WorkoutPlan) -> WorkoutPlanResponse:
    """Build the prompt from a validated WorkoutPlan, call Groq, and return a validated plan.

    Raises PlanGenerationError with a user-friendly message on any API or output failure.
    """
    if client is None:
        raise PlanGenerationError("The app is missing its GROQ_API_KEY. Add it to the .env file and restart.")
    try:
        workout_days = min(plan.days_available, 6)
        rest_days = 7 - workout_days

        user_prompt = "\n".join([
            "Create a weekly workout plan for this user:",
            f"- Goal: {plan.fitness_goal}",
            f"- Experience: {plan.experience}",
            f"- Workout days: exactly {workout_days}; rest days: exactly {rest_days}",
            f"- Equipment: {', '.join(plan.equipment_access)}",
            f"- Injuries/limitations: {', '.join(plan.optional) or 'none'}",
        ])

        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
                response_format=build_response_format(),
                **({"max_completion_tokens": MAX_COMPLETION_TOKENS} if MAX_COMPLETION_TOKENS else {}),
            )
        # reference -https://github.com/groq/groq-python
        except AuthenticationError as e:
            print("Groq auth failed:", e)
            raise PlanGenerationError("The AI service rejected our API key. Please check GROQ_API_KEY.") from e
        except RateLimitError as e:
            print("Groq rate limit:", e)
            raise PlanGenerationError("Too many requests right now. Please wait a minute and try again.") from e
        except APITimeoutError as e:
            print("Groq timeout:", e)
            raise PlanGenerationError("The AI took too long to respond. Please try again.") from e
        except APIConnectionError as e:
            print("Groq unreachable:", e.__cause__)
            raise PlanGenerationError("Couldn't reach the AI service. Check your internet connection.") from e
        except BadRequestError as e:
            print("Groq bad request:", e)
            raise PlanGenerationError("The AI returned an unusable response. Please try again.") from e
        except GroqError as e:
            print("Groq error:", e)
            raise PlanGenerationError("Something went wrong with the AI service. Please try again.") from e

        raw_answer = response.choices[0].message.content

        if not raw_answer:
            raise ValueError("Groq returned an empty response")

        data = json.loads(raw_answer)

        # Some models wrap the plan in an extra key, e.g. {"WorkoutPlanResponse": {...}}
        if isinstance(data, dict) and "plan_name" not in data and len(data) == 1:
            data = next(iter(data.values()))

        workout = WorkoutPlanResponse.model_validate(data)

        if workout.workout_days != workout_days:
            raise ValueError("Incorrect number of workout days")

        if workout.rest_days != rest_days:
            raise ValueError("Incorrect number of rest days")

        violations = find_equipment_violations(plan, workout)
        if violations:
            raise ValueError(
                f"Plan uses equipment the user doesn't have: {', '.join(violations)}"
            )

        return workout

    except (ValueError, ValidationError) as e:
        print("Bad LLM output:", e)
        raise PlanGenerationError(
            "The AI returned an incomplete plan. Please click Generate again."
        ) from e


def generate_workout_plan(
    fitness_goal: str,
    experience: str,
    days_available: int,
    equipment_access: list[str],
    limitations: list[str] | None = None,
) -> WorkoutPlanResponse:
    """Entry point that takes the structured inputs as parameters.

    Validates them (InvalidInputError with a friendly message on bad input), then builds the
    prompt and calls Groq via create_workout_plan().
    """
    try:
        plan = WorkoutPlan(
            fitness_goal=fitness_goal,
            experience=experience,
            days_available=days_available,
            equipment_access=equipment_access,
            optional=limitations or [],
        )
    except ValidationError as e:
        print("Invalid input:", e)
        reason = e.errors()[0]["msg"].removeprefix("Value error, ")
        raise InvalidInputError(f"Some inputs are invalid: {reason}") from e

    return create_workout_plan(plan)
