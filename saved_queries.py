"""
Saved report definitions (library of reusable SQL).
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional


def _library_path() -> str:
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "saved_queries.json")


def load_library() -> Dict[str, Any]:
    path = _library_path()
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def list_saved_reports() -> List[Dict[str, str]]:
    """Short metadata for each saved report (id, title, description)."""
    data = load_library()
    out = []
    for r in data.get("reports", []):
        out.append(
            {
                "id": r["id"],
                "title": r.get("title", r["id"]),
                "description": r.get("description", ""),
            }
        )
    return out


def get_report_sql(report_id: str) -> Optional[str]:
    for r in load_library().get("reports", []):
        if r["id"] == report_id:
            return r["sql"].strip()
    return None


LIST_SAVED_REPORTS_TOOL = {
    "name": "list_saved_reports",
    "description": """List predefined saved reports (id, title, description). Use when the user asks for a standard report, template, or 'saved' analysis. To run one, use run_saved_report with the report id.""",
    "input_schema": {"type": "object", "properties": {}},
}

RUN_SAVED_REPORT_TOOL = {
    "name": "run_saved_report",
    "description": "Execute the SQL for a saved report by id (from list_saved_reports). Returns the same structure as query_database.",
    "input_schema": {
        "type": "object",
        "properties": {
            "report_id": {
                "type": "string",
                "description": "Report id, e.g. revenue_by_category",
            }
        },
        "required": ["report_id"],
    },
}
