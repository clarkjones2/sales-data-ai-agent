"""
Chart generation from SQL query results (Plotly HTML exports).
Used by the Q&A agent when users ask for graphs, plots, or visualizations.
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

import pandas as pd
import plotly.express as px

from database_tools import DatabaseQueryTool


class VisualizationTool:
    """Run a query, build a Plotly figure, save as interactive HTML."""

    CHART_TYPES = frozenset(
        {"bar", "horizontal_bar", "line", "scatter", "pie", "area"}
    )

    def __init__(
        self,
        db_tool: DatabaseQueryTool,
        output_dir: Optional[str] = None,
    ):
        self.db_tool = db_tool
        base = os.path.dirname(os.path.abspath(__file__))
        self.output_dir = output_dir or os.path.join(base, "charts_output")
        os.makedirs(self.output_dir, exist_ok=True)

    def create_visualization(
        self,
        sql_query: str,
        chart_type: str,
        x_column: str,
        y_column: str,
        title: str = "",
        color_column: Optional[str] = None,
        max_rows: int = 500,
    ) -> Dict[str, Any]:
        """
        Execute SQL, then chart two columns from the result set.

        For pie charts: x_column = slice labels (names), y_column = numeric values.

        Args:
            sql_query: SQLite query whose result includes x_column and y_column
            chart_type: bar | horizontal_bar | line | scatter | pie | area
            x_column: Category / x-axis / pie labels
            y_column: Numeric y-axis / pie values
            title: Chart title
            color_column: Optional third column for grouped or colored series (bar/line)
            max_rows: Cap rows fetched for plotting
        """
        ct = chart_type.strip().lower().replace("-", "_")
        if ct == "hbar":
            ct = "horizontal_bar"

        if ct not in self.CHART_TYPES:
            return {
                "success": False,
                "message": (
                    f"Invalid chart_type '{chart_type}'. "
                    f"Use one of: {', '.join(sorted(self.CHART_TYPES))}"
                ),
            }

        result = self.db_tool.query_database(sql_query, max_rows=max_rows)
        if not result.get("success"):
            return {
                "success": False,
                "message": result.get("message", "Query failed"),
                "error": result.get("error"),
                "query": sql_query,
            }

        rows = result.get("data") or []
        if not rows:
            return {
                "success": False,
                "message": "Query returned no rows to chart.",
                "query": sql_query,
            }

        df = pd.DataFrame(rows)

        for col, label in [(x_column, "x_column"), (y_column, "y_column")]:
            if col not in df.columns:
                return {
                    "success": False,
                    "message": (
                        f"Column '{col}' ({label}) not in query result. "
                        f"Columns: {list(df.columns)}"
                    ),
                    "query": sql_query,
                }

        if color_column and color_column not in df.columns:
            return {
                "success": False,
                "message": (
                    f"color_column '{color_column}' not in result. "
                    f"Columns: {list(df.columns)}"
                ),
            }

        # Coerce y to numeric where reasonable
        if ct != "pie":
            df[y_column] = pd.to_numeric(df[y_column], errors="coerce")
        else:
            df[y_column] = pd.to_numeric(df[y_column], errors="coerce")

        df = df.dropna(subset=[y_column])
        if df.empty:
            return {
                "success": False,
                "message": "No numeric values left in y_column after cleaning.",
            }

        color_kw = {}
        if color_column and ct in ("bar", "line", "scatter", "area"):
            color_kw["color"] = color_column

        try:
            if ct == "pie":
                fig = px.pie(
                    df,
                    names=x_column,
                    values=y_column,
                    title=title or None,
                )
            elif ct == "bar":
                fig = px.bar(
                    df,
                    x=x_column,
                    y=y_column,
                    title=title or None,
                    **color_kw,
                )
            elif ct == "horizontal_bar":
                fig = px.bar(
                    df,
                    x=y_column,
                    y=x_column,
                    orientation="h",
                    title=title or None,
                    labels={y_column: y_column, x_column: x_column},
                    **color_kw,
                )
            elif ct == "line":
                fig = px.line(
                    df,
                    x=x_column,
                    y=y_column,
                    title=title or None,
                    markers=True,
                    **color_kw,
                )
            elif ct == "scatter":
                fig = px.scatter(
                    df,
                    x=x_column,
                    y=y_column,
                    title=title or None,
                    **color_kw,
                )
            else:  # area
                fig = px.area(
                    df,
                    x=x_column,
                    y=y_column,
                    title=title or None,
                    **color_kw,
                )
        except Exception as e:
            return {
                "success": False,
                "message": f"Could not build chart: {e}",
                "query": sql_query,
            }

        fig.update_layout(
            template="plotly_white",
            margin=dict(l=40, r=40, t=60, b=80),
        )
        if ct in ("bar", "line", "scatter", "area") and df[x_column].dtype == object:
            sample = df[x_column].astype(str).str.len().max()
            if sample and sample > 12:
                fig.update_xaxes(tickangle=-35)

        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        fname = f"chart_{stamp}_{uuid.uuid4().hex[:8]}.html"
        filepath = os.path.join(self.output_dir, fname)

        try:
            fig.write_html(filepath, include_plotlyjs="cdn", full_html=True)
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to write HTML file: {e}",
            }

        png_filepath = None
        try:
            png_fname = fname.replace(".html", ".png")
            png_path = os.path.join(self.output_dir, png_fname)
            fig.write_image(png_path, width=1000, height=600, scale=1)
            png_filepath = os.path.abspath(png_path)
        except Exception:
            pass

        msg = f"Saved interactive chart ({len(df)} points) to {filepath}"
        if png_filepath:
            msg += f" (PNG: {png_filepath})"

        return {
            "success": True,
            "message": msg,
            "filepath": os.path.abspath(filepath),
            "png_filepath": png_filepath,
            "format": "html",
            "row_count": len(df),
            "columns": list(df.columns),
            "chart_type": ct,
        }


CREATE_VISUALIZATION_TOOL_SPEC = {
    "name": "create_visualization",
    "description": """Build an interactive chart (saved as HTML) from a SQL query.

Use when the user asks for a chart, graph, plot, visualization, or "show me" a trend visually.

Workflow:
1. Write a SQL query that returns a small result set (ideally under 100 rows) with clear column names.
2. Choose chart_type: bar, horizontal_bar, line, scatter, pie, or area.
3. Set x_column and y_column to exact column names from the SELECT list.
   - bar / line / scatter / area: x_column = categories or dates, y_column = numeric measure.
   - horizontal_bar: x_column = category labels (y-axis), y_column = numeric (x-axis).
   - pie: x_column = slice names, y_column = numeric values.

Optional color_column: use when SQL returns a third grouping column for grouped/colored bars or lines.

Example — revenue by product category (bar):
  SELECT p.Category AS category, SUM(oi.Sales) AS revenue
  FROM Order_Items oi JOIN Products p ON oi.Product_Key = p.Product_Key
  GROUP BY p.Category ORDER BY revenue DESC
  x_column=category, y_column=revenue, chart_type=bar

The tool saves an HTML file (and a PNG if the kaleido package is installed). Tell the user the file path(s).
""",
    "input_schema": {
        "type": "object",
        "properties": {
            "sql_query": {
                "type": "string",
                "description": "SQLite SELECT that returns columns matching x_column and y_column",
            },
            "chart_type": {
                "type": "string",
                "description": "One of: bar, horizontal_bar, line, scatter, pie, area",
            },
            "x_column": {
                "type": "string",
                "description": "Result column for x-axis, categories, or pie labels",
            },
            "y_column": {
                "type": "string",
                "description": "Result column for y-axis values or pie sizes",
            },
            "title": {
                "type": "string",
                "description": "Short chart title (optional)",
            },
            "color_column": {
                "type": "string",
                "description": "Optional column for series/color grouping (bar, line, scatter, area)",
            },
        },
        "required": ["sql_query", "chart_type", "x_column", "y_column"],
    },
}


if __name__ == "__main__":
    vt = VisualizationTool(DatabaseQueryTool())
    out = vt.create_visualization(
        sql_query="""
            SELECT p.Category AS category, SUM(oi.Sales) AS revenue
            FROM Order_Items oi
            JOIN Products p ON oi.Product_Key = p.Product_Key
            GROUP BY p.Category
            ORDER BY revenue DESC
        """,
        chart_type="bar",
        x_column="category",
        y_column="revenue",
        title="Revenue by category",
    )
    print(out)
