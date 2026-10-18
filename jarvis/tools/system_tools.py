"""
Safe system automation and productivity actions for JARVIS.
Handles Windows settings, application control, window management,
website navigation, system telemetry, and auditable actions.
"""

import os
import sys
import shutil
import platform
import subprocess
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

try:
    import win32gui
    import win32con
    import win32api
    import win32process
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False

try:
    import winreg
    HAS_WINREG = True
except ImportError:
    HAS_WINREG = False

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

from jarvis.core.logger import jarvis_logger
from jarvis.memory.database import db_manager


class SystemTools:
    # Approved applications whitelist
    APPROVED_APPS = {
        "notepad": "notepad.exe",
        "calculator": "calc.exe",
        "calc": "calc.exe",
        "cmd": "cmd.exe",
        "terminal": "powershell.exe",
        "powershell": "powershell.exe",
        "explorer": "explorer.exe",
        "files": "explorer.exe",
        "vscode": "code",
        "vs code": "code",
        "code": "code",
        "chrome": "chrome",
        "google chrome": "chrome",
        "paint": "mspaint.exe",
        "mspaint": "mspaint.exe",
        "edge": "msedge.exe",
        "msedge": "msedge.exe",
        "whatsapp": "whatsapp:"
    }

    APP_PROCESS_NAMES = {
        "chrome": ["chrome.exe"],
        "google chrome": ["chrome.exe"],
        "notepad": ["notepad.exe", "Notepad.exe"],
        "whatsapp": ["WhatsApp.exe"],
        "calculator": ["CalculatorApp.exe", "calc.exe"],
        "calc": ["CalculatorApp.exe", "calc.exe"],
        "paint": ["mspaint.exe"],
        "mspaint": ["mspaint.exe"],
        "vscode": ["Code.exe"],
        "vs code": ["Code.exe"],
        "code": ["Code.exe"],
        "cmd": ["cmd.exe"],
        "terminal": ["WindowsTerminal.exe", "powershell.exe"],
        "powershell": ["powershell.exe"],
        "edge": ["msedge.exe"],
        "msedge": ["msedge.exe"]
    }

    # Approved website bookmarks
    APPROVED_SITES = {
        "google": "https://www.google.com",
        "youtube": "https://www.youtube.com",
        "github": "https://www.github.com",
        "linkedin": "https://www.linkedin.com",
        "chatgpt": "https://chat.openai.com",
        "stackoverflow": "https://stackoverflow.com",
        "twitter": "https://twitter.com",
        "x": "https://x.com",
        "wikipedia": "https://www.wikipedia.org"
    }

    # Windows Settings URIs
    SETTINGS_URIS = {
        "main": "ms-settings:",
        "settings": "ms-settings:",
        "bluetooth": "ms-settings:bluetooth",
        "wifi": "ms-settings:network-wifi",
        "network": "ms-settings:network-wifi",
        "display": "ms-settings:display",
        "screen": "ms-settings:display",
        "sound": "ms-settings:sound",
        "volume": "ms-settings:sound",
        "battery": "ms-settings:batterysaver",
        "apps": "ms-settings:appsfeatures"
    }

    @classmethod
    def log_activity(cls, action_name: str, details: str, status: str):
        """Audit log action into SQLite."""
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                now = datetime.now().isoformat()
                cursor.execute(
                    """
                    INSERT INTO activity_logs (action_name, details, status, timestamp)
                    VALUES (?, ?, ?, ?)
                    """,
                    (action_name, details, status, now)
                )
                conn.commit()
        except Exception as e:
            jarvis_logger.warning(f"Could not write to activity_logs: {e}")

    @classmethod
    def open_windows_settings(cls, target: str = "main") -> Dict[str, Any]:
        """Open Windows Settings directly via ms-settings: URI."""
        clean_target = target.lower().strip()
        uri = cls.SETTINGS_URIS.get(clean_target, "ms-settings:")

        try:
            subprocess.Popen(f"start {uri}", shell=True)
            msg = f"Windows {clean_target.capitalize()} Settings open kar di hain."
            cls.log_activity("open_settings", f"URI: {uri}", "success")
            return {"success": True, "message": msg, "target": clean_target}
        except Exception as e:
            err = f"Failed to open Windows settings ({clean_target}): {e}"
            jarvis_logger.error(err)
            cls.log_activity("open_settings", err, "failure")
            return {"success": False, "message": err}

    @classmethod
    def _find_in_registry_app_paths(cls, app_name: str) -> Optional[str]:
        """Lookup application executable in Windows App Paths registry."""
        if not HAS_WINREG:
            return None
        keys = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths")
        ]
        candidates = [app_name, f"{app_name}.exe"]
        for root_key, subkey in keys:
            for cand in candidates:
                try:
                    with winreg.OpenKey(root_key, f"{subkey}\\{cand}") as reg_key:
                        val, _ = winreg.QueryValueEx(reg_key, "")
                        if val and os.path.exists(val):
                            return val
                except OSError:
                    continue
        return None

    @classmethod
    def open_app(cls, app_name: str) -> Dict[str, Any]:
        """Launch an application safely."""
        clean_name = app_name.lower().strip()

        # Handle UWP / Protocol based apps
        if clean_name == "whatsapp":
            try:
                subprocess.Popen("start whatsapp:", shell=True)
                msg = "WhatsApp open kar diya hai Rehan bhai."
                cls.log_activity("open_app", msg, "success")
                return {"success": True, "message": msg}
            except Exception as e:
                err = f"Failed to launch WhatsApp: {e}"
                cls.log_activity("open_app", err, "failure")
                return {"success": False, "message": err}

        exe = cls.APPROVED_APPS.get(clean_name)

        if not exe:
            # Check PATH
            found_path = shutil.which(clean_name)
            if found_path:
                exe = clean_name
            else:
                # Check Windows App Paths
                reg_path = cls._find_in_registry_app_paths(clean_name)
                if reg_path:
                    exe = reg_path
                else:
                    msg = f"Application '{app_name}' mujhe system par nahi mili Rehan bhai."
                    cls.log_activity("open_app", msg, "rejected")
                    return {"success": False, "message": msg}

        try:
            if clean_name in ["chrome", "google chrome"]:
                subprocess.Popen("start chrome", shell=True)
            elif clean_name in ["edge", "msedge"]:
                subprocess.Popen("start msedge", shell=True)
            else:
                subprocess.Popen(exe, shell=True)

            msg = f"{clean_name.capitalize()} open kar diya hai Rehan bhai."
            cls.log_activity("open_app", msg, "success")
            return {"success": True, "message": msg}
        except Exception as e:
            err = f"Failed to launch '{clean_name}': {e}"
            jarvis_logger.error(err)
            cls.log_activity("open_app", err, "failure")
            return {"success": False, "message": err}

    @classmethod
    def close_app(cls, app_name: str) -> Dict[str, Any]:
        """Gracefully close an application or its window."""
        clean_name = app_name.lower().strip()
        exe_list = cls.APP_PROCESS_NAMES.get(clean_name, [f"{clean_name}.exe"])

        closed = False
        # Try graceful taskkill without /F first (sends WM_CLOSE to windows)
        for exe in exe_list:
            try:
                res = subprocess.run(
                    ["taskkill", "/IM", exe],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if res.returncode == 0 or "SUCCESS" in res.stdout:
                    closed = True
                    break
            except Exception as e:
                jarvis_logger.debug(f"taskkill error for {exe}: {e}")

        # If process name close didn't catch it, attempt window close by title match
        if not closed and HAS_WIN32:
            target_kw = clean_name.replace(".exe", "")
            def enum_wnd(hwnd, _):
                nonlocal closed
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd).lower()
                    if target_kw in title:
                        win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
                        closed = True
            try:
                win32gui.EnumWindows(enum_wnd, None)
            except Exception:
                pass

        if closed:
            msg = f"{clean_name.capitalize()} band kar diya hai Rehan bhai."
            cls.log_activity("close_app", f"Closed {clean_name}", "success")
            return {"success": True, "message": msg, "app": clean_name}
        else:
            msg = f"{clean_name.capitalize()} abhi system par running nahi mila Rehan bhai."
            cls.log_activity("close_app", f"Not running: {clean_name}", "not_running")
            return {"success": True, "message": msg, "app": clean_name}

    @classmethod
    def change_volume(cls, direction: str) -> Dict[str, Any]:
        """Adjust system volume (up, down, mute/unmute)."""
        clean_dir = direction.lower().strip()
        if not HAS_WIN32:
            return {"success": False, "message": "win32 API not available for volume control."}
        try:
            if clean_dir == "up":
                for _ in range(5):
                    win32api.keybd_event(win32con.VK_VOLUME_UP, 0, 0, 0)
                    win32api.keybd_event(win32con.VK_VOLUME_UP, 0, win32con.KEYEVENTF_KEYUP, 0)
                msg = "Volume increase kar diya hai Rehan bhai."
            elif clean_dir == "down":
                for _ in range(5):
                    win32api.keybd_event(win32con.VK_VOLUME_DOWN, 0, 0, 0)
                    win32api.keybd_event(win32con.VK_VOLUME_DOWN, 0, win32con.KEYEVENTF_KEYUP, 0)
                msg = "Volume decrease kar diya hai Rehan bhai."
            elif clean_dir in ["mute", "unmute", "toggle_mute"]:
                win32api.keybd_event(win32con.VK_VOLUME_MUTE, 0, 0, 0)
                win32api.keybd_event(win32con.VK_VOLUME_MUTE, 0, win32con.KEYEVENTF_KEYUP, 0)
                msg = "Audio mute/unmute toggle kar diya hai Rehan bhai."
            else:
                return {"success": False, "message": f"Unknown volume action: {direction}"}
            cls.log_activity("change_volume", f"Direction: {clean_dir}", "success")
            return {"success": True, "message": msg}
        except Exception as e:
            err = f"Failed to adjust volume: {e}"
            cls.log_activity("change_volume", err, "failure")
            return {"success": False, "message": err}

    @classmethod
    def open_folder(cls, folder_name: str) -> Dict[str, Any]:
        """Open system folder (Downloads, Documents, Desktop, etc.) in File Explorer."""
        clean_name = folder_name.lower().strip()
        user_home = Path.home()

        folders_map = {
            "downloads": user_home / "Downloads",
            "download": user_home / "Downloads",
            "documents": user_home / "Documents",
            "document": user_home / "Documents",
            "desktop": user_home / "Desktop",
            "pictures": user_home / "Pictures",
            "images": user_home / "Pictures",
            "photos": user_home / "Pictures",
            "videos": user_home / "Videos",
            "video": user_home / "Videos",
            "music": user_home / "Music",
            "audio": user_home / "Music",
            "projects": user_home / "Desktop" / "JARVIS" if (user_home / "Desktop" / "JARVIS").exists() else user_home / "Projects",
            "project": user_home / "Desktop" / "JARVIS" if (user_home / "Desktop" / "JARVIS").exists() else user_home / "Projects",
        }

        target_path = folders_map.get(clean_name)
        if not target_path:
            cand = Path(folder_name)
            if cand.exists() and cand.is_dir():
                target_path = cand
            else:
                target_path = user_home / clean_name.capitalize()

        if target_path.exists():
            try:
                os.startfile(str(target_path))
                display_name = target_path.name
                msg = f"{display_name} folder khol diya hai Rehan bhai."
                cls.log_activity("open_folder", str(target_path), "success")
                return {"success": True, "message": msg, "path": str(target_path)}
            except Exception as e:
                err = f"Failed to open folder {target_path}: {e}"
                cls.log_activity("open_folder", err, "failure")
                return {"success": False, "message": err}
        else:
            msg = f"{clean_name.capitalize()} folder system par nahi mila Rehan bhai."
            cls.log_activity("open_folder", f"Folder not found: {clean_name}", "not_found")
            return {"success": False, "message": msg}

    @classmethod
    def open_website(cls, site_or_url: str) -> Dict[str, Any]:
        """Open approved bookmark or valid HTTPS web URL in default browser."""
        target = site_or_url.strip().lower()
        url = cls.APPROVED_SITES.get(target)

        if not url:
            if target.startswith("http://") or target.startswith("https://"):
                url = site_or_url.strip()
            elif "." in target and " " not in target:
                url = f"https://{target}"
            else:
                url = f"https://www.google.com/search?q={site_or_url.replace(' ', '+')}"

        try:
            webbrowser.open(url)
            msg = f"Website khol di hai: {url}"
            cls.log_activity("open_website", msg, "success")
            return {"success": True, "message": msg, "url": url}
        except Exception as e:
            err = f"Failed to open website {url}: {e}"
            cls.log_activity("open_website", err, "failure")
            return {"success": False, "message": err}

    @classmethod
    def minimize_active_window(cls) -> Dict[str, Any]:
        """Minimize the active foreground window."""
        if not HAS_WIN32:
            return {"success": False, "message": "win32gui not available."}
        try:
            hwnd = win32gui.GetForegroundWindow()
            if hwnd:
                win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
                msg = "Active window minimize kar di hai Rehan bhai."
                cls.log_activity("minimize_window", f"HWND: {hwnd}", "success")
                return {"success": True, "message": msg}
            return {"success": False, "message": "No active window found."}
        except Exception as e:
            err = f"Could not minimize window: {e}"
            cls.log_activity("minimize_window", err, "failure")
            return {"success": False, "message": err}

    @classmethod
    def maximize_active_window(cls) -> Dict[str, Any]:
        """Maximize the active foreground window."""
        if not HAS_WIN32:
            return {"success": False, "message": "win32gui not available."}
        try:
            hwnd = win32gui.GetForegroundWindow()
            if hwnd:
                win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
                msg = "Active window maximize kar di hai Rehan bhai."
                cls.log_activity("maximize_window", f"HWND: {hwnd}", "success")
                return {"success": True, "message": msg}
            return {"success": False, "message": "No active window found."}
        except Exception as e:
            err = f"Could not maximize window: {e}"
            cls.log_activity("maximize_window", err, "failure")
            return {"success": False, "message": err}

    @classmethod
    def close_active_window(cls) -> Dict[str, Any]:
        """Close the active foreground window."""
        if not HAS_WIN32:
            return {"success": False, "message": "win32gui not available."}
        try:
            hwnd = win32gui.GetForegroundWindow()
            if hwnd:
                title = win32gui.GetWindowText(hwnd)
                win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
                msg = f"Window '{title}' close kar di hai Rehan bhai."
                cls.log_activity("close_window", f"HWND: {hwnd}, Title: {title}", "success")
                return {"success": True, "message": msg}
            return {"success": False, "message": "No active window found."}
        except Exception as e:
            err = f"Could not close window: {e}"
            cls.log_activity("close_window", err, "failure")
            return {"success": False, "message": err}

    @classmethod
    def shutdown_system(cls) -> Dict[str, Any]:
        """Initiate system shutdown with 60 second grace period."""
        try:
            subprocess.run(["shutdown", "/s", "/t", "60"], check=True)
            msg = "Laptop shutdown initiate kar diya hai (60 seconds mein band hoga). Cancel karne ke liye 'cancel shutdown' bolein."
            cls.log_activity("shutdown_system", "Initiated shutdown", "success")
            return {"success": True, "message": msg}
        except Exception as e:
            err = f"Shutdown failed: {e}"
            cls.log_activity("shutdown_system", err, "failure")
            return {"success": False, "message": err}

    @classmethod
    def restart_system(cls) -> Dict[str, Any]:
        """Initiate system restart with 60 second grace period."""
        try:
            subprocess.run(["shutdown", "/r", "/t", "60"], check=True)
            msg = "Laptop restart initiate kar diya hai (60 seconds mein restart hoga)."
            cls.log_activity("restart_system", "Initiated restart", "success")
            return {"success": True, "message": msg}
        except Exception as e:
            err = f"Restart failed: {e}"
            cls.log_activity("restart_system", err, "failure")
            return {"success": False, "message": err}

    @classmethod
    def cancel_shutdown(cls) -> Dict[str, Any]:
        """Cancel pending shutdown."""
        try:
            subprocess.run(["shutdown", "/a"], check=True)
            msg = "Shutdown cancel kar diya gaya hai Rehan bhai."
            cls.log_activity("cancel_shutdown", "Cancelled shutdown", "success")
            return {"success": True, "message": msg}
        except Exception as e:
            err = f"Cancel shutdown failed: {e}"
            return {"success": False, "message": err}

    @classmethod
    def get_system_telemetry(cls) -> Dict[str, Any]:
        """Returns safe system status (OS, time, platform)."""
        now = datetime.now()
        data = {
            "time": now.strftime("%I:%M %p"),
            "date": now.strftime("%A, %d %B %Y"),
            "os": f"{platform.system()} {platform.release()}",
            "machine": platform.machine(),
            "python_version": platform.python_version()
        }
        return data

    @classmethod
    def run_approved_script(cls, script_path_str: str) -> Dict[str, Any]:
        """Run an explicitly approved local Python script with timeout."""
        path = Path(script_path_str).resolve()
        if not path.exists():
            msg = f"Script file '{path}' does not exist."
            cls.log_activity("run_script", msg, "failure")
            return {"success": False, "message": msg}

        if path.suffix.lower() != ".py":
            msg = f"Only Python (.py) scripts are permitted for safe execution."
            cls.log_activity("run_script", msg, "rejected")
            return {"success": False, "message": msg}

        try:
            res = subprocess.run(
                [sys.executable, str(path)],
                capture_output=True,
                text=True,
                timeout=15
            )
            out = res.stdout.strip()
            err = res.stderr.strip()
            success = res.returncode == 0
            details = f"Code: {res.returncode}. Output: {out[:200]}"
            cls.log_activity("run_script", details, "success" if success else "failure")
            return {
                "success": success,
                "stdout": out,
                "stderr": err,
                "returncode": res.returncode
            }
        except subprocess.TimeoutExpired:
            msg = "Script execution timed out (exceeded 15s limit)."
            cls.log_activity("run_script", msg, "failure")
            return {"success": False, "message": msg}
        except Exception as e:
            msg = f"Error running script: {e}"
            cls.log_activity("run_script", msg, "failure")
            return {"success": False, "message": msg}


system_tools = SystemTools()
