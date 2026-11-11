
import json
from datetime import datetime
import streamlit as st
import requests
import re  




st.title("AI Workout Plan Generator")

API_URL = "http://127.0.0.1:8001/workout"

# ---------- Inputs (each has a key, so the callback can read it) ----------
st.selectbox(
    "What is your fitness goal?",
    ["Build muscle", "Lose fat", "General fitness", "Improve endurance"],
    key="fitness_goal",
)

st.selectbox(
    "Experience level",
    ["beginner", "intermediate", "advanced"],
    key="experience",
)

st.slider("Days available per week", min_value=1, max_value=7, value=3, key="days_available")

st.multiselect(
    "Equipment available",
    ["No equipment", "Home dumbbells", "Full gym"],
    key="equipment_access",
)

st.text_area(
    "Injuries or limitations (optional)",
    placeholder="e.g. bad knees, no overhead pressing",
    key="limitations_text",
)


# ---------- Helpers ----------
def build_payload() -> dict:
    """Read the current widget values from session state and build the API request body."""
    text = st.session_state.limitations_text
    limitations = [s.strip() for s in text.split(",") if s.strip()] if text else []
    return {
        "fitness_goal": st.session_state.fitness_goal,
        "experience": st.session_state.experience,
        "days_available": st.session_state.days_available,
        "equipment_access": st.session_state.equipment_access,
        "optional": limitations,
    }


def generate_plan(is_regenerate: bool = False) -> None:
    """Button callback: call the API and save the plan (or an error message) in session state.

    is_regenerate=True keeps the current plan as `previous_workout` so the page can show what changed.
    """
    st.session_state.message = None  # clear the previous message

    if not st.session_state.equipment_access:
        st.session_state.message = ("warning", "Please select your equipment.")
        return

    try:
        response = requests.post(API_URL, json=build_payload(), timeout=60)
        response.raise_for_status()
        new_workout = response.json()

        if is_regenerate and "workout" in st.session_state:
            st.session_state.previous_workout = st.session_state.workout
            st.session_state.plan_version = st.session_state.get("plan_version", 1) + 1
            message = f"Plan regenerated! (version {st.session_state.plan_version})"
        else:
            st.session_state.pop("previous_workout", None)  # a fresh Generate starts over
            st.session_state.plan_version = 1
            message = "Plan generated!"

        st.session_state.workout = new_workout
        st.session_state.generated_at = datetime.now().strftime("%H:%M:%S")
        st.session_state.message = ("success", message)
    except requests.exceptions.Timeout:
        st.session_state.message = ("error", "The plan is taking too long to generate. Please try again.")
    except requests.exceptions.ConnectionError:
        st.session_state.message = ("error", f"Could not connect to the API. Make sure it's running on {API_URL}")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 422:
            text = "Some inputs are invalid. Please check your selections (max 5 limitations)."
        elif e.response.status_code == 404:
            text = "The workout API wasn't found at this address. Is the right server running on port 8001?"
        else:
            try:
                text = e.response.json().get("detail", "Something went wrong.")
            except ValueError:
                text = "Something went wrong. Please try again."
        st.session_state.message = ("error", text)
    except Exception:
        st.session_state.message = ("error", "Something unexpected went wrong. Please try again.")


def plan_to_markdown(workout: dict) -> str:
    """Convert the plan into a readable Markdown text file."""
    lines = [
        f"# {workout['plan_name']}",
        "",
        f"- Goal: {workout['fitness_goal']}",
        f"- Experience: {workout['experience']}",
        f"- Workout days: {workout['workout_days']}",
        f"- Rest days: {workout['rest_days']}",
        "",
    ]
    for day in workout["weekly_schedule"]:
        lines.append(f"## {day['day']} — {day['type'].title()}")
        if day["type"] == "rest":
            lines.append("Recovery day")
        else:
            lines.append(f"**Warm-up:** {day['warmup']}")
            lines.append("")
            for ex in day["exercises"]:
                reps = ex["reps"]
                reps_text = f"{reps} reps" if re.fullmatch(r"[\d\s\-\u2010-\u2013]+", reps) else reps
                sets_word = "set" if ex["sets"] == 1 else "sets"
                lines.append(f"- {ex['name']}: {ex['sets']} {sets_word} × {reps_text}, {ex['rest_seconds']}s rest")
            lines.append("")
            lines.append(f"**Cool-down:** {day['cooldown']}")
        lines.append("")
    lines.append("## Safety notes")
    lines.append(workout["safety_notes"])
    return "\n".join(lines)


def plan_changes(old: dict, new: dict) -> list[str]:
    """Describe day-by-day differences in exercises between two plans."""
    old_days = {d["day"]: d for d in old["weekly_schedule"]}
    changes = []
    for day in new["weekly_schedule"]:
        before = old_days.get(day["day"], {"type": "rest", "exercises": []})
        if before["type"] != day["type"]:
            changes.append(f"**{day['day']}:** {before['type']} → {day['type']}")
            continue
        old_names = {e["name"] for e in before["exercises"]}
        new_names = {e["name"] for e in day["exercises"]}
        added, removed = sorted(new_names - old_names), sorted(old_names - new_names)
        if added or removed:
            parts = []
            if added:
                parts.append("added " + ", ".join(added))
            if removed:
                parts.append("removed " + ", ".join(removed))
            changes.append(f"**{day['day']}:** " + "; ".join(parts))
    return changes


# ---------- Button + status message ----------
col_generate, col_regenerate = st.columns(2)
with col_generate:
    st.button("Generate Plan", on_click=generate_plan, type="primary")
with col_regenerate:
    # Only offer "Regenerate" once a plan exists; it re-runs the same request for a fresh plan.
    if "workout" in st.session_state:
        st.button("🔄 Regenerate Plan", on_click=generate_plan, kwargs={"is_regenerate": True})

if st.session_state.get("message"):
    kind, text = st.session_state.message
    {"success": st.success, "warning": st.warning, "error": st.error}[kind](text)


if "workout" in st.session_state:
    workout = st.session_state.workout

    st.subheader(workout["plan_name"])
    st.caption(
        f"Version {st.session_state.get('plan_version', 1)} · "
        f"generated at {st.session_state.get('generated_at', '—')}"
    )

    if "previous_workout" in st.session_state:
        with st.expander("What changed vs the previous version"):
            changes = plan_changes(st.session_state.previous_workout, workout)
            if changes:
                for change in changes:
                    st.markdown(f"- {change}")
            else:
                st.write("Same exercises as before (sets, reps or notes may differ).")

    st.write(f"Workout days: {workout['workout_days']}")
    st.write(f"Rest days: {workout['rest_days']}")

    for day in workout["weekly_schedule"]:
        with st.expander(f"{day['day']} — {day['type'].title()}"):
            if day["type"] == "rest":
                st.write("Recovery day")
            else:
                st.write(f"Warm-up: {day['warmup']}")

                for exercise in day["exercises"]:
                    reps = exercise["reps"]
                    reps_text = f"{reps} reps" if re.fullmatch(r"[\d\s\-\u2010-\u2013]+", reps) else reps
                    st.write(
                        f"{exercise['name']}: "
                        f"{exercise['sets']} {'set' if exercise['sets'] == 1 else 'sets'} × {reps_text}, "
                        f"{exercise['rest_seconds']}s rest"
                    )

                st.write(f"Cool-down: {day['cooldown']}")

    st.info(workout["safety_notes"])

    # ---------- Download ----------
    st.subheader("Download your plan")
    file_format = st.radio(
        "File format",
        ["Text (Markdown)", "JSON"],
        horizontal=True,
        key="download_format",
    )
    file_stem = re.sub(r"[^a-z0-9]+", "_", workout["plan_name"].lower()).strip("_") or "workout_plan"
    if file_format == "JSON":
        data = json.dumps(workout, indent=2, ensure_ascii=False)
        file_name, mime = f"{file_stem}.json", "application/json"
    else:
        data = plan_to_markdown(workout)
        file_name, mime = f"{file_stem}.md", "text/markdown"

    st.download_button(
        "Download plan",
        data=data,
        file_name=file_name,
        mime=mime,
    )

  