"""
Export conversation history and query log to Markdown, JSON, and PDF.
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional


def _flatten_assistant_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if hasattr(block, "text"):
                parts.append(getattr(block, "text", "") or "")
            elif isinstance(block, dict):
                if block.get("type") == "text":
                    parts.append(block.get("text", ""))
                elif block.get("type") == "tool_use":
                    parts.append(
                        f"[tool: {block.get('name', '?')} {block.get('input', {})}]"
                    )
            else:
                parts.append(str(block)[:300])
        return "\n".join(parts)
    return str(content)[:2000]


def conversation_to_markdown(
    conversation_history: List[Dict[str, Any]],
    query_log: List[Dict[str, Any]],
    title: str = "Session export",
) -> str:
    lines = [
        f"# {title}",
        "",
        f"**Exported:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Conversation",
        "",
    ]
    for msg in conversation_history:
        role = msg.get("role", "")
        content = msg.get("content")
        if role == "user":
            if isinstance(content, str):
                lines.append("### User")
                lines.append(content)
                lines.append("")
            elif isinstance(content, list):
                lines.append("### User (tool results)")
                lines.append("```")
                lines.append(json.dumps(content, default=str, indent=2)[:8000])
                lines.append("```")
                lines.append("")
        elif role == "assistant":
            lines.append("### Assistant")
            lines.append(_flatten_assistant_content(content))
            lines.append("")
    lines.append("## Query log")
    lines.append("")
    if not query_log:
        lines.append("_No queries logged._")
    else:
        for i, q in enumerate(query_log, 1):
            ok = "ok" if q.get("success") else "failed"
            snippet = (q.get("query") or "")[:400]
            lines.append(f"{i}. ({ok}) `{snippet}{'...' if len(q.get('query','')) > 400 else ''}`")
            lines.append("")
    return "\n".join(lines)


def conversation_to_pdf_bytes(markdown_text: str) -> bytes:
    """Render plain-text/Markdown content to a simple PDF (fpdf2)."""
    try:
        from fpdf import FPDF
    except ImportError as e:
        raise ImportError("fpdf2 is required for PDF export") from e

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", size=9)
    for line in markdown_text.split("\n"):
        safe = line.encode("latin-1", errors="replace").decode("latin-1")
        try:
            pdf.multi_cell(0, 4, safe[:2000] or " ")
        except Exception:
            pdf.multi_cell(0, 4, "[line omitted]")
    out = pdf.output()
    if isinstance(out, str):
        return out.encode("latin-1")
    return bytes(out)


def build_json_export(
    conversation_history: List[Dict[str, Any]],
    query_log: List[Dict[str, Any]],
    chart_paths: Optional[List[str]] = None,
) -> Dict[str, Any]:
    return {
        "exported_at": datetime.now().isoformat(),
        "conversation": conversation_history,
        "queries": query_log,
        "chart_paths": chart_paths or [],
    }
