"""
Context and conversation session manager for JARVIS.
Handles multi-turn memory rolling, follow-up tracking, and session persistence.
"""

import uuid
from typing import List, Dict, Any, Optional
from jarvis.memory.database import DatabaseManager, db_manager
from jarvis.core.logger import jarvis_logger


class ContextManager:
    def __init__(self, max_turns: int = 15, manager: Optional[DatabaseManager] = None):
        self.max_turns = max_turns
        self.db = manager or db_manager
        self.session_id = str(uuid.uuid4())[:8]
        self.active_history: List[Dict[str, str]] = []
        self.current_topic: str = ""

    def add_turn(self, role: str, content: str):
        """Add a conversation turn ('user' or 'assistant')."""
        turn = {"role": role, "content": content}
        self.active_history.append(turn)

        # Keep rolling window
        if len(self.active_history) > self.max_turns * 2:
            self.active_history = self.active_history[-(self.max_turns * 2):]

        # Persist turn in database
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO conversation_history (session_id, role, content)
                    VALUES (?, ?, ?)
                    """,
                    (self.session_id, role, content)
                )
                conn.commit()
        except Exception as e:
            jarvis_logger.warning(f"Could not persist conversation turn: {e}")

    def get_history_for_llm(self) -> List[Dict[str, str]]:
        """Return history suitable for LLM APIs (excluding latest pending prompt)."""
        return list(self.active_history)

    def clear_active_session(self):
        """Reset active conversation session."""
        self.active_history.clear()
        self.session_id = str(uuid.uuid4())[:8]
        self.current_topic = ""
        jarvis_logger.info("Cleared active conversation context.")

    def get_recent_summary(self) -> str:
        """Returns brief string of recent turns for context awareness."""
        if not self.active_history:
            return "No previous conversation."
        lines = []
        for h in self.active_history[-6:]:
            prefix = "Rehan" if h["role"] == "user" else "JARVIS"
            lines.append(f"{prefix}: {h['content'][:100]}")
        return "\n".join(lines)


context_manager = ContextManager()
