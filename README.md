# AI Workout Plan Generator: Pydantic version

A Streamlit app that turns structured inputs (fitness goal, experience, days per week, equipment, injuries) into a personalized weekly workout plan using an LLM on the [Groq API](https://console.groq.com/docs/api-reference).

This version uses **Pydantic** to validate both sides of the LLM call (the user's inputs before the prompt is built, and the model's JSON after it returns) and **Groq Structured Outputs** (strict JSON schema) so the model's response always has the right shape.

---

## How it works

```
┌───────────────┐   POST /workout    ┌───────────┐      ┌────────────────────────────┐      ┌──────────┐
│ app.py        │ ─────────────────▶ │ api.py    │ ───▶ │ main.py                    │ ───▶ │ Groq API │
│ Streamlit UI  │ ◀───────────────── │ FastAPI   │ ◀─── │ prompt + call + checks     │ ◀─── │ gpt-oss  │
└───────────────┘   plan JSON        └───────────┘      └────────────────────────────┘      └──────────┘
                                          │                          │
                                          └──── schemas.py (Pydantic models) ────┘
```

1. **Inputs**: the user fills in the form in `app.py` and clicks **Generate Plan**.
2. **Input validation**: FastAPI parses the request into the `WorkoutPlan` Pydantic model (1–7 days, allowed goals and equipment, max 5 limitations). Invalid input returns a 422, shown as a friendly message.
3. **Prompt**: `main.py` writes the rules into the **system prompt** and the user's details as labeled lines in the **user prompt**.
4. **LLM call**: Groq is called with a **strict JSON schema** generated from the `WorkoutPlanResponse` model.
5. **Output validation**: the response is parsed and checked by Pydantic (7 days, each weekday once, day counts match, no exercises on rest days), then by an equipment check in code.
6. **Display**: the plan is saved in `st.session_state` and shown day by day.

## Files

| File | Purpose |
|---|---|
| `app.py` | Streamlit page: inputs, Generate/Regenerate buttons, day-by-day display, download |
| `api.py` | FastAPI app exposing `POST /workout` |
| `main.py` | `generate_workout_plan()` (typed parameters) → `create_workout_plan()`: builds the prompt, calls Groq, runs the checks, maps errors to friendly messages |
| `schemas.py` | Pydantic models: `WorkoutPlan` (input), `WorkoutPlanResponse` / `WorkoutDay` / `Exercise` (output), and `strict_json_schema()` for Groq strict mode |
| `compare_models.py` | Runs 6 test cases across models and response modes and writes a comparison report |
| `report.md` | Prompt-design report: approach, test results, findings |

## What Pydantic does here

| Model | Checks |
|---|---|
| `WorkoutPlan` (input) | goal is one of 4 options · experience is beginner/intermediate/advanced · 1–7 days · at least one valid equipment option · at most 5 limitations (blank entries removed) |
| `WorkoutPlanResponse` (output) | all fields present and correctly typed · exactly 7 days, each weekday once · workout + rest days = 7 and match the schedule · rest days have no exercises, workout days have at least one · sets ≥ 1, rest ≥ 0 |
| `strict_json_schema()` | converts the output model into a schema Groq's strict mode accepts (every field required, `additionalProperties: false`, unsupported keywords removed) |

The strict schema guarantees the **structure**; Pydantic and the code checks still enforce the **rules** a schema can't express (e.g. day counts adding up, equipment limits).

## Prompt design

- **System prompt**: rules that apply to every user: use only the listed equipment (also in safety notes), avoid exercises that load reported injuries, warm-up and cool-down every workout day, match difficulty to experience, exact number of workout and rest days, **no medical claims**, and a **required disclaimer** when injuries are given:
  > "Consult a doctor or physiotherapist before starting this plan, given your reported limitations."
- **User prompt**: only this user's details, as labeled lines:
  ```
  Create a weekly workout plan for this user:
  - Goal: build muscle
  - Experience: beginner
  - Workout days: exactly 3; rest days: exactly 4
  - Equipment: No equipment
  - Injuries/limitations: bad knees
  ```
- **"The prompt asks, the code verifies"**: day counts and equipment rules are also checked in code, because the model doesn't always follow them.

## Setup

Requires Python 3.13+ and [uv](https://docs.astral.sh/uv/). The project's `pyproject.toml` and `uv.lock` are in the parent `workout_generator/` folder, and `uv` finds them automatically.

1. Create a `.env` file in the **parent `workout_generator/` folder** (or in this folder):
   ```
   GROQ_API_KEY=your_groq_key_here
   GROQ_MODEL=openai/gpt-oss-120b
   ```
   Optional: `GROQ_RESPONSE_MODE=json_object` switches from strict structured outputs back to the older JSON mode.
2. Install dependencies (from `workout_generator/`):
   ```bash
   uv sync
   ```

Never commit `.env`: it contains your API key and is listed in `.gitignore`.

## Run

Two terminals, both in this `pydnatic_version/` folder:

```bash
# Terminal 1: the API
uv run uvicorn api:app --reload --port 8001

# Terminal 2: the UI
uv run streamlit run app.py
```

Open the Local URL Streamlit prints (usually http://localhost:8501). The API docs are at http://127.0.0.1:8001/docs.

> Port 8001 is used because port 8000 is often taken by Docker or other dev servers. If you change it, update `API_URL` in `app.py`. `--reload` only watches `.py` files: restart uvicorn after editing `.env`.

## Features

- Structured inputs: goal, experience, days per week (1–7), equipment (multiselect), optional injuries/limitations (comma-separated)
- Day-by-day plan with warm-up, exercises (sets × reps, rest) and cool-down
- Safety notes, with a doctor/physiotherapist disclaimer whenever injuries are reported
- **Regenerate** button, with version number and a "What changed vs the previous version" comparison
- Last plan stored in `st.session_state`, so it persists across reruns
- **Download** the plan as Markdown or JSON

## Structured outputs (strict mode)

By default the Groq call uses [Structured Outputs](https://console.groq.com/docs/structured-outputs):

```python
response_format={
    "type": "json_schema",
    "json_schema": {
        "name": "workout_plan",
        "schema": strict_json_schema(WorkoutPlanResponse),
        "strict": True,
    },
}
```

In strict mode the model can only generate JSON that matches the schema (no missing fields, wrong types or invalid JSON). Both `openai/gpt-oss-20b` and `openai/gpt-oss-120b` support it.

## Error handling

| Situation | What the user sees |
|---|---|
| No equipment selected | "Please select your equipment." |
| Invalid input (e.g. 0 days, more than 5 limitations) | "Some inputs are invalid…" |
| Invalid / missing API key | "The AI service rejected our API key…" / server refuses to start |
| Rate limit (429) | "Too many requests right now…" |
| Groq timeout / network down | "The AI took too long…" / "Couldn't reach the AI service…" |
| Empty, malformed or rule-breaking LLM output | "The AI returned an incomplete plan. Please click Generate again." |
| API server not running | "Could not connect to the API…" |
| Request takes over 60 s | "The plan is taking too long to generate…" |

Technical details are printed in the uvicorn terminal for debugging; users only see friendly messages.

## Testing and model comparison

```bash
uv run python compare_models.py --token-limits 8192 none   # both models × both modes × both token settings
uv run python compare_models.py --runs 3 --pause 15 --out results_run2.md   # longer pause avoids the free-tier rate limit
```

Writes `model_comparison_strict.md` with, for each model and mode: valid plans, disclaimer correctness, injury-safe exercise choices and average response time.

**Results: every combination (6 tests × 2 runs each, best evidence from all runs):**

| Model | Mode | Max tokens | Valid plans |
|---|---|---|---|
| gpt-oss-20b | json_object | none | 4/12 |
| gpt-oss-20b | json_object | 8192 | **10/10** (+2 rate-limited) |
| gpt-oss-20b | strict | none | 4/12 (twice) |
| gpt-oss-20b | strict | 8192 | **11/11** (+1 rate-limited) |
| gpt-oss-120b | json_object | none | 11/12 (twice) |
| gpt-oss-120b | json_object | 8192 | **12/12** |
| gpt-oss-120b | strict | none | 12/12 (twice) |
| gpt-oss-120b | strict | 8192 | **12/12** |

- **The token limit mattered most for gpt-oss-20b:** without it, the model often ran out of tokens mid-plan; with 8192 it was reliable in both modes.
- **gpt-oss-120b was reliable in every configuration;** its only failure (JSON mode, no token limit) was a plan with fewer than 7 days, caught by Pydantic.
- **Strict structured outputs + `max_completion_tokens=8192` gave 100% for both models.** That's the app's setup, with `gpt-oss-120b` as the default model.
- On Groq's free tier, gpt-oss-20b hit the **daily token limit** partway through a 48-call run; requests refused for rate limits are not counted as model results.

Details in `report.md` (sections 2, 7, 8 and 9) and the `results_*.md` files.

## Known limitations

- The equipment and injury checks use word matching, so they can miss unusual exercise names or flag safe variations (e.g. "supported squat").
- Structured outputs guarantee the format, not the quality of the advice; subtle injury risks still depend on the model's judgment.
- The plan is kept only for the browser session; refreshing the page clears it (use **Download** to keep it).
- This is not medical advice; users with injuries are told to consult a professional.
