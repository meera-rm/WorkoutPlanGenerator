# Model and response-mode comparison

2 run(s) per test · same system prompt, Pydantic validation and code checks

- **json_object**: older JSON mode (valid JSON; schema only described in the prompt)
- **strict**: Groq Structured Outputs, `json_schema` with `strict: true`
- **Valid plan**: passed JSON, schema, day-count and equipment checks
- **Disclaimer correct**: present when injuries were given, absent otherwise
- **Injury-safe**: no exercise names from the test's avoid-list

## Overall

| Model | Mode | Valid plans | Avg time (s) |
|---|---|---|---|
| openai/gpt-oss-20b | strict | 4/12 (33%) | 3.7 |

## 1. No equipment + bad knees

| Model | Mode | Valid plan | Disclaimer correct | Injury-safe | Avg time (s) | Notes |
|---|---|---|---|---|---|---|
| openai/gpt-oss-20b | strict | 1/2 | 1/1 | 1/1 | 2.2 | errors: The AI returned an unusable response. Please try again. |

## 2. Dumbbells + no overhead pressing

| Model | Mode | Valid plan | Disclaimer correct | Injury-safe | Avg time (s) | Notes |
|---|---|---|---|---|---|---|
| openai/gpt-oss-20b | strict | 0/2 | — | — | 3.5 | errors: The AI returned an unusable response. Please try again. |

## 3. Full gym, advanced, 7 days

| Model | Mode | Valid plan | Disclaimer correct | Injury-safe | Avg time (s) | Notes |
|---|---|---|---|---|---|---|
| openai/gpt-oss-20b | strict | 0/2 | — | — | 4.6 | errors: The AI returned an incomplete plan. Please click Generate again. |

## 4. No equipment, beginner, 2 days

| Model | Mode | Valid plan | Disclaimer correct | Injury-safe | Avg time (s) | Notes |
|---|---|---|---|---|---|---|
| openai/gpt-oss-20b | strict | 2/2 | 2/2 | 2/2 | 5.8 | — |

## 5. Full gym + bad back, no running

| Model | Mode | Valid plan | Disclaimer correct | Injury-safe | Avg time (s) | Notes |
|---|---|---|---|---|---|---|
| openai/gpt-oss-20b | strict | 0/2 | — | — | 3.2 | errors: The AI returned an incomplete plan. Please click Generate again.; The AI returned an unusable response. Please try again. |

## 6. No equipment + Home dumbbells

| Model | Mode | Valid plan | Disclaimer correct | Injury-safe | Avg time (s) | Notes |
|---|---|---|---|---|---|---|
| openai/gpt-oss-20b | strict | 1/2 | 1/1 | 1/1 | 2.8 | errors: The AI returned an unusable response. Please try again. |
