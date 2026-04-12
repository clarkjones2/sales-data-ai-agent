"""
Golden SQL tests: verify core queries execute against superstore.db (no API calls).
"""
from __future__ import annotations

import json
import os
import sqlite3

import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(PROJECT_ROOT, "superstore.db")
GOLDEN_PATH = os.path.join(os.path.dirname(__file__), "golden_questions.json")


def _load_golden():
    with open(GOLDEN_PATH, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def conn():
    if not os.path.isfile(DB_PATH):
        pytest.skip(f"Missing database: {DB_PATH}")
    c = sqlite3.connect(DB_PATH)
    yield c
    c.close()


@pytest.mark.parametrize(
    "name,sql",
    [(q["name"], q["sql"]) for q in _load_golden()["queries"]],
)
def test_golden_query_runs(conn, name, sql):
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    assert rows is not None


def test_golden_file_nonempty():
    data = _load_golden()
    assert len(data.get("queries", [])) >= 1
