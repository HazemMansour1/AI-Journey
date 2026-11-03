
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).with_name("tasks.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def create_tasks_table():
    conn = get_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task TEXT NOT NULL,
            priority TEXT,
            deadline TEXT,
            estimated_hours REAL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

def save_task(task_data):
    conn = get_connection()

    try:
        cursor = conn.execute("""
            INSERT INTO tasks (
                task,
                priority,
                deadline,
                estimated_hours
            )
            VALUES (?, ?, ?, ?)
        """, (
            task_data["task"],
            task_data["priority"],
            task_data.get("deadline"),
            task_data.get("estimated_hours")
        ))

        conn.commit()
        return cursor.lastrowid

    finally:
        conn.close()

def get_all_tasks():
    conn = get_connection()

    try:
        cursor = conn.execute("""
            SELECT * FROM tasks
            ORDER BY id DESC
        """)

        rows = cursor.fetchall()

        return [dict(row) for row in rows]

    finally:
        conn.close()

def update_task_priority(task_id, new_priority):
    conn = get_connection()

    try:
        cursor = conn.execute("""
            UPDATE tasks
            SET priority = ?
            WHERE id = ?
        """, (new_priority, task_id))

        conn.commit()

        return cursor.rowcount > 0

    finally:
        conn.close()

def delete_task(task_id):
    conn = get_connection()

    try:
        cursor = conn.execute("""
            DELETE FROM tasks
            WHERE id = ?
        """, (task_id,))

        conn.commit()

        return cursor.rowcount > 0

    finally:
        conn.close()


if __name__ == "__main__":
    create_tasks_table()
    print("Database initialized successfully!")
