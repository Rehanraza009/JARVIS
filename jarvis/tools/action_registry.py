"""
Action Registry for JARVIS.
Central dispatcher that detects, classifies, validates, permission-checks,
and executes real Windows automation and application actions.
"""

import re
from enum import Enum
from typing import Dict, Any, Optional, Callable
from jarvis.tools.system_tools import system_tools
from jarvis.tools.web_search import web_search_tool
from jarvis.tools.doc_reader import doc_reader
from jarvis.core.events import bus, AssistantState
from jarvis.core.logger import jarvis_logger


class PermissionLevel(str, Enum):
    SAFE = "safe"                               # Execute immediately
    CONFIRMATION_REQUIRED = "confirm_required" # Requires user popup/approval


class ActionRegistry:
    def __init__(self):
        self.actions: Dict[str, Dict[str, Any]] = {}
        self._register_default_actions()

    def register(
        self,
        name: str,
        handler: Callable,
        permission: PermissionLevel,
        description: str
    ):
        self.actions[name] = {
            "handler": handler,
            "permission": permission,
            "description": description
        }

    def _register_default_actions(self):
        # Settings
        self.register(
            "open_settings",
            system_tools.open_windows_settings,
            PermissionLevel.SAFE,
            "Open Windows Settings (main, bluetooth, wifi, display, sound)"
        )
        self.register(
            "navigate_ui",
            self._handle_ui_navigation,
            PermissionLevel.SAFE,
            "Navigate inside JARVIS desktop application tabs"
        )
        # Apps & Sites
        self.register(
            "open_app",
            system_tools.open_app,
            PermissionLevel.SAFE,
            "Open desktop application (e.g. Chrome, Notepad, WhatsApp, Calculator, VS Code, Paint)"
        )
        self.register(
            "close_app",
            system_tools.close_app,
            PermissionLevel.SAFE,
            "Close desktop application gracefully (e.g. Chrome, Notepad, WhatsApp, Calculator, VS Code)"
        )
        self.register(
            "change_volume",
            system_tools.change_volume,
            PermissionLevel.SAFE,
            "Adjust system volume (up, down, mute/unmute)"
        )
        self.register(
            "open_website",
            system_tools.open_website,
            PermissionLevel.SAFE,
            "Open website or search query in browser"
        )
        # Window Management
        self.register(
            "minimize_window",
            system_tools.minimize_active_window,
            PermissionLevel.SAFE,
            "Minimize active foreground window"
        )
        self.register(
            "maximize_window",
            system_tools.maximize_active_window,
            PermissionLevel.SAFE,
            "Maximize active foreground window"
        )
        self.register(
            "close_window",
            system_tools.close_active_window,
            PermissionLevel.SAFE,
            "Close active foreground window"
        )
        # System Power Actions
        self.register(
            "shutdown_system",
            system_tools.shutdown_system,
            PermissionLevel.CONFIRMATION_REQUIRED,
            "Initiate Windows shutdown with confirmation"
        )
        self.register(
            "restart_system",
            system_tools.restart_system,
            PermissionLevel.CONFIRMATION_REQUIRED,
            "Initiate Windows restart with confirmation"
        )
        self.register(
            "cancel_shutdown",
            system_tools.cancel_shutdown,
            PermissionLevel.SAFE,
            "Cancel pending Windows shutdown"
        )
        # Search & Docs
        self.register(
            "web_search",
            web_search_tool.search,
            PermissionLevel.SAFE,
            "Perform real-time web search"
        )
        self.register(
            "read_file",
            doc_reader.read_file,
            PermissionLevel.SAFE,
            "Read and parse local text/code/PDF document"
        )
        self.register(
            "run_script",
            system_tools.run_approved_script,
            PermissionLevel.CONFIRMATION_REQUIRED,
            "Run an explicitly approved local Python script"
        )
        self.register(
            "open_folder",
            system_tools.open_folder,
            PermissionLevel.SAFE,
            "Open system folders like Downloads, Documents, Desktop in File Explorer"
        )
        self.register(
            "stop_listening",
            self._handle_stop_listening,
            PermissionLevel.SAFE,
            "Pause voice listening and mute microphone"
        )
        self.register(
            "start_listening",
            self._handle_start_listening,
            PermissionLevel.SAFE,
            "Resume voice listening and unmute microphone"
        )

    def _handle_ui_navigation(self, tab: str) -> Dict[str, Any]:
        """Trigger UI tab switch via Qt event bus."""
        bus.navigation_requested.emit(tab.lower().strip())
        return {"success": True, "message": f"JARVIS {tab.capitalize()} open kar diya hai."}

    def _handle_stop_listening(self) -> Dict[str, Any]:
        from jarvis.speech.stt_engine import stt_engine
        stt_engine.set_muted(True)
        bus.mic_mute_toggled.emit(True)
        return {"success": True, "message": "Microphone listening pause kar di hai Rehan bhai. Jab bhi dobara baat karni ho, 'Jarvis, listen again' bolein ya mic button press karein."}

    def _handle_start_listening(self) -> Dict[str, Any]:
        from jarvis.speech.stt_engine import stt_engine
        stt_engine.set_muted(False)
        bus.mic_mute_toggled.emit(False)
        return {"success": True, "message": "Microphone active kar diya hai Rehan bhai. Main sun rahi hoon!"}

    def detect_action_intent(self, user_input: str) -> Optional[Dict[str, Any]]:
        """
        Parses text for actionable commands with natural Hindi/Hinglish/English variations.
        Returns dict with action_name, kwargs, and permission level if detected.
        """
        text = user_input.strip()
        text_lower = text.lower()

        # -------------------------------------------------------------
        # 0. Voice Listening Control (Stop / Resume)
        # -------------------------------------------------------------
        if any(p in text_lower for p in [
            "stop listening", "jarvis stop listening", "jarvis, stop listening",
            "mic band karo", "listening band karo", "don't listen", "jarvis mat suno", "sunna band karo"
        ]):
            return {
                "action": "stop_listening",
                "kwargs": {},
                "permission": PermissionLevel.SAFE,
                "confirmation_msg": "Microphone listening pause kar rahi hoon Rehan bhai."
            }

        if any(p in text_lower for p in [
            "listen again", "jarvis listen again", "jarvis, listen again",
            "mic on karo", "start listening", "listening shuru karo", "jarvis suno", "ab suno"
        ]):
            return {
                "action": "start_listening",
                "kwargs": {},
                "permission": PermissionLevel.SAFE,
                "confirmation_msg": "Microphone active kar rahi hoon Rehan bhai."
            }

        # -------------------------------------------------------------
        # 1. JARVIS In-App Navigation ("Jarvis settings kholo", "Voice change karo")
        # -------------------------------------------------------------
        if any(p in text_lower for p in [
            "jarvis settings band karo", "jarvis settings close karo", "jarvis setting band karo", "jarvis setting close karo", "jarvis ki setting band karo"
        ]):
            return {
                "action": "navigate_ui",
                "kwargs": {"tab": "chat"},
                "permission": PermissionLevel.SAFE,
                "confirmation_msg": "Ji Rehan bhai, JARVIS Settings band kar di hain."
            }

        if any(p in text_lower for p in [
            "jarvis settings", "jarvis setting", "jarvis ki setting", "jarvis ki settings"
        ]):
            return {
                "action": "navigate_ui",
                "kwargs": {"tab": "settings"},
                "permission": PermissionLevel.SAFE,
                "confirmation_msg": "Ji Rehan bhai, JARVIS Settings open kar rahi hoon."
            }

        if any(p in text_lower for p in ["voice change karo", "awaz badlo", "change voice", "jarvis ki voice"]):
            return {
                "action": "navigate_ui",
                "kwargs": {"tab": "settings"},
                "permission": PermissionLevel.SAFE,
                "confirmation_msg": "Ji Rehan bhai, voice settings open kar rahi hoon jahan aap female voices select kar sakte hain."
            }

        # -------------------------------------------------------------
        # 2. Windows Settings ("settings kholo", "setting on karo", "bluetooth settings kholo")
        # -------------------------------------------------------------
        # Specific sub-settings
        if any(w in text_lower for w in ["bluetooth settings", "bluetooth on karo", "bluetooth kholo", "bluetooth open karo"]):
            return {
                "action": "open_settings",
                "kwargs": {"target": "bluetooth"},
                "permission": PermissionLevel.SAFE,
                "confirmation_msg": "Ji Rehan bhai, Bluetooth Settings khol rahi hoon."
            }

        if any(w in text_lower for w in ["wifi settings", "wi-fi settings", "wifi kholo", "wifi on karo", "network settings"]):
            return {
                "action": "open_settings",
                "kwargs": {"target": "wifi"},
                "permission": PermissionLevel.SAFE,
                "confirmation_msg": "Ji Rehan bhai, Wi-Fi Settings khol rahi hoon."
            }

        if any(w in text_lower for w in ["display settings", "screen settings", "display setting"]):
            return {
                "action": "open_settings",
                "kwargs": {"target": "display"},
                "permission": PermissionLevel.SAFE,
                "confirmation_msg": "Ji Rehan bhai, Display Settings khol rahi hoon."
            }

        if any(w in text_lower for w in ["sound settings", "volume settings", "sound setting"]):
            return {
                "action": "open_settings",
                "kwargs": {"target": "sound"},
                "permission": PermissionLevel.SAFE,
                "confirmation_msg": "Ji Rehan bhai, Sound Settings khol rahi hoon."
            }

        # General Windows Settings ("setting on karo", "settings kholo", "windows settings open karo")
        settings_patterns = [
            r"(?:jarvis\s*,?\s*)?(?:windows\s+|laptop\s+ki\s+)?settings?\s+(?:kholo|khol do|on karo|open karo|chalao|kholna)",
            r"(?:jarvis\s*,?\s*)?(?:open|kholo|chalao|launch)\s+(?:windows\s+|laptop\s+ki\s+)?settings?",
            r"(?:jarvis\s*,?\s*)?settings?\s+on\s+karo",
            r"(?:jarvis\s*,?\s*)?setting\s+on\s+karo"
        ]
        for pat in settings_patterns:
            if re.search(pat, text_lower):
                return {
                    "action": "open_settings",
                    "kwargs": {"target": "main"},
                    "permission": PermissionLevel.SAFE,
                    "confirmation_msg": "Ji Rehan bhai, Windows Settings khol rahi hoon."
                }

        # -------------------------------------------------------------
        # 3. Window Management (Minimize, Maximize, Close)
        # -------------------------------------------------------------
        if any(p in text_lower for p in ["window minimize", "minimize window", "screen minimize", "window chhota karo"]):
            return {
                "action": "minimize_window",
                "kwargs": {},
                "permission": PermissionLevel.SAFE,
                "confirmation_msg": "Ji Rehan bhai, window minimize kar rahi hoon."
            }

        if any(p in text_lower for p in ["window maximize", "maximize window", "screen maximize", "window bada karo"]):
            return {
                "action": "maximize_window",
                "kwargs": {},
                "permission": PermissionLevel.SAFE,
                "confirmation_msg": "Ji Rehan bhai, window maximize kar rahi hoon."
            }

        if any(p in text_lower for p in ["active window close", "window close karo", "window band karo", "close active window"]):
            return {
                "action": "close_window",
                "kwargs": {},
                "permission": PermissionLevel.SAFE,
                "confirmation_msg": "Ji Rehan bhai, active window close kar rahi hoon."
            }

        # Volume Control
        if any(w in text_lower for w in ["volume badhao", "volume up", "sound badhao", "awaz badhao", "awaz tez karo", "volume uncha karo"]):
            return {
                "action": "change_volume",
                "kwargs": {"direction": "up"},
                "permission": PermissionLevel.SAFE,
                "confirmation_msg": "Volume increase kar rahi hoon Rehan bhai."
            }

        if any(w in text_lower for w in ["volume kam karo", "volume down", "sound kam karo", "awaz kam karo", "volume dheere karo"]):
            return {
                "action": "change_volume",
                "kwargs": {"direction": "down"},
                "permission": PermissionLevel.SAFE,
                "confirmation_msg": "Volume decrease kar rahi hoon Rehan bhai."
            }

        if any(w in text_lower for w in ["sound mute", "mute karo", "unmute karo", "volume mute", "audio mute", "awaz band karo", "sound band karo"]):
            return {
                "action": "change_volume",
                "kwargs": {"direction": "mute"},
                "permission": PermissionLevel.SAFE,
                "confirmation_msg": "Audio mute/unmute kar rahi hoon Rehan bhai."
            }

        # -------------------------------------------------------------
        # 4. System Power (Shutdown / Restart) - Requires Confirmation
        # -------------------------------------------------------------
        if any(p in text_lower for p in ["laptop shutdown", "shutdown karo", "system shutdown", "laptop band karo"]):
            return {
                "action": "shutdown_system",
                "kwargs": {},
                "permission": PermissionLevel.CONFIRMATION_REQUIRED,
                "confirmation_msg": "Rehan bhai, kya aap sach mein laptop shutdown karna chahte hain?"
            }

        if any(p in text_lower for p in ["laptop restart", "restart karo", "reboot karo"]):
            return {
                "action": "restart_system",
                "kwargs": {},
                "permission": PermissionLevel.CONFIRMATION_REQUIRED,
                "confirmation_msg": "Rehan bhai, kya aap sach mein laptop restart karna chahte hain?"
            }

        if "cancel shutdown" in text_lower or "shutdown cancel" in text_lower:
            return {
                "action": "cancel_shutdown",
                "kwargs": {},
                "permission": PermissionLevel.SAFE,
                "confirmation_msg": "Shutdown cancel kar rahi hoon Rehan bhai."
            }

        # -------------------------------------------------------------
        # 5. Open Websites
        # -------------------------------------------------------------
        m_site = re.match(r"(?:jarvis\s*,?\s*)?(?:open|kholo|chalao)\s+(youtube|google|github|linkedin|chatgpt|stackoverflow|twitter|x|wikipedia)(?:\s+(?:kholo|open karo))?", text_lower)
        if m_site:
            site = m_site.group(1).strip()
            return {
                "action": "open_website",
                "kwargs": {"site_or_url": site},
                "permission": PermissionLevel.SAFE,
                "confirmation_msg": f"Ji Rehan bhai, {site.capitalize()} open kar rahi hoon."
            }

        # Google search request (e.g. "Google par Python tutorials search karo")
        m_google_search = re.search(r"(?:google\s+par\s+|search\s+on\s+google\s+for\s+)(.*?)(?:\s+(?:search\s+karo|dhundo|kholo))?$", text_lower)
        if m_google_search and m_google_search.group(1).strip():
            query = m_google_search.group(1).strip()
            return {
                "action": "open_website",
                "kwargs": {"site_or_url": f"https://www.google.com/search?q={query.replace(' ', '+')}"},
                "permission": PermissionLevel.SAFE,
                "confirmation_msg": f"Ji Rehan bhai, Google par '{query}' search kar rahi hoon."
            }

        # -------------------------------------------------------------
        # 5b. Open System Folders (Downloads, Documents, Desktop, etc.)
        # -------------------------------------------------------------
        folder_names_pat = r"(downloads?|documents?|desktop|pictures?|images?|photos?|videos?|music|projects?)"
        m_folder = re.search(
            rf"(?:jarvis\s*,?\s*)?(?:open|kholo|chalao)?\s*{folder_names_pat}\s+folder(?:\s+(?:kholo|khol do|open karo|chalao))?",
            text_lower
        )
        if not m_folder:
            m_folder = re.search(
                rf"(?:jarvis\s*,?\s*)?(?:open|kholo|chalao)\s+{folder_names_pat}\s+folder?",
                text_lower
            )
        if m_folder:
            f_name = m_folder.group(1).strip()
            return {
                "action": "open_folder",
                "kwargs": {"folder_name": f_name},
                "permission": PermissionLevel.SAFE,
                "confirmation_msg": f"Ji Rehan bhai, {f_name.capitalize()} folder open kar rahi hoon."
            }

        # -------------------------------------------------------------
        # 6a. Close Specific Application (Chrome band karo, Notepad band karo, etc.)
        # -------------------------------------------------------------
        close_apps_pat = r"(chrome|google chrome|paint|ms paint|mspaint|notepad|calculator|calc|vscode|vs code|code|terminal|powershell|cmd|explorer|file explorer|files|whatsapp|edge|msedge)"
        m_close_prefix = re.match(
            rf"(?:jarvis\s*,?\s*)?(?:close|exit|quit|band karo|band kar do)\s+{close_apps_pat}$",
            text_lower
        )
        m_close_suffix = re.match(
            rf"(?:jarvis\s*,?\s*)?{close_apps_pat}\s+(?:band karo|band kar do|close karo|close kar do|exit karo|quit karo|hata do)$",
            text_lower
        )
        m_close = m_close_prefix or m_close_suffix
        if m_close:
            raw_target = m_close.group(1).strip()
            if raw_target in ["google chrome", "chrome"]:
                app_key = "chrome"
            elif raw_target in ["ms paint", "mspaint", "paint"]:
                app_key = "paint"
            elif raw_target in ["file explorer", "files", "explorer"]:
                app_key = "explorer"
            elif raw_target in ["vs code", "code", "vscode"]:
                app_key = "vscode"
            elif raw_target in ["calculator", "calc"]:
                app_key = "calculator"
            elif raw_target in ["terminal", "powershell"]:
                app_key = "powershell"
            elif raw_target in ["edge", "msedge"]:
                app_key = "edge"
            else:
                app_key = raw_target

            return {
                "action": "close_app",
                "kwargs": {"app_name": app_key},
                "permission": PermissionLevel.SAFE,
                "confirmation_msg": f"Ji Rehan bhai, {raw_target.capitalize()} band kar rahi hoon."
            }

        # -------------------------------------------------------------
        # 6b. Applications Open (Chrome, WhatsApp, Paint, Notepad, Calculator, etc.)
        # -------------------------------------------------------------
        open_apps_pat = r"(chrome|google chrome|paint|ms paint|mspaint|notepad|calculator|calc|vscode|vs code|code|terminal|powershell|cmd|explorer|file explorer|files|whatsapp|edge|msedge)"
        m_app = re.match(
            rf"(?:jarvis\s*,?\s*)?(?:open|kholo|chalao|launch|start|open karo|on karo)\s+{open_apps_pat}",
            text_lower
        )
        if not m_app:
            m_app_rev = re.match(
                rf"(?:jarvis\s*,?\s*)?{open_apps_pat}\s+(?:kholo|khol do|open karo|chalao|start karo|on karo)",
                text_lower
            )
            if m_app_rev:
                m_app = m_app_rev

        if m_app:
            target_app = m_app.group(1).strip()
            # Normalize names
            if target_app in ["google chrome", "chrome"]:
                app_key = "chrome"
            elif target_app in ["ms paint", "mspaint", "paint"]:
                app_key = "paint"
            elif target_app in ["file explorer", "files", "explorer"]:
                app_key = "explorer"
            elif target_app in ["vs code", "code", "vscode"]:
                app_key = "vscode"
            elif target_app in ["calculator", "calc"]:
                app_key = "calculator"
            elif target_app in ["terminal", "powershell"]:
                app_key = "powershell"
            elif target_app in ["edge", "msedge"]:
                app_key = "edge"
            else:
                app_key = target_app

            return {
                "action": "open_app",
                "kwargs": {"app_name": app_key},
                "permission": PermissionLevel.SAFE,
                "confirmation_msg": f"Ji Rehan bhai, {target_app.capitalize()} open kar rahi hoon."
            }

        # -------------------------------------------------------------
        # 7. Explicit Web Search
        # -------------------------------------------------------------
        m_search = re.match(r"(?:jarvis\s*,?\s*)?(?:search\s+(?:the\s+)?web\s+for|search\s+for|search\s+karo|dhundo)\s+(.*)", text_lower)
        if m_search and m_search.group(1).strip():
            return {
                "action": "web_search",
                "kwargs": {"query": m_search.group(1).strip()},
                "permission": PermissionLevel.SAFE,
                "confirmation_msg": "Web research kar rahi hoon Rehan bhai."
            }

        # -------------------------------------------------------------
        # 8. Read Document
        # -------------------------------------------------------------
        m_read = re.match(r"(?:jarvis\s*,?\s*)?(?:read|summarize|padho|check file)\s+file\s+['\"]?([^'\"]+)['\"]?", text, re.IGNORECASE)
        if m_read and m_read.group(1).strip():
            return {
                "action": "read_file",
                "kwargs": {"file_path_str": m_read.group(1).strip()},
                "permission": PermissionLevel.SAFE,
                "confirmation_msg": "Document inspect kar rahi hoon Rehan bhai."
            }

        # -------------------------------------------------------------
        # 9. Generic App Match Fallback (e.g. "Photoshop kholo")
        # -------------------------------------------------------------
        m_generic_app = re.match(r"(?:jarvis\s*,?\s*)?([a-zA-Z0-9_\-]+)\s+(?:kholo|open karo|chalao)", text_lower)
        if m_generic_app:
            potential_app = m_generic_app.group(1).strip()
            # Avoid matching conversational words
            if potential_app not in ["setting", "settings", "jarvis", "window", "screen", "mic", "voice", "tab", "laptop", "pc"]:
                return {
                    "action": "open_app",
                    "kwargs": {"app_name": potential_app},
                    "permission": PermissionLevel.SAFE,
                    "confirmation_msg": f"{potential_app.capitalize()} check kar rahi hoon Rehan bhai."
                }

        return None

    def execute(self, action_name: str, **kwargs) -> Dict[str, Any]:
        """Execute a registered action with error catching and state/action signals."""
        if action_name not in self.actions:
            return {"success": False, "error": f"Unknown action: {action_name}"}

        entry = self.actions[action_name]
        bus.state_changed.emit(AssistantState.EXECUTING)
        bus.action_started.emit(action_name, str(kwargs))
        try:
            handler = entry["handler"]
            result = handler(**kwargs)
            success = result.get("success", True) if isinstance(result, dict) else True
            msg = result.get("message", "") if isinstance(result, dict) else str(result)
            bus.action_finished.emit(action_name, success, msg)
            return {"success": True, "result": result}
        except Exception as e:
            jarvis_logger.error(f"Error executing action '{action_name}': {e}")
            bus.action_finished.emit(action_name, False, str(e))
            return {"success": False, "error": str(e)}


action_registry = ActionRegistry()
