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

### Manual Review

PASS or FAIL assigned manually if the 3 criteria are met:

- Does the query execute on our database?
- Does the query match what the user was asking for?
- Does the NL response accurately translate the query output?

Note: meeting the timing requirement does not affect pass or fail.

### Calculate Results

-   **Accuracy** = (Number of Pass) / 25 × 100%
-   **Target**: 80% or better
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

Full execution of the current test plan costs \~\$0.45, using ~100,000 tokens.