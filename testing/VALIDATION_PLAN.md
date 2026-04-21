# Validation Plan

## 1. Purpose

This validation plan defines the testing process used to evaluate the accuracy and performance of our agent.

## 2. Scope

This validation covers the following requirements:

| Req ID | Requirement | How Tested |
|--------|-------------|------------|
| 4.1 | Simple queries return results within 10 seconds | Response time captured per prompt and prompts categorized |
| 4.1 | Complex queries return results within 30 seconds | Response time captured per prompt and prompts categorized |
| 4.3 | 80% first-attempt accuracy for non-technical users | Manual Pass/Fail review of 25 test prompts |

## 3. Process

### Define Test Prompts

25 natural language questions are defined in `test_cases.json`, written from the perspective of a non-technical business user. Prompts are categorized by complexity and query type.

### Execute Test Run

The `validation_runner.py` script:

1.  Loads the 25 test prompts from `test_cases.json`
2.  Initializes agent
3.  Sends each prompt to the agent (one at a time, fresh conversation per prompt)
4.  Captures:
    -   The generated SQL query
    -   The agent's natural language answer
    -   Response time (seconds)
5.  Outputs all results to `validation_results.csv`


### Automated Evaluation

- Each agent answer is automatically evaluated using an LLM-as-Judge (gpt-4o-mini), which compares the agent's answer to the expected answer and assigns PASS/FAIL with a reason.
- For ambiguous or complex cases (e.g., Test 15), a `judge_guidance` field in `test_cases.json` can instruct the judge to defer to manual review.
- **Manual review is only performed on failures** (auto FAILs or MANUAL_REVIEW cases). The reviewer checks the agent's answer, expected answer, and judge reason, and updates the `manual_pass_fail` column if the judge was incorrect.

Note: Meeting the timing requirement does not affect pass or fail.

### Calculate Results

-   **Auto Accuracy** = (Number of Auto PASS) / 25 × 100%
-   **Adjusted Accuracy** = (Number of PASS after manual review) / 25 × 100%
-   **Target**: 80% or better (adjusted)
-   **Performance**: All simple queries faster than 10s, complex queries faster than 30s

## 4. Test Prompts

See `test_cases.json`

## 5. Output Files

| File | Description |
|------|-------------|
| `test_cases.json` | The 25 test prompts with IDs and categories |
| `validation_runner.py` | Script that executes the test run |
| `validation_results.csv` | Generated output with SQL, answers, times, and Pass/Fail column, and summary statistics |

## 6. Cost


The total cost of a full test run varies by model selected.

## 7. How to Run Validation (Anthropic vs GPT)

To run the validation suite with different agent models:

**Claude Sonnet (Anthropic):**

```bash
python3 testing/validation_runner.py anthropic
```

This uses the default Claude Sonnet model as the agent. Requires `ANTHROPIC_API_KEY` in your `.env` file.

**OpenAI GPT (e.g., GPT-4o):**

```bash
python3 testing/validation_runner.py openai gpt-4o
```

This uses the specified OpenAI model as the agent. Requires `OPENAI_API_KEY` in your `.env` file.

**Judge Model:**

The LLM judge always uses GPT-4o-mini (OpenAI) for automated evaluation, regardless of the agent model.

**Output:**

Results are saved as `validation_results_<model>_<timestamp>.csv` in the `testing/` directory.