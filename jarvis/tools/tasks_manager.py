"""
Task and Reminder manager for JARVIS.
Stores to-do items and reminders in SQLite, with natural language intent extraction.
"""

import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from jarvis.memory.database import DatabaseManager, db_manager
from jarvis.core.logger import jarvis_logger


class TaskManager:
    def __init__(self, manager: Optional[DatabaseManager] = None):
        self.db = manager or db_manager

    def add_task(
        self,
        title: str,
        description: str = "",
        due_date: str = "",
        priority: str = "normal"
    ) -> int:
        """Add a new task or reminder."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            cursor.execute(
                """
                INSERT INTO tasks (title, description, due_date, priority, status, created_at)
                VALUES (?, ?, ?, ?, 'pending', ?)
                """,
                (title.strip(), description.strip(), due_date.strip(), priority.lower().strip(), now)
            )
            conn.commit()
            task_id = cursor.lastrowid
            jarvis_logger.info(f"Task created id={task_id}: {title}")
            return task_id

    def list_tasks(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List tasks optionally filtered by 'pending' or 'completed'."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            if status:
                cursor.execute("SELECT * FROM tasks WHERE status = ? ORDER BY id DESC", (status.lower(),))
            else:
                cursor.execute("SELECT * FROM tasks ORDER BY status DESC, id DESC")
            return [dict(r) for r in cursor.fetchall()]

    def complete_task(self, task_id: int) -> bool:
        """Mark task as completed."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE tasks SET status = 'completed' WHERE id = ?", (task_id,))
            conn.commit()
            return cursor.rowcount > 0

    def delete_task(self, task_id: int) -> bool:
        """Delete task by id."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            conn.commit()
            return cursor.rowcount > 0

    def get_completed_today(self) -> List[Dict[str, Any]]:
        """Get tasks completed today."""
        today_str = datetime.now().strftime("%Y-%m-%d")
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks WHERE status = 'completed' ORDER BY id DESC")
            all_completed = [dict(r) for r in cursor.fetchall()]
            today_completed = [t for t in all_completed if t.get("created_at", "").startswith(today_str)]
            return today_completed if today_completed else all_completed[:5]

    def get_daily_plan(self) -> Dict[str, Any]:
        """Generate structured daily plan from pending tasks and user context."""
        pending = self.list_tasks(status="pending")
        completed = self.get_completed_today()

        def _sort_key(t):
            due = t.get("due_date", "") or ""
            prio = t.get("priority", "normal")
            prio_score = 0 if prio == "high" else (1 if prio == "normal" else 2)
            has_due = 0 if due else 1
            return (prio_score, has_due, t.get("id", 0))

        sorted_pending = sorted(pending, key=_sort_key)
        return {
            "pending": sorted_pending,
            "completed": completed,
            "total_pending": len(pending),
            "total_completed": len(completed)
        }

    def detect_task_intent(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Detects if user is asking to add, list, complete tasks, or get daily plan.
        """
        text_lower = text.lower().strip()

        # 1. Daily Plan Intent
        if any(p in text_lower for p in [
            "aaj ka plan", "daily plan", "today's plan", "mera plan kya hai",
            "aaj kya karna hai", "plan batao", "kya plan hai", "aaj ka kya plan hai"
        ]):
            return {"action": "daily_plan"}

        # 2. Completed Tasks Today
        if any(p in text_lower for p in [
            "maine aaj kya", "aaj kya complete kiya", "completed tasks",
            "aaj kya-kya complete kiya", "khatam kiye tasks", "finished tasks"
        ]):
            return {"action": "completed_today"}

        # 3. List tasks
        if any(p in text_lower for p in [
            "list tasks", "show tasks", "my tasks", "pending tasks",
            "kya tasks hain", "to-do list", "tasks dikhao", "reminders dikhao",
            "meri pending tasks batao", "meri pending tasks", "pending task"
        ]):
            return {"action": "list"}

        # 4. Complete task
        m_comp = re.search(r"(?:complete|done|finish|khatam|mark completed)\s+(?:task\s+)?#?(\d+)", text_lower)
        if not m_comp:
            m_comp = re.search(r"(?:task\s+)?#?(\d+)\s+(?:ko\s+)?(?:complete|done|khatam)\s+(?:mark\s+karo|karo)", text_lower)
        if m_comp:
            return {"action": "complete", "task_id": int(m_comp.group(1))}
        elif any(p in text_lower for p in ["is task ko complete mark karo", "task complete karo", "complete task"]):
            pending = self.list_tasks(status="pending")
            if pending:
                return {"action": "complete", "task_id": pending[0]["id"]}

        # 5. Add task / reminder / multi-task
        add_patterns = [
            r"(?:remind me to|reminder set karo|add task|task banao|to-do mein add karo)\s+(.*)",
            r"(?:yaad dilana ki|remind me that)\s+(.*)",
            r"(?:aaj mujhe\s+(?:ye\s+)?(?:teen|do|ek)?\s*(?:kaam|tasks?)\s+karne hain\s*:?\s*)(.*)",
            r"(?:kal ke liye reminder lagao\s*:?\s*)(.*)"
        ]
        for pat in add_patterns:
            m = re.match(pat, text_lower)
            if m and m.group(1).strip():
                content = m.group(1).strip()
                due = ""
                m_due = re.search(r"\b(tomorrow|aaj|today|kal|by \d+:\d+|at \d+\s*(?:am|pm)?|tonight)\b", content)
                if m_due:
                    due = m_due.group(0)

                return {
                    "action": "add",
                    "title": content,
                    "due_date": due,
                    "priority": "normal"
                }

        return None


task_manager = TaskManager()
