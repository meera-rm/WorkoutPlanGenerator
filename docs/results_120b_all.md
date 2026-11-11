# Model and response-mode comparison

2 run(s) per test · same system prompt, Pydantic validation and code checks

- **json_object**: older JSON mode (valid JSON; schema only described in the prompt)
- **strict**: Groq Structured Outputs, `json_schema` with `strict: true`
- **Max tokens**: `max_completion_tokens` sent to Groq (`none` = Groq's default)
- **Valid plan**: passed JSON, schema, day-count and equipment checks
- **Disclaimer correct**: present when injuries were given, absent otherwise
- **Injury-safe**: no exercise names from the test's avoid-list

## Overall

| Model | Mode | Max tokens | Valid plans | Avg time (s) |
|---|---|---|---|---|
| openai/gpt-oss-120b | json_object | 8192 | 12/12 (100%) | 5.6 |
| openai/gpt-oss-120b | json_object | none | 11/12 (92%) | 5.1 |
| openai/gpt-oss-120b | strict | 8192 | 12/12 (100%) | 5.0 |
| openai/gpt-oss-120b | strict | none | 12/12 (100%) | 5.6 |

## 1. No equipment + bad knees

| Model | Mode | Max tokens | Valid plan | Disclaimer correct | Injury-safe | Avg time (s) | Notes |
|---|---|---|---|---|---|---|---|
| openai/gpt-oss-120b | json_object | 8192 | 2/2 | 2/2 | 2/2 | 6.0 | — |
| openai/gpt-oss-120b | json_object | none | 2/2 | 2/2 | 1/2 | 4.5 | avoided words found: squat |
| openai/gpt-oss-120b | strict | 8192 | 2/2 | 2/2 | 2/2 | 4.6 | — |
| openai/gpt-oss-120b | strict | none | 2/2 | 2/2 | 2/2 | 4.1 | — |

## 2. Dumbbells + no overhead pressing

| Model | Mode | Max tokens | Valid plan | Disclaimer correct | Injury-safe | Avg time (s) | Notes |
|---|---|---|---|---|---|---|---|
| openai/gpt-oss-120b | json_object | 8192 | 2/2 | 2/2 | 2/2 | 6.1 | — |
| openai/gpt-oss-120b | json_object | none | 2/2 | 2/2 | 1/2 | 6.0 | avoided words found: overhead press |
| openai/gpt-oss-120b | strict | 8192 | 2/2 | 2/2 | 2/2 | 7.5 | — |
| openai/gpt-oss-120b | strict | none | 2/2 | 2/2 | 2/2 | 8.3 | — |

## 3. Full gym, advanced, 7 days

| Model | Mode | Max tokens | Valid plan | Disclaimer correct | Injury-safe | Avg time (s) | Notes |
|---|---|---|---|---|---|---|---|
| openai/gpt-oss-120b | json_object | 8192 | 2/2 | 2/2 | 2/2 | 5.8 | — |
| openai/gpt-oss-120b | json_object | none | 2/2 | 2/2 | 2/2 | 5.8 | — |
| openai/gpt-oss-120b | strict | 8192 | 2/2 | 2/2 | 2/2 | 5.5 | — |
| openai/gpt-oss-120b | strict | none | 2/2 | 2/2 | 2/2 | 7.1 | — |

## 4. No equipment, beginner, 2 days

| Model | Mode | Max tokens | Valid plan | Disclaimer correct | Injury-safe | Avg time (s) | Notes |
|---|---|---|---|---|---|---|---|
| openai/gpt-oss-120b | json_object | 8192 | 2/2 | 2/2 | 2/2 | 5.5 | — |
| openai/gpt-oss-120b | json_object | none | 2/2 | 2/2 | 2/2 | 3.6 | — |
| openai/gpt-oss-120b | strict | 8192 | 2/2 | 2/2 | 2/2 | 3.3 | — |
| openai/gpt-oss-120b | strict | none | 2/2 | 2/2 | 2/2 | 3.7 | — |

## 5. Full gym + bad back, no running

| Model | Mode | Max tokens | Valid plan | Disclaimer correct | Injury-safe | Avg time (s) | Notes |
|---|---|---|---|---|---|---|---|
| openai/gpt-oss-120b | json_object | 8192 | 2/2 | 2/2 | 2/2 | 5.3 | — |
| openai/gpt-oss-120b | json_object | none | 1/2 | 1/1 | 1/1 | 6.6 | errors: The AI returned an incomplete plan. Please click Generate again. |
| openai/gpt-oss-120b | strict | 8192 | 2/2 | 2/2 | 2/2 | 5.5 | — |
| openai/gpt-oss-120b | strict | none | 2/2 | 2/2 | 2/2 | 5.4 | — |

## 6. No equipment + Home dumbbells

| Model | Mode | Max tokens | Valid plan | Disclaimer correct | Injury-safe | Avg time (s) | Notes |
|---|---|---|---|---|---|---|---|
| openai/gpt-oss-120b | json_object | 8192 | 2/2 | 2/2 | 2/2 | 4.8 | — |
| openai/gpt-oss-120b | json_object | none | 2/2 | 2/2 | 2/2 | 4.2 | — |
| openai/gpt-oss-120b | strict | 8192 | 2/2 | 2/2 | 2/2 | 3.6 | — |
| openai/gpt-oss-120b | strict | none | 2/2 | 2/2 | 2/2 | 5.2 | — |
