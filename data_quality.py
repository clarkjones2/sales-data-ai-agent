"""
Lightweight data-quality checks for the Superstore SQLite database.
"""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional


def _connect_ro(db_path: str) -> sqlite3.Connection:
    p = Path(os.path.abspath(db_path))
    uri = p.as_uri() + "?mode=ro"
    return sqlite3.connect(uri, uri=True)


def run_data_quality_report(db_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Row counts, null checks on key columns, date ranges, FK/orphan checks.
    """
    from database_tools import _default_superstore_db_path

    path = db_path or _default_superstore_db_path()
    if not os.path.isfile(path):
        return {"success": False, "message": f"Database file not found: {path}"}

    try:
        conn = _connect_ro(path)
    except Exception as e:
        return {"success": False, "message": f"Could not open database: {e}"}

    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    report: Dict[str, Any] = {
        "success": True,
        "database": os.path.abspath(path),
        "table_row_counts": {},
        "null_checks": [],
        "date_ranges": [],
        "integrity": [],
        "warnings": [],
    }

    try:
        cur.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
        )
        tables = [r[0] for r in cur.fetchall()]

        for t in tables:
            cur.execute(f'SELECT COUNT(*) AS c FROM "{t}"')
            report["table_row_counts"][t] = cur.fetchone()[0]

        # Nulls on important text/numeric columns
        null_specs: List[tuple] = [
            ("Customers", "Customer_Name"),
            ("Orders", "Order_Date"),
            ("Order_Items", "Sales"),
            ("Products", "Category"),
        ]
        for table, col in null_specs:
            if table not in report["table_row_counts"]:
                continue
            cur.execute(f'SELECT COUNT(*) FROM "{table}" WHERE "{col}" IS NULL')
            nulls = cur.fetchone()[0]
            report["null_checks"].append(
                {"table": table, "column": col, "null_count": nulls}
            )
            if nulls > 0:
                report["warnings"].append(
                    f"{table}.{col} has {nulls} NULL value(s)"
                )

        # Order date range
        if "Orders" in report["table_row_counts"]:
            cur.execute(
                "SELECT MIN(Order_Date), MAX(Order_Date) FROM Orders WHERE Order_Date IS NOT NULL"
            )
            row = cur.fetchone()
            if row and row[0]:
                report["date_ranges"].append(
                    {
                        "table": "Orders",
                        "column": "Order_Date",
                        "min": row[0],
                        "max": row[1],
                    }
                )

        # Orphan order lines
        if "Order_Items" in tables and "Orders" in tables:
            cur.execute(
                """
                SELECT COUNT(*) FROM Order_Items oi
                LEFT JOIN Orders o ON oi.Order_ID = o.Order_ID
                WHERE o.Order_ID IS NULL
                """
            )
            orphans = cur.fetchone()[0]
            report["integrity"].append(
                {
                    "check": "Order_Items.Order_ID -> Orders.Order_ID",
                    "orphan_rows": orphans,
                }
            )
            if orphans > 0:
                report["warnings"].append(
                    f"Found {orphans} order line(s) without matching order"
                )

        # Duplicate order IDs in Orders (should be 0)
        if "Orders" in tables:
            cur.execute(
                """
                SELECT COUNT(*) - COUNT(DISTINCT Order_ID) FROM Orders
                """
            )
            dup = cur.fetchone()[0]
            report["integrity"].append(
                {"check": "Orders duplicate Order_ID rows", "extra_rows": dup}
            )

    finally:
        conn.close()

    report["summary"] = (
        f"{len(tables)} tables; "
        f"{len(report['warnings'])} warning(s)"
    )
    return report


def format_data_quality_markdown(report: Dict[str, Any]) -> str:
    """Human-readable summary for UI or digest."""
    if not report.get("success"):
        return f"**Data quality failed:** {report.get('message', 'unknown')}"
    lines = [
        "# Data quality snapshot",
        "",
        f"**Database:** `{report.get('database')}`",
        f"**Summary:** {report.get('summary', '')}",
        "",
        "## Row counts",
    ]
    for t, c in sorted(report.get("table_row_counts", {}).items()):
        lines.append(f"- **{t}:** {c:,}")
    lines.append("")
    lines.append("## Null checks")
    for row in report.get("null_checks", []):
        lines.append(
            f"- {row['table']}.{row['column']}: {row['null_count']} nulls"
        )
    lines.append("")
    lines.append("## Date ranges")
    for dr in report.get("date_ranges", []):
        lines.append(
            f"- {dr['table']}.{dr['column']}: {dr['min']} → {dr['max']}"
        )
    lines.append("")
    lines.append("## Integrity")
    for row in report.get("integrity", []):
        lines.append(f"- {row}")
    if report.get("warnings"):
        lines.append("")
        lines.append("## Warnings")
        for w in report["warnings"]:
            lines.append(f"- {w}")
    return "\n".join(lines)
