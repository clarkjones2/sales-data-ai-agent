import sys
import os
import json
import csv
import time
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from qa_agent import DatabaseQAAgent

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_CASES_FILE = os.path.join(SCRIPT_DIR, "test_cases.json")
RESULTS_FILE = os.path.join(SCRIPT_DIR, "validation_results.csv")


def load_test_cases():
    """Load test prompts from test_cases.json"""
    with open(TEST_CASES_FILE, "r") as f:
        data = json.load(f)
    return data["test_cases"]


def extract_sql_from_log(agent, log_start_index):
    """
    Extract SQL queries generated during the agent's response.
    Returns all SQL queries executed after log_start_index.
    """
    full_log = agent.db_tool.get_query_log()
    new_entries = full_log[log_start_index:]

    sql_queries = []
    for entry in new_entries:
        query = entry.get("query", "")
        if query and not query.strip().startswith("PRAGMA") and "sqlite_master" not in query:
            sql_queries.append(query.strip())

    return " | ".join(sql_queries) if sql_queries else "(no SQL generated)"


def run_validation():
    """Run all test cases and write results to CSV"""
    print("=" * 60)
    print("VALIDATION RUNNER")
    print("=" * 60)

    # Load test cases
    test_cases = load_test_cases()

    # Initialize agent
    print("Initializing agent...")
    try:
        agent = DatabaseQAAgent()
        print("Agent ready.\n")
    except Exception as e:
        print(f"ERROR: Could not initialize agent: {e}")
        sys.exit(1)

    results = []

    for tc in test_cases:
        test_id = tc["id"]
        prompt = tc["prompt"]
        category = tc["category"]

        print(f"[{test_id:02d}/25] {prompt}")

        # Reset conversation for each prompt (first-attempt test)
        agent.reset_conversation()

        # Record where the query log is before this prompt
        log_start = len(agent.db_tool.get_query_log())

        # Send prompt and measure time
        start_time = time.time()
        try:
            answer = agent.ask(prompt)
        except Exception as e:
            answer = f"ERROR: {e}"
        elapsed = round(time.time() - start_time, 2)


        sql = extract_sql_from_log(agent, log_start)

        if category == "Complex":
            time_pass = "Yes" if elapsed <= 30 else "No"
        else:
            time_pass = "Yes" if elapsed <= 10 else "No"

        results.append({
            "id": test_id,
            "category": category,
            "prompt": prompt,
            "generated_sql": sql,
            "agent_answer": answer,
            "response_time_sec": elapsed,
            "time_req_met": time_pass,
            "pass_fail": ""
        })

        print(f"       Time: {elapsed}s | SQL captured: {'Yes' if sql != '(no SQL generated)' else 'No'}")
        print()

    # Write results to CSV
    print(f"Writing results to {RESULTS_FILE}...")
    with open(RESULTS_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "id", "category", "prompt", "generated_sql",
            "agent_answer", "response_time_sec", "time_req_met", "pass_fail"
        ])
        writer.writeheader()
        writer.writerows(results)

    # Print summary
    print("\n" + "=" * 60)
    print("VALIDATION RUN COMPLETE")
    print("=" * 60)
    print(f"  Test cases run:  {len(results)}")
    print(f"  Results file:    {RESULTS_FILE}")
    print(f"  Timestamp:       {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)


if __name__ == "__main__":
    run_validation()