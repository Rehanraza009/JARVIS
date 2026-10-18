"""
High-level Memory Service for user-controlled personal context.
Provides persistent storage, contextual retrieval, natural memory commands, and privacy controls.
"""

import json
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from jarvis.memory.database import DatabaseManager, db_manager
from jarvis.core.logger import jarvis_logger


class MemoryService:
    def __init__(self, manager: Optional[DatabaseManager] = None):
        self.db = manager or db_manager

    def save_memory(
        self,
        category: str,
        key: str,
        content: str,
        source: str = "user_explicit"
    ) -> int:
        """Save a new memory or update if matching key in category exists."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check for existing key in category
            cursor.execute(
                "SELECT id FROM memories WHERE category = ? AND key = ?",
                (category.lower().strip(), key.lower().strip())
            )
            row = cursor.fetchone()
            
            now = datetime.now().isoformat()
            if row:
                mem_id = row["id"]
                cursor.execute(
                    """
                    UPDATE memories
                    SET content = ?, source = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (content.strip(), source, now, mem_id)
                )
                jarvis_logger.info(f"Updated memory id={mem_id} [{category}:{key}]")
            else:
                cursor.execute(
                    """
                    INSERT INTO memories (category, key, content, source, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (category.lower().strip(), key.lower().strip(), content.strip(), source, now, now)
                )
                mem_id = cursor.lastrowid
                jarvis_logger.info(f"Inserted memory id={mem_id} [{category}:{key}]")

            conn.commit()
            return mem_id

    def list_memories(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all memories or filter by category."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            if category:
                cursor.execute(
                    "SELECT * FROM memories WHERE category = ? ORDER BY updated_at DESC",
                    (category.lower().strip(),)
                )
            else:
                cursor.execute("SELECT * FROM memories ORDER BY updated_at DESC")
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def search_memories(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search memories using keyword matching against key, content, and category."""
        if not query or not query.strip():
            return []

        tokens = [t.lower().strip() for t in re.split(r"\W+", query) if len(t.strip()) > 2]
        if not tokens:
            return []

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM memories")
            rows = cursor.fetchall()

            scored = []
            for r in rows:
                item = dict(r)
                text = f"{item['category']} {item['key']} {item['content']}".lower()
                score = sum(1 for token in tokens if token in text)
                if score > 0:
                    scored.append((score, item))

            scored.sort(key=lambda x: x[0], reverse=True)
            return [item for _, item in scored[:limit]]

    def get_memory(self, memory_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve a specific memory by ID."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM memories WHERE id = ?", (memory_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def update_memory(
        self,
        memory_id: int,
        content: str,
        key: Optional[str] = None,
        category: Optional[str] = None
    ) -> bool:
        """Update existing memory content and metadata."""
        now = datetime.now().isoformat()
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            if key and category:
                cursor.execute(
                    """
                    UPDATE memories
                    SET content = ?, key = ?, category = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (content.strip(), key.strip(), category.strip(), now, memory_id)
                )
            else:
                cursor.execute(
                    "UPDATE memories SET content = ?, updated_at = ? WHERE id = ?",
                    (content.strip(), now, memory_id)
                )
            conn.commit()
            return cursor.rowcount > 0

    def delete_memory(self, memory_id: int) -> bool:
        """Delete a memory by ID."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
            conn.commit()
            jarvis_logger.info(f"Deleted memory id={memory_id}")
            return cursor.rowcount > 0

    def delete_all_memories(self) -> int:
        """Delete all saved memories."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM memories")
            conn.commit()
            count = cursor.rowcount
            jarvis_logger.info(f"Wiped all memories ({count} items removed)")
            return count

    def forget_by_query(self, query: str) -> List[str]:
        """Find and delete memories matching query keywords."""
        matches = self.search_memories(query, limit=5)
        deleted_keys = []
        for m in matches:
            if self.delete_memory(m["id"]):
                deleted_keys.append(f"{m['key']} ({m['content']})")
        return deleted_keys

    def export_memories_json(self) -> str:
        """Export all memories as JSON."""
        memories = self.list_memories()
        return json.dumps(memories, indent=2, ensure_ascii=False)

    def import_memories_json(self, json_str: str) -> int:
        """Import memories from JSON string."""
        data = json.loads(json_str)
        count = 0
        for item in data:
            if "category" in item and "key" in item and "content" in item:
                self.save_memory(
                    category=item["category"],
                    key=item["key"],
                    content=item["content"],
                    source=item.get("source", "imported")
                )
                count += 1
        return count

    def detect_natural_memory_intent(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Detects if user is asking to remember something, recall memories, or forget something.
        Returns a dict with action: 'remember' | 'recall' | 'forget' | 'delete_all'
        """
        text_lower = text.lower().strip()

        # Delete all / wipe memories
        if any(p in text_lower for p in [
            "delete all memories", "delete my saved memory", "wipe memory",
            "clear all memories", "saari memories delete kar do", "mera saara data bhool jao"
        ]):
            return {"action": "delete_all"}

        # Goals intent
        if any(p in text_lower for p in [
            "mere current goals", "mere goals", "my goals", "what are my goals",
            "current goals kya hain", "mere target kya hain", "mere lakshya kya hain"
        ]):
            return {"action": "goals"}

        # What do you remember / recall
        if any(p in text_lower for p in [
            "what do you remember about me", "what do you remember",
            "mere baare mein kya pata hai", "kya yaad hai mere baare mein",
            "list my memories", "show my memories", "tujhe mere baare mein kya yaad hai"
        ]):
            return {"action": "recall"}

        # Forget something
        forget_patterns = [
            r"(?:jarvis\s*,?\s*)?(?:is\s+memory\s+ko\s+bhool\s+jao|ye\s+bhool\s+jao|is\s+baat\s+ko\s+bhool\s+jao)\s*(.*)",
            r"(?:jarvis\s*,?\s*)?(?:forget\s+(?:that|about)?\s*)(.*)",
            r"(?:jarvis\s*,?\s*)?(?:bhool\s+jao\s*(?:ki)?\s*)(.*)",
            r"(?:jarvis\s*,?\s*)?(?:delete\s+memory\s*(?:about)?\s*)(.*)"
        ]
        for pat in forget_patterns:
            m = re.match(pat, text_lower)
            if m and m.group(1).strip():
                return {"action": "forget", "query": m.group(1).strip()}

        # Remember something explicit
        remember_patterns = [
            r"(?:jarvis\s*,?\s*)?(?:ye\s+information\s+yaad\s+rakhna|is\s+baat\s+ko\s+yaad\s+rakhna|ye\s+yaad\s+rakhna)\s*:?\s*(.*)",
            r"(?:jarvis\s*,?\s*)?(?:remember\s+(?:that|this)?\s*:?\s*)(.*)",
            r"(?:jarvis\s*,?\s*)?(?:yaad\s+rakhna\s*(?:ki)?\s*:?\s*)(.*)",
            r"(?:jarvis\s*,?\s*)?(?:note\s+down\s*(?:that)?\s*:?\s*)(.*)"
        ]
        for pat in remember_patterns:
            m = re.match(pat, text_lower)
            if m and m.group(1).strip():
                content = m.group(1).strip()
                # Categorize heuristically
                category = "personal"
                if any(w in content for w in ["goal", "target", "aim", "banna hai", "chahta hoon"]):
                    category = "goal"
                elif any(w in content for w in ["career", "job", "internship", "placement", "salary", "role"]):
                    category = "career"
                elif any(w in content for w in ["project", "repo", "app", "code", "jarvis"]):
                    category = "project"
                elif any(w in content for w in ["like", "favorite", "love", "prefer", "pasand"]):
                    category = "preference"

                # Generate a concise key
                key = "_".join(re.findall(r"\w+", content)[:3]) or "user_note"
                return {
                    "action": "remember",
                    "category": category,
                    "key": key,
                    "content": content
                }

        return None


memory_service = MemoryService()
