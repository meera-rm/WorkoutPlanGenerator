# Workout Plan Generator: Prompt Design Report

> Draft based on my test runs. Review and edit before submitting.

## 1. Approach

### Inputs → prompt
User inputs are validated with Pydantic (`WorkoutPlan`) and then written into the **user prompt** as labeled lines, not raw JSON:

```
Create a weekly workout plan for this user:
- Goal: build muscle
- Experience: beginner
- Workout days: exactly 3; rest days: exactly 4
- Equipment: No equipment
- Injuries/limitations: bad knees
```

Labeling matters: an early version sent the raw input JSON, where injuries appeared as `"optional": ["bad knees"]`, which gave the model no hint that these were injuries.

### System prompt vs user prompt
- **System prompt:** rules that apply to every user (equipment definitions, injury rule, warm-up/cool-down, no medical claims, conditional disclaimer, output JSON schema).
- **User prompt:** only this user's details.

An earlier version repeated the same rules in both places; removing the duplicates made the prompt shorter and avoided conflicting wording.

### "The prompt asks, the code verifies"
Prompt rules are not guarantees, so hard constraints are also checked in code:
- **Structure:** JSON mode + `WorkoutPlanResponse` validation (7 days, each weekday once, rest days have no exercises, workout days have at least one)
- **Day counts:** workout/rest days must match what was requested
- **Equipment:** banned-word check per equipment choice (e.g. "barbell", "machine", "leg press" for No equipment) across exercises, warm-ups, cool-downs and safety notes

Any failed check returns a friendly "please generate again" message.

## 2. Model choice: gpt-oss-20b vs gpt-oss-120b

I ran the same 6 test cases twice per model with `compare_models.py` (same prompt, same code checks). Full results: `model_comparison.md`.

| Test | 20b valid | 120b valid | 20b avg s | 120b avg s |
|---|---|---|---|---|
| 1. No equipment + bad knees | 1/2 | 2/2 | 2.8 | 4.2 |
| 2. Dumbbells + no overhead pressing | 0/2 | 2/2 | 2.6 | 5.9 |
| 3. Full gym, advanced, 7 days | 0/2 | 1/2 | 5.6 | 16.2 |
| 4. No equipment, beginner, 2 days | 2/2 | 2/2 | 12.4 | 14.5 |
| 5. Full gym + bad back, no running | 0/2 | 2/2 | 11.8 | 16.8 |
| 6. No equipment + Home dumbbells | 1/2 | 2/2 | 5.8 | 17.8 |
| **Total** | **4/12 (33%)** | **11/12 (92%)** | | |

**How 20b failed:**
- 5× Groq `json_validate_failed`: the model's output wasn't valid JSON. Once it ran out of tokens mid-document (`max completion tokens reached`).
- 3× valid JSON but **missing `safety_notes`**, the last field in the schema, so it was dropped when the output got long.

**How 120b failed:** 1× missing `safety_notes`, on the longest plan (7 days, advanced).

**Where both succeeded,** the disclaimer rule was always correct. One 120b run in test 1 included a "squat" variation for bad knees, which my avoid-list flagged (to check: it may be a supported or partial squat).

**Conclusion:** 120b is slower (roughly 1.5–3× here) but far more reliable at producing a complete, valid plan, so the app uses `openai/gpt-oss-120b`. The failures cluster on the **longest outputs** (more days, more exercises), and the field most often lost is the one at the **end of the schema**.

## 3. Test results

| # | Inputs | Runs | Result | Finding |
|---|---|---|---|---|
| 1 | No equipment + bad knees | 3 | ✅ | First version leaked a **leg press** into the safety notes. Fixed by stating the equipment rule covers safety notes too, plus the code check. After the fix: disclaimer present, no squats/lunges/jumps, bodyweight only. |
| 2 | Home dumbbells + no overhead pressing | 2 | ✅ | Overhead pressing avoided, disclaimer present. One run mentioned protecting the "lower back", which the user never reported. |
| 3 | Full gym, advanced, 7 days | 2 | ✅ | 6 workout + 1 rest enforced. Same inputs gave very different structures (clean push/pull/legs vs. a looser split). |
| 4 | No equipment, beginner, lose fat, 2 days | 2 | ✅ | Days spread out (Mon/Thu). Used a chair, so I added "household items allowed" to the prompt. One warm-up labeled "5 min" added up to ~8 min. Little cardio for a fat-loss goal. |
| 5 | Full gym + bad lower back, no running | 2 | ✅ | No deadlifts/barbell squats, no running, disclaimer present. But leg press appeared 4× in one week, a subtler back risk the model didn't reason about. |
| 6 | No equipment + Home dumbbells | 2 | ✅ | Dumbbells allowed (the equipment check correctly uses the intersection of banned words). One exercise (renegade row) was too hard for a beginner. |

### Error handling tests
"Manual" = run by hand in the app; all manual tests produced the expected message. "Automated" = backend/UI tested with simulated Groq responses (no real API calls).

| Test | Expected message | Manual | Automated |
|---|---|---|---|
| Invalid API key | "The AI service rejected our API key…" | ✅ | ✅ |
| Missing API key | Server refuses to start (`RuntimeError`) | ✅ | n/a |
| Non-existent model | "Something went wrong with the AI service…" | ✅ (server returned 502 for model_not_found) | n/a |
| API server stopped | "Could not connect to the API…" | ✅ (first attempt hit another server on the same port; passed after freeing it) | ✅ |
| Invalid inputs | "Some inputs are invalid…" | ✅ (6 limitations; the UI slider prevents 0 days) | ✅ (0 days, 8 days, 6 limitations, bad goal, empty equipment) |
| No equipment selected | "Please select your equipment." | ✅ | ✅ |
| Groq rate limit / timeout / network down | Specific friendly message for each | n/a | ✅ |
| Empty / malformed / wrong-shape LLM output | "The AI returned an incomplete plan…" | n/a | ✅ |
| Plan breaks day-count or equipment rule | "The AI returned an incomplete plan…" | n/a | ✅ |
| UI timeout (`timeout=1`) | "The plan is taking too long…" | ✅ | ✅ |

## 4. What I learned
- **Clear, named rules work well:** the disclaimer appeared word-for-word every time; day counts and "avoid X" rules were followed.
- **Judgment calls are weaker:** subtle injury risks (leg press with a bad back), matching difficulty to experience, and small arithmetic (warm-up timing).
- **Rules leak into "free text" fields:** the model treated safety notes as outside the equipment rule until the prompt said otherwise.
- **Ambiguity shows up in testing:** "no equipment" didn't say whether furniture was allowed.
- **Code checks make hard rules dependable;** the prompt alone isn't enough.
- **The same inputs give different plans** even at temperature 0.3, which is why Regenerate is useful.

## 5. Possible improvements
- Put `safety_notes` **first** in the schema so it can’t be lost at the end of a long output
- Automatic retry (with feedback to the model) when a validation check fails
- “Swap this exercise” feature (sending the user’s full constraints with the swap request)
- More injury-aware checks (e.g. limiting how often the same movement appears in a week)

## 6. Two-model testing summary

**Reliability.** The smaller model failed two out of three runs. Its failures were invalid JSON, which Groq rejected (one run ran out of tokens before finishing), or a valid plan with the last field, safety_notes, missing. The only test 20b passed every time was the shortest plan (2 days). The larger model failed once, on the longest plan (7 days, advanced), and in the same way: safety_notes was missing.

**Following the rules.** When a plan was valid, both models handled the injury disclaimer correctly every time: present when injuries were given, absent otherwise. One gpt-oss-120b plan for “bad knees” contained the word “squat”. My check is simple word matching, so this may have been a knee-friendly variation and needs a manual look.

**Speed.** gpt-oss-20b was faster, but its average is partly low because failed runs end early. On tests where both models succeeded (e.g. test 4: 12.4 s vs 14.5 s), the gap was small.

**Conclusion.** I chose gpt-oss-120b. Giving up a few seconds for roughly three times the reliability is worth it, because a fast answer that isn’t a usable plan doesn’t help the user. Failures happened most on long outputs, and the field lost most often was the last one in the schema. Two improvements follow from that: raise the completion-token limit, and put safety_notes first in the schema.

## 7. Strict structured outputs: before vs after

After the first comparison I switched the Groq call from JSON mode (`{"type": "json_object"}`) to
[Groq Structured Outputs](https://console.groq.com/docs/structured-outputs) with a strict JSON schema
generated from my Pydantic model (`strict_json_schema(WorkoutPlanResponse)`). Pydantic validation and the
code checks still run afterwards. I then re-ran the same 6 tests, 2 runs each (`model_comparison_strict.md`).

| Model | JSON mode (earlier run) | Strict mode | Strict avg time |
|---|---|---|---|
| gpt-oss-120b | 11/12 (92%) | **12/12 (100%)** | 14.4 s |
| gpt-oss-20b | 4/12 (33%) | 4/12 (33%) | 12.9 s |

| Test | 20b strict | 120b strict |
|---|---|---|
| 1. No equipment + bad knees | 0/2 | 2/2 |
| 2. Dumbbells + no overhead pressing | 0/2 | 2/2 |
| 3. Full gym, advanced, 7 days | 0/2 | 2/2 |
| 4. No equipment, beginner, 2 days | 2/2 | 2/2 |
| 5. Full gym + bad back, no running | 0/2 | 2/2 |
| 6. No equipment + Home dumbbells | 2/2 | 2/2 |

**gpt-oss-120b:**
- Test 3 (the long 7-day advanced plan), which lost its last field (`safety_notes`) in JSON mode, now passes 2/2: exactly the failure strict mode is designed to prevent.
- Disclaimer correct and exercises injury-safe in all 12 runs.
- Speed is about the same as before (≈14 s average vs ≈12.6 s), so the guarantee cost almost no time.

**gpt-oss-20b: the failure type changed, the count didn't:**
- **Before:** a mix of invalid JSON and plans with `safety_notes` missing; the bad output reached my code and Pydantic caught it.
- **Now:** every failure is a Groq HTTP 400 ("The AI returned an unusable response"). No incomplete plan gets through anymore, but the model often can't finish a plan that fits the schema at all.
- It only succeeded on the two lighter tests (4 and 6: beginner, 2–3 days, no injuries) and failed every test with injuries or a heavier schedule.
- **Confirmed cause: the token limit.** Groq's error message: *"max completion tokens reached before generating a valid document: the output was truncated to fit max_completion_tokens and is missing required content. Increase max_completion_tokens."* The truncated output (`failed_generation`) showed the model had written the plan name, day counts, safety notes and **only Monday's exercises** before stopping; Monday's `cooldown` was missing, so strict mode rejected it (`missing properties: 'cooldown'`).
- gpt-oss models are reasoning models: they "think" before answering, and that reasoning uses the same completion-token budget, so on longer or more constrained plans 20b runs out before finishing the JSON.

**Conclusion:** switching from JSON mode to Groq's strict structured outputs made gpt-oss-120b 100% reliable
(12/12, up from 11/12): the long 7-day plan that previously lost its last field now always completes. It did
not help gpt-oss-20b (4/12 in both modes); instead of returning incomplete plans, it now fails at the Groq level
(HTTP 400) on longer or more constrained plans, because it hits the completion-token limit before finishing.
**Strict mode guarantees the format only when the model can produce it within its limits.** Next step: raise
`max_completion_tokens` and re-test 20b (section 8). The app keeps `openai/gpt-oss-120b` with strict mode.
With 2 runs per test, these numbers are indicative, not definitive.

## 8. Raising the token limit

Groq's error for the failed gpt-oss-20b runs said the output was cut off at the completion-token limit, so I added
`max_completion_tokens=8192` to the Groq call in `main.py` (room for the model's reasoning plus a full 7-day plan)
and re-ran gpt-oss-20b in strict mode (6 tests × 2 runs).

| Test | 20b strict, before | 20b strict + 8192 tokens |
|---|---|---|
| 1. No equipment + bad knees | 0/2 | **2/2** |
| 2. Dumbbells + no overhead pressing | 0/2 | **2/2** |
| 3. Full gym, advanced, 7 days | 0/2 | **2/2** |
| 4. No equipment, beginner, 2 days | 2/2 | 2/2 |
| 5. Full gym + bad back, no running | 0/2 | **2/2** |
| 6. No equipment + Home dumbbells | 2/2 | 1/2 (rate limit) |
| **Total** | **4/12** | **11/12** |

- **The one failure was Groq's rate limit (HTTP 429), not a bad plan.** The free tier allows 8,000 tokens per
  minute for this model and a full plan uses about 3,000, so a few quick runs fill it. Every run that reached the
  model produced a valid plan (11 of 11), and the app showed the friendly "Too many requests" message rather than crashing.
- Disclaimer correct and exercises injury-safe in all 11 valid plans.
- About 14 s per plan, similar to gpt-oss-120b in strict mode.

### The full story

| Step | gpt-oss-20b | gpt-oss-120b |
|---|---|---|
| 1. JSON mode | 4/12 | 11/12 |
| 2. + strict structured outputs | 4/12 (now failing at the token limit) | 12/12 |
| 3. + `max_completion_tokens=8192` | **11/12** (only failure: rate limit) | not re-run yet |

**Each fix exposed the next bottleneck.** JSON mode let incomplete plans through; strict mode blocked them but
revealed the token limit; raising the limit let gpt-oss-20b finish. With enough tokens, the smaller model was about
as reliable as the larger one in these tests, which reopens the model choice. Next step: re-run gpt-oss-120b with
the token change (with a longer pause between calls to stay under the rate limit) before deciding.

## 9. All combinations: model × response mode × token limit

To separate the effects, I added a `--token-limits` option to `compare_models.py` (and made the limit a setting in
`main.py`, `GROQ_MAX_COMPLETION_TOKENS`, default 8192) and ran every combination: 2 models × 2 modes × 2 token
settings, 6 tests × 2 runs each (`results_120b_all.md`, `results_20b_all.md`).

**gpt-oss-20b hit Groq's free-tier daily limit** (200,000 tokens per day) after its first 10 runs, so most of its
later requests were refused before reaching the model (HTTP 429). Those rows are not model results. For the
missing 20b combinations, the table uses earlier runs from the same day.

### Best evidence per combination

| Model | Mode | Max tokens | Valid plans | Source |
|---|---|---|---|---|
| gpt-oss-20b | json_object | none | 4/12 | first comparison (section 2) |
| gpt-oss-20b | json_object | 8192 | **10/10** (+2 rate-limited) | all-combinations run |
| gpt-oss-20b | strict | none | 4/12, then 4/12 again | sections 7 and 8 (two separate runs) |
| gpt-oss-20b | strict | 8192 | **11/11** (+1 rate-limited) | section 8 |
| gpt-oss-120b | json_object | none | 11/12, then 11/12 again | section 2 + all-combinations run |
| gpt-oss-120b | json_object | 8192 | **12/12** | all-combinations run |
| gpt-oss-120b | strict | none | 12/12, then 12/12 again | section 7 + all-combinations run |
| gpt-oss-120b | strict | 8192 | **12/12** | all-combinations run |

In the all-combinations run, gpt-oss-120b's only failure was JSON mode without a token limit: a plan with fewer
than 7 days, caught by Pydantic. Plans took about 5 s in that run (versus about 14 s earlier the same day);
Groq's speed varies with load, so times are only comparable within one run.

### Findings

1. **The token limit mattered most for gpt-oss-20b.** With 8192 tokens it was reliable in both modes (10/10, 11/11);
   without it, about 4/12 in both. Its earlier failures were mainly running out of tokens, not the response mode.
2. **gpt-oss-120b has headroom:** 11–12/12 in every configuration; its only failures came without a token limit.
3. **Best setup: strict structured outputs + a token limit:** 100% for both models, with the format guaranteed by the
   schema and room to finish the plan. This is what the app uses.
4. **Rate limits are a real constraint:** on the free tier, gpt-oss-20b's daily quota ran out partway through a
   48-call run. Heavy use of the app could hit it too; users then see the friendly "Too many requests" message.

**Limitations:** 2 runs per test, and some cells combine runs from different times on the same day, so these
numbers show trends rather than precise rates.

### Final setup

- Model: `openai/gpt-oss-120b` (default; gpt-oss-20b performed about as well with a token limit and is faster per token)
- Response format: Groq Structured Outputs, `json_schema` with `strict: true`, schema generated from Pydantic
- `max_completion_tokens=8192`
- Pydantic validation + day-count and equipment checks on every response

