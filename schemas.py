
from typing import Literal
from pydantic import BaseModel, Field, field_validator, model_validator


# 1. USER INPUT MODEL
class WorkoutPlan(BaseModel):
    fitness_goal: str = Field(
        description="Goal: build muscle, lose fat, general fitness, or improve endurance"
    )

    experience: Literal[
        "beginner", "intermediate", "advanced"
    ]

    days_available: int = Field(
        ge=1,
        le=7,
        description="Days available per week for workouts"
    )

    equipment_access: list[
        Literal["No equipment", "Home dumbbells", "Full gym"]
    ] = Field(min_length=1)

    optional: list[str] = Field(
        default_factory=list,
        description="Injuries or exercise limitations"
    )

    @field_validator("fitness_goal")
    @classmethod
    def validate_goal(cls, value: str) -> str:
        value = value.strip().lower()

        allowed_goals = [
            "build muscle",
            "lose fat",
            "general fitness",
            "improve endurance"
        ]

        if value not in allowed_goals:
            raise ValueError(
                f"Goal must be one of: {', '.join(allowed_goals)}"
            )

        return value

    @field_validator("optional")
    @classmethod
    def validate_limitations(cls, values: list[str]) -> list[str]:
        cleaned = [
            item.strip()
            for item in values
            if item.strip()
        ]

        if len(cleaned) > 5:
            raise ValueError(
                "Maximum 5 limitations allowed"
            )

        return cleaned


# 2. EXERCISE MODEL
class Exercise(BaseModel):
    name: str
    sets: int = Field(ge=1)
    reps: str
    rest_seconds: int = Field(ge=0)


# 3. DAILY WORKOUT MODEL
class WorkoutDay(BaseModel):
    day: Literal[
        "Monday", "Tuesday", "Wednesday",
        "Thursday", "Friday", "Saturday", "Sunday"
    ]

    type: Literal["workout", "rest"]

    warmup: str = ""
    exercises: list[Exercise] = Field(default_factory=list)
    cooldown: str = ""


# 4. AI RESPONSE MODEL
class WorkoutPlanResponse(BaseModel):
    plan_name: str = Field(
        description="Name of the generated workout plan"
    )

    fitness_goal: str

    experience: Literal[
        "beginner", "intermediate", "advanced"
    ]

    workout_days: int = Field(ge=1, le=6)
    rest_days: int = Field(ge=1, le=6)

    weekly_schedule: list[WorkoutDay]

    safety_notes: str

    @model_validator(mode="after")
    def validate_schedule(self):
        if self.workout_days + self.rest_days != 7:
            raise ValueError(
                "Workout days and rest days must total 7"
            )

        if len(self.weekly_schedule) != 7:
            raise ValueError(
                "Weekly schedule must contain exactly 7 days"
            )

        days = [day.day for day in self.weekly_schedule]

        if len(set(days)) != 7:
            raise ValueError(
                "Each weekday must appear exactly once"
            )

        workout_count = sum(
            day.type == "workout"
            for day in self.weekly_schedule
        )

        rest_count = sum(
            day.type == "rest"
            for day in self.weekly_schedule
        )

        if workout_count != self.workout_days:
            raise ValueError(
                "Workout day count does not match schedule"
            )

        if rest_count != self.rest_days:
            raise ValueError(
                "Rest day count does not match schedule"
            )

        for day in self.weekly_schedule:
            if day.type == "rest" and day.exercises:
                raise ValueError(
                    f"{day.day} is a rest day and cannot contain exercises"
                )

            if day.type == "workout" and not day.exercises:
                raise ValueError(
                    f"{day.day} is a workout day and must contain exercises"
                )

        return self






    
    

# 5. STRICT JSON SCHEMA FOR GROQ STRUCTURED OUTPUTS
# Groq's strict mode (https://console.groq.com/docs/structured-outputs) requires:
#   - every property listed in "required"
#   - "additionalProperties": false on every object
# Pydantic's default schema breaks both (fields with defaults aren't required), and adds
# keywords like "default"/"minimum" that strict mode may not support. This converts it.
# The Pydantic models above still run afterwards to enforce the rules a schema can't express
# (days add up to 7, each weekday once, no exercises on rest days, etc.).
_UNSUPPORTED_STRICT_KEYWORDS = {
    "default", "title",
    "minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum",
    "minLength", "maxLength", "minItems", "maxItems", "pattern",
}


def _make_strict(node):
    """Recursively rewrite a JSON schema node to satisfy Groq strict mode."""
    if isinstance(node, list):
        return [_make_strict(item) for item in node]
    if not isinstance(node, dict):
        return node

    strict = {
        key: _make_strict(value)
        for key, value in node.items()
        if key not in _UNSUPPORTED_STRICT_KEYWORDS
    }
    if "properties" in strict:  # it's an object schema
        strict["required"] = list(strict["properties"].keys())
        strict["additionalProperties"] = False
    return strict


def strict_json_schema(model: type[BaseModel]) -> dict:
    """Return a Groq strict-mode compatible JSON schema for a Pydantic model."""
    return _make_strict(model.model_json_schema())
