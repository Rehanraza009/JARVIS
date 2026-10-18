"""
Utility script to create a reliable one-click desktop shortcut for JARVIS on Windows.
Points to wscript.exe executing JARVIS.vbs with project working directory and Python icon.
"""

import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def create_shortcut():
    try:
        import win32com.client
        desktop = Path(os.environ["USERPROFILE"]) / "Desktop"
        vbs_launcher = BASE_DIR / "JARVIS.vbs"
        shortcut_path = desktop / "JARVIS.lnk"
        wscript_exe = Path(os.environ.get("SystemRoot", "C:\\Windows")) / "System32" / "wscript.exe"

        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(str(shortcut_path))

        # Use wscript.exe with JARVIS.vbs argument for reliable execution regardless of file associations
        if wscript_exe.exists():
            shortcut.TargetPath = str(wscript_exe)
            shortcut.Arguments = f'"{vbs_launcher}"'
        else:
            shortcut.TargetPath = str(vbs_launcher)
            shortcut.Arguments = ""

        shortcut.WorkingDirectory = str(BASE_DIR)
        shortcut.Description = "JARVIS — Personal AI Friend & Assistant for Rehan Raza"

        # Set Python 3.13 executable icon if present
        python_exe = Path("C:/Python313/python.exe")
        if python_exe.exists():
            shortcut.IconLocation = f"{python_exe},0"
        else:
            shortcut.IconLocation = "shell32.dll,277"

        shortcut.Save()

        print(f"[OK] Desktop shortcut created successfully at: {shortcut_path}")
        print(f"     TargetPath:       {shortcut.TargetPath}")
        print(f"     Arguments:        {shortcut.Arguments}")
        print(f"     WorkingDirectory: {shortcut.WorkingDirectory}")
        print(f"     IconLocation:     {shortcut.IconLocation}")
        return True
    except Exception as e:
        print(f"[Warning] Could not create desktop shortcut: {e}")
        return False


if __name__ == "__main__":
    create_shortcut()
