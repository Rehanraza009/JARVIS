"""
Central Conversation Manager for JARVIS.
Coordinates intent parsing, memory retrieval, tool execution, LLM queries, and response generation.
"""

from typing import Dict, Any, Optional, Generator
from jarvis.core.logger import jarvis_logger
from jarvis.core.events import bus, AssistantState
from jarvis.llm.provider_factory import get_active_llm
from jarvis.memory.memory_service import memory_service
from jarvis.tools.tasks_manager import task_manager
from jarvis.tools.action_registry import action_registry, PermissionLevel
from jarvis.tools.web_search import web_search_tool
from jarvis.conversation.context_manager import context_manager
from jarvis.conversation.prompt_templates import build_system_instruction


class ConversationManager:
    def __init__(self):
        self.active_llm = get_active_llm()

    def refresh_llm(self):
        self.active_llm = get_active_llm()

    def process_message(self, user_text: str) -> str:
        """
        Main pipeline for processing an incoming user message.
        Returns the text response from JARVIS.
        """
        text = user_text.strip()
        if not text:
            return "Kahiye Rehan bhai, main sun raha hoon!"

        bus.state_changed.emit(AssistantState.THINKING)
        bus.message_received.emit("user", text)

        try:
            # 1. Check for Natural Memory Intent
            mem_intent = memory_service.detect_natural_memory_intent(text)
            if mem_intent:
                action = mem_intent.get("action")
                if action == "remember":
                    mem_id = memory_service.save_memory(
                        category=mem_intent["category"],
                        key=mem_intent["key"],
                        content=mem_intent["content"],
                        source="user_explicit"
                    )
                    bus.memory_changed.emit()
                    response = f"Done Rehan bhai! Maine yaad rakh liya hai: \"{mem_intent['content']}\" (Category: {mem_intent['category']})."
                    self._finish_turn(text, response)
                    return response

                elif action == "recall":
                    all_mems = memory_service.list_memories()
                    if not all_mems:
                        response = "Abhi tak mere paas aapke baare mein koi saved memory nahi hai Rehan bhai. Aap 'Remember that...' bolkar kuch bhi save karwa sakte hain!"
                    else:
                        lines = ["Rehan bhai, mere paas aapke baare mein ye approved memories saved hain:"]
                        for m in all_mems[:8]:
                            lines.append(f"• [{m['category'].capitalize()}] {m['content']}")
                        response = "\n".join(lines)
                    self._finish_turn(text, response)
                    return response

                elif action == "forget":
                    q = mem_intent.get("query", "")
                    deleted = memory_service.forget_by_query(q)
                    bus.memory_changed.emit()
                    if deleted:
                        response = f"Ji bhai, maine ye memory delete kar di: {', '.join(deleted)}."
                    else:
                        response = f"Mujhe '{q}' se related koi memory nahi mili Rehan bhai."
                    self._finish_turn(text, response)
                    return response

                elif action == "goals":
                    goals = memory_service.list_memories(category="goal")
                    if not goals:
                        goals = memory_service.list_memories(category="career")
                    if not goals:
                        response = "Rehan bhai, filhaal koi specific goals saved nahi hain. Aap bol sakte hain 'Yaad rakhna ki mera goal hai...' aur main turant save kar loongi!"
                    else:
                        lines = ["Aapke current goals ye rahe Rehan bhai:"]
                        for g in goals:
                            lines.append(f"• {g['content']}")
                        response = "\n".join(lines)
                    self._finish_turn(text, response)
                    return response

                elif action == "delete_all":
                    count = memory_service.delete_all_memories()
                    bus.memory_changed.emit()
                    response = f"Aapka kehna sar-aankhon par Rehan bhai. Maine saari saved memories wipe kar di hain ({count} items deleted)."
                    self._finish_turn(text, response)
                    return response

            # 2. Check for Task / Reminder Intent
            task_intent = task_manager.detect_task_intent(text)
            if task_intent:
                action = task_intent.get("action")
                if action == "daily_plan":
                    plan = task_manager.get_daily_plan()
                    pending = plan["pending"]
                    completed = plan["completed"]
                    if not pending and not completed:
                        response = "Aaj koi scheduled tasks nahi hain Rehan bhai! Ekdum clear schedule hai. Kuch naya plan karna ho toh bataiye, main add kar doongi."
                    else:
                        lines = ["Aaj ka daily plan ye raha Rehan bhai:"]
                        if pending:
                            lines.append("\nPending Tasks:")
                            for t in pending:
                                due = f" (Due: {t['due_date']})" if t.get('due_date') else ""
                                prio = " [High Priority]" if t.get('priority') == 'high' else ""
                                lines.append(f"• [#{t['id']}] {t['title']}{due}{prio}")
                        if completed:
                            lines.append("\nCompleted Today:")
                            for c in completed:
                                lines.append(f"✓ [#{c['id']}] {c['title']}")
                        if pending:
                            lines.append("\nJARVIS Suggestion: Focused time block karein aur high priority tasks pehle निपटा lijiye!")
                        response = "\n".join(lines)
                    self._finish_turn(text, response)
                    return response

                elif action == "completed_today":
                    completed = task_manager.get_completed_today()
                    if not completed:
                        response = "Aaj abhi tak koi task completed mark nahi hua hai Rehan bhai. Kaam shuru karte hain!"
                    else:
                        lines = ["Aaj aapne ye tasks successfully complete kiye hain Rehan bhai:"]
                        for c in completed:
                            lines.append(f"✓ [#{c['id']}] {c['title']}")
                        lines.append("Shabaash! Great progress!")
                        response = "\n".join(lines)
                    self._finish_turn(text, response)
                    return response

                elif action == "add":
                    t_id = task_manager.add_task(
                        title=task_intent["title"],
                        due_date=task_intent.get("due_date", ""),
                        priority=task_intent.get("priority", "normal")
                    )
                    bus.tasks_changed.emit()
                    due_info = f" (Due: {task_intent['due_date']})" if task_intent.get("due_date") else ""
                    response = f"Bilkul Rehan bhai! Task #{t_id} add kar diya: '{task_intent['title']}'{due_info}."
                    self._finish_turn(text, response)
                    return response

                elif action == "list":
                    tasks = task_manager.list_tasks(status="pending")
                    if not tasks:
                        response = "Filhaal koi pending task nahi hai Rehan bhai! Ekdum chill mahool hai."
                    else:
                        lines = ["Aapke pending tasks ye rahe Rehan bhai:"]
                        for t in tasks:
                            due = f" [Due: {t['due_date']}]" if t['due_date'] else ""
                            lines.append(f"• [#{t['id']}] {t['title']}{due}")
                        response = "\n".join(lines)
                    self._finish_turn(text, response)
                    return response

                elif action == "complete":
                    tid = task_intent["task_id"]
                    if task_manager.complete_task(tid):
                        bus.tasks_changed.emit()
                        response = f"Zabardast Rehan bhai! Task #{tid} completed mark kar diya."
                    else:
                        response = f"Task #{tid} nahi mila bhai."
                    self._finish_turn(text, response)
                    return response

            # 3. Check for Action Registry Commands (Settings, Apps, Sites, Search, Window, Docs)
            action_intent = action_registry.detect_action_intent(text)
            if action_intent:
                act_name = action_intent["action"]
                kwargs = action_intent["kwargs"]
                perm = action_intent["permission"]
                confirm_msg = action_intent.get("confirmation_msg", "")

                if perm == PermissionLevel.SAFE:
                    res = action_registry.execute(act_name, **kwargs)
                    if res["success"]:
                        result_obj = res.get("result", {})
                        if isinstance(result_obj, dict) and "message" in result_obj:
                            response = result_obj["message"]
                        elif confirm_msg:
                            response = confirm_msg
                        elif act_name == "web_search":
                            results = res["result"]
                            if results:
                                lines = ["Rehan bhai, web research ke top results ye rahe:"]
                                for r in results[:3]:
                                    lines.append(f"• **{r['title']}**\n  {r['snippet']}\n  Source: {r['url']}")
                                response = "\n\n".join(lines)
                            else:
                                response = f"Web search par koi relevant results nahi mile bhai for '{kwargs.get('query')}'."
                        elif act_name == "read_file":
                            f_res = res["result"]
                            if f_res["success"]:
                                snippet = f_res["content"][:600]
                                response = f"File '{f_res['filename']}' padh li hai Rehan bhai:\n\n```\n{snippet}\n```"
                            else:
                                response = f"File padhne mein dikkat aayi Rehan bhai: {f_res.get('error')}"
                        else:
                            response = f"Ji Rehan bhai, {act_name} complete ho gaya hai."
                    else:
                        response = f"Action execute karne mein problem aayi Rehan bhai: {res.get('error')}"

                    self._finish_turn(text, response)
                    return response

                elif perm == PermissionLevel.CONFIRMATION_REQUIRED:
                    response = confirm_msg or f"Rehan bhai, kya aap sach mein {act_name} perform karna chahte hain?"
                    bus.action_confirmation_requested.emit(act_name, response)
                    self._finish_turn(text, response)
                    return response

            # 4. Check if query benefits from real-time web search
            tool_context = ""
            lower_text = text.lower()
            needs_search = any(w in lower_text for w in [
                "latest", "today's news", "current weather", "who won", "score", "aaj ki khabar",
                "stock price", "current version", "release date", "what is happening in", "what's happening in",
                "kya chal raha hai", "recent news", "updates on", "current events", "happening in ai"
            ])
            if needs_search:
                search_results = web_search_tool.search(text, max_results=3)
                if search_results:
                    tool_context = web_search_tool.format_search_context(search_results)

            # 5. Retrieve relevant approved personal memories
            relevant_mems = memory_service.search_memories(text, limit=3)

            # 6. Build dynamic system instruction and invoke LLM
            system_instruction = build_system_instruction(
                relevant_memories=relevant_mems,
                tool_context=tool_context
            )
            history = context_manager.get_history_for_llm()

            response = self.active_llm.generate_response(
                prompt=text,
                history=history,
                system_instruction=system_instruction
            )

            self._finish_turn(text, response)
            return response

        except Exception as e:
            jarvis_logger.error(f"Error processing message: {e}")
            bus.state_changed.emit(AssistantState.ERROR)
            err_msg = f"Rehan bhai, ek technical issue aa gaya: {e}. Main abhi bhi yahan hoon, aap doosra sawaal pooch sakte hain!"
            return err_msg

    def _finish_turn(self, user_text: str, assistant_text: str):
        """Record turn in history and emit UI / TTS signals."""
        context_manager.add_turn("user", user_text)
        context_manager.add_turn("assistant", assistant_text)
        bus.message_received.emit("jarvis", assistant_text)
        bus.state_changed.emit(AssistantState.IDLE)


conversation_manager = ConversationManager()
