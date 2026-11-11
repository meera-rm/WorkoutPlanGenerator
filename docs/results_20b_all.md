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
| openai/gpt-oss-20b | json_object | 8192 | 10/12 (83%) | 3.0 |
| openai/gpt-oss-20b | json_object | none | 1/12 (8%) | 0.2 |
| openai/gpt-oss-20b | strict | 8192 | 0/12 (0%) | 0.1 |
| openai/gpt-oss-20b | strict | none | 1/12 (8%) | 8.6 |

## 1. No equipment + bad knees

| Model | Mode | Max tokens | Valid plan | Disclaimer correct | Injury-safe | Avg time (s) | Notes |
|---|---|---|---|---|---|---|---|
| openai/gpt-oss-20b | json_object | 8192 | 2/2 | 2/2 | 2/2 | 2.9 | — |
| openai/gpt-oss-20b | json_object | none | 0/2 | — | — | 0.1 | errors: Too many requests right now. Please wait a minute and try again. |
| openai/gpt-oss-20b | strict | 8192 | 0/2 | — | — | 0.1 | errors: Too many requests right now. Please wait a minute and try again. |
| openai/gpt-oss-20b | strict | none | 0/2 | — | — | 0.1 | errors: Too many requests right now. Please wait a minute and try again. |

## 2. Dumbbells + no overhead pressing

| Model | Mode | Max tokens | Valid plan | Disclaimer correct | Injury-safe | Avg time (s) | Notes |
|---|---|---|---|---|---|---|---|
| openai/gpt-oss-20b | json_object | 8192 | 2/2 | 2/2 | 2/2 | 4.1 | — |
| openai/gpt-oss-20b | json_object | none | 0/2 | — | — | 0.1 | errors: Too many requests right now. Please wait a minute and try again. |
| openai/gpt-oss-20b | strict | 8192 | 0/2 | — | — | 0.1 | errors: Too many requests right now. Please wait a minute and try again. |
| openai/gpt-oss-20b | strict | none | 1/2 | 1/1 | 1/1 | 51.5 | errors: Too many requests right now. Please wait a minute and try again. |

## 3. Full gym, advanced, 7 days

| Model | Mode | Max tokens | Valid plan | Disclaimer correct | Injury-safe | Avg time (s) | Notes |
|---|---|---|---|---|---|---|---|
| openai/gpt-oss-20b | json_object | 8192 | 2/2 | 2/2 | 2/2 | 3.8 | — |
| openai/gpt-oss-20b | json_object | none | 0/2 | — | — | 0.1 | errors: Too many requests right now. Please wait a minute and try again. |
| openai/gpt-oss-20b | strict | 8192 | 0/2 | — | — | 0.1 | errors: Too many requests right now. Please wait a minute and try again. |
| openai/gpt-oss-20b | strict | none | 0/2 | — | — | 0.1 | errors: Too many requests right now. Please wait a minute and try again. |

## 4. No equipment, beginner, 2 days

| Model | Mode | Max tokens | Valid plan | Disclaimer correct | Injury-safe | Avg time (s) | Notes |
|---|---|---|---|---|---|---|---|
| openai/gpt-oss-20b | json_object | 8192 | 2/2 | 2/2 | 2/2 | 2.2 | — |
| openai/gpt-oss-20b | json_object | none | 1/2 | 1/1 | 1/1 | 0.9 | errors: Too many requests right now. Please wait a minute and try again. |
| openai/gpt-oss-20b | strict | 8192 | 0/2 | — | — | 0.1 | errors: Too many requests right now. Please wait a minute and try again. |
| openai/gpt-oss-20b | strict | none | 0/2 | — | — | 0.1 | errors: Too many requests right now. Please wait a minute and try again. |

## 5. Full gym + bad back, no running

| Model | Mode | Max tokens | Valid plan | Disclaimer correct | Injury-safe | Avg time (s) | Notes |
|---|---|---|---|---|---|---|---|
| openai/gpt-oss-20b | json_object | 8192 | 2/2 | 2/2 | 2/2 | 5.1 | — |
| openai/gpt-oss-20b | json_object | none | 0/2 | — | — | 0.1 | errors: Too many requests right now. Please wait a minute and try again. |
| openai/gpt-oss-20b | strict | 8192 | 0/2 | — | — | 0.1 | errors: Too many requests right now. Please wait a minute and try again. |
| openai/gpt-oss-20b | strict | none | 0/2 | — | — | 0.1 | errors: Too many requests right now. Please wait a minute and try again. |

## 6. No equipment + Home dumbbells

| Model | Mode | Max tokens | Valid plan | Disclaimer correct | Injury-safe | Avg time (s) | Notes |
|---|---|---|---|---|---|---|---|
| openai/gpt-oss-20b | json_object | 8192 | 0/2 | — | — | 0.1 | errors: Too many requests right now. Please wait a minute and try again. |
| openai/gpt-oss-20b | json_object | none | 0/2 | — | — | 0.1 | errors: Too many requests right now. Please wait a minute and try again. |
| openai/gpt-oss-20b | strict | 8192 | 0/2 | — | — | 0.1 | errors: Too many requests right now. Please wait a minute and try again. |
| openai/gpt-oss-20b | strict | none | 0/2 | — | — | 0.1 | errors: Too many requests right now. Please wait a minute and try again. |
