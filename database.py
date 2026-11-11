import sqlite3
import json
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "data" / "tasks.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY,
        question TEXT,
        answer TEXT,
        report TEXT,
        evidence TEXT,
        created_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_task(question: str, answer: str, report: str, evidence: list):
    turned_evidence = json.dumps(evidence)
    created_at = datetime.now().isoformat()
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO tasks (question, answer, report, evidence, created_at) VALUES (?, ?, ?, ?, ?)",
        (question, answer, report, turned_evidence, created_at)
    )
    conn.commit()
    conn.close()

def get_tasks() -> list:
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT id, question, answer, report, created_at FROM tasks ORDER BY created_at DESC").fetchall()
    conn.close()
    return [
        {
            "id": row[0],
            "question": row[1],
            "answer": row[2],
            "report": row[3],
            "created_at": row[4],
        }
        for row in rows
    ]
if __name__ == "__main__":
    init_db()
    save_task(
        question = "测试问题",
        answer = "测试回答",
        report = "测试报告",
        evidence = [{"tool_name": "get_summary", "parameters": {}, "results": {}}]
    )

    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT * FROM tasks").fetchall()
    conn.close()
    print(rows)