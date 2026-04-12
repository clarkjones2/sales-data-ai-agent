"""
Anthropic tool specs for analysis, estimates, quality, and backups (used by qa_agent).
"""
from saved_queries import LIST_SAVED_REPORTS_TOOL, RUN_SAVED_REPORT_TOOL

ESTIMATE_QUERY_ROWS_TOOL = {
    "name": "estimate_query_rows",
    "description": """Estimate how many rows a SELECT query would return (COUNT(*) wrapper). Use before running a potentially large query to set expectations.""",
    "input_schema": {
        "type": "object",
        "properties": {
            "sql_query": {
                "type": "string",
                "description": "A single SELECT statement (SQLite)",
            }
        },
        "required": ["sql_query"],
    },
}

EXPLAIN_QUERY_PLAN_TOOL = {
    "name": "explain_query_plan",
    "description": """Run SQLite EXPLAIN QUERY PLAN on a SELECT. Use to reason about index use and query structure (not row counts).""",
    "input_schema": {
        "type": "object",
        "properties": {
            "sql_query": {
                "type": "string",
                "description": "A SELECT statement to explain",
            }
        },
        "required": ["sql_query"],
    },
}

RUN_DATA_QUALITY_TOOL = {
    "name": "run_data_quality_checks",
    "description": """Run automated data-quality checks: per-table row counts, NULL counts on key columns, order date range, orphan Order_Items, duplicate Order_ID checks. Use when the user asks about data quality, trust, or validation.""",
    "input_schema": {"type": "object", "properties": {}},
}

BACKUP_DATABASE_TOOL = {
    "name": "backup_database",
    "description": """Create a timestamped backup of the SQLite database file using SQLite's backup API. Use when the user asks to back up, snapshot, or archive the database.""",
    "input_schema": {
        "type": "object",
        "properties": {
            "backup_directory": {
                "type": "string",
                "description": "Optional directory for the backup file (default: backups/ next to the database)",
            }
        },
    },
}
