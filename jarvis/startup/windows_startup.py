"""
Windows Startup Integration for JARVIS.
Uses Windows Registry (HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run)
to configure seamless launch on user sign-in without requiring administrative privileges.
"""

import sys
import os
from pathlib import Path
from jarvis.core.logger import jarvis_logger
from jarvis.core.config import BASE_DIR

try:
    import winreg
    HAS_WINREG = True
except ImportError:
    HAS_WINREG = False

REG_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "JARVIS_Assistant"


class WindowsStartupManager:
    @staticmethod
    def is_startup_enabled() -> bool:
        """Check if JARVIS is registered in Windows startup registry."""
        if not HAS_WINREG:
            return False

        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY, 0, winreg.KEY_READ) as key:
                val, _ = winreg.QueryValueEx(key, APP_NAME)
                return bool(val)
        except FileNotFoundError:
            return False
        except Exception as e:
            jarvis_logger.warning(f"Error querying Windows startup registry: {e}")
            return False

    @staticmethod
    def enable_startup() -> bool:
        """Register JARVIS to run on Windows user login."""
        if not HAS_WINREG:
            jarvis_logger.warning("Windows registry (winreg) is not available on this platform.")
            return False

        try:
            # Prefer wscript.exe with JARVIS.vbs --startup for complete logging and error dialogs on login
            vbs_launcher = BASE_DIR / "JARVIS.vbs"
            wscript_exe = Path(os.environ.get("SystemRoot", "C:\\Windows")) / "System32" / "wscript.exe"

            if vbs_launcher.exists() and wscript_exe.exists():
                cmd_line = f'"{wscript_exe}" "{vbs_launcher}" --startup'
            else:
                # Direct pythonw fallback with verified absolute paths
                known_pythonw = Path("C:/Python313/pythonw.exe")
                sys_pythonw = Path(sys.executable).parent / "pythonw.exe"
                exe_to_use = str(known_pythonw) if known_pythonw.exists() else (str(sys_pythonw) if sys_pythonw.exists() else sys.executable)
                runner_script = BASE_DIR / "run_jarvis.py"
                cmd_line = f'"{exe_to_use}" "{runner_script}" --startup'

            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY, 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, cmd_line)

            jarvis_logger.info(f"Registered JARVIS to Windows startup: {cmd_line}")
            return True
        except Exception as e:
            jarvis_logger.error(f"Failed to enable Windows startup: {e}")
            return False

    @staticmethod
    def disable_startup() -> bool:
        """Remove JARVIS from Windows startup registry."""
        if not HAS_WINREG:
            return False

        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY, 0, winreg.KEY_SET_VALUE) as key:
                winreg.DeleteValue(key, APP_NAME)
            jarvis_logger.info("Removed JARVIS from Windows startup registry.")
            return True
        except FileNotFoundError:
            return True
        except Exception as e:
            jarvis_logger.warning(f"Error disabling Windows startup: {e}")
            return False


startup_manager = WindowsStartupManager()
