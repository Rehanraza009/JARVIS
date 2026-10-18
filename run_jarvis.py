"""
JARVIS — Main Entry Point
Launches the PySide6 Desktop GUI application or CLI mode.
Includes comprehensive startup error logging, exception dialogs,
and dual stdout/stderr capture to data/startup_launcher.log.
"""

import sys
import os
import argparse
import datetime
import traceback
from pathlib import Path

# Add project root to sys.path and ensure working directory context
BASE_DIR = Path(__file__).resolve().parent
os.chdir(str(BASE_DIR))
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Ensure data directory exists
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
STARTUP_LOG_FILE = DATA_DIR / "startup_launcher.log"


def show_fatal_startup_dialog(title: str, message: str):
    """Show a native Windows error dialog using Win32 API without requiring PySide6."""
    try:
        import ctypes
        # 0x10 = MB_ICONERROR, 0x1000 = MB_SYSTEMMODAL
        ctypes.windll.user32.MessageBoxW(0, message, title, 0x10 | 0x1000)
    except Exception:
        pass


class StartupLogWriter:
    """Redirects stdout and stderr to startup_launcher.log while preserving console output."""
    def __init__(self, log_path: Path, original_stream=None):
        self.log_path = log_path
        self.original_stream = original_stream

    def write(self, text: str):
        if not text:
            return
        if self.original_stream is not None:
            try:
                self.original_stream.write(text)
                self.original_stream.flush()
            except Exception:
                pass
        try:
            with open(self.log_path, "a", encoding="utf-8", errors="replace") as f:
                f.write(text)
        except Exception:
            pass

    def flush(self):
        if self.original_stream is not None:
            try:
                self.original_stream.flush()
            except Exception:
                pass


# Initialize stdout and stderr capture
orig_stdout = sys.stdout
orig_stderr = sys.stderr
sys.stdout = StartupLogWriter(STARTUP_LOG_FILE, orig_stdout)
sys.stderr = StartupLogWriter(STARTUP_LOG_FILE, orig_stderr)


def global_exception_handler(exc_type, exc_value, exc_traceback):
    """Global uncaught exception handler to capture and alert on any fatal crash."""
    tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
    tb_text = "".join(tb_lines)

    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    error_msg = (
        f"[{now_str}] [FATAL_CRASH]\n"
        f"Python: {sys.executable}\n"
        f"WorkingDir: {os.getcwd()}\n"
        f"Exception: {exc_type.__name__}: {exc_value}\n\n"
        f"{tb_text}\n"
    )
    sys.stderr.write(error_msg)
    sys.stderr.flush()

    user_alert = (
        f"JARVIS encountered a critical startup error and cannot open:\n\n"
        f"{exc_type.__name__}: {exc_value}\n\n"
        f"Python interpreter: {sys.executable}\n\n"
        f"Full details have been recorded in the startup log:\n"
        f"{STARTUP_LOG_FILE}"
    )
    show_fatal_startup_dialog("JARVIS — Startup Error", user_alert)


sys.excepthook = global_exception_handler

# Log startup banner
now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
print(f"\n============================================================")
print(f"[{now_str}] JARVIS Startup Initiated")
print(f"Python Executable: {sys.executable}")
print(f"Python Version   : {sys.version.split()[0]}")
print(f"Arguments        : {sys.argv}")
print(f"Project Root     : {BASE_DIR}")
print(f"============================================================")

# Import core modules with safe error handling
try:
    from jarvis.core.logger import jarvis_logger
    from jarvis.core.config import active_config
    from jarvis.speech.wake_word import wake_word_service
    from jarvis.speech.tts_engine import tts_engine
except Exception as e:
    err_text = f"Failed to import core JARVIS modules: {e}"
    print(f"[FATAL] {err_text}")
    traceback.print_exc()
    show_fatal_startup_dialog(
        "JARVIS — Core Module Import Error",
        f"Failed to load core JARVIS modules:\n\n{e}\n\n"
        f"Please verify dependencies are installed:\n"
        f"pip install -r requirements.txt\n\n"
        f"Startup log:\n{STARTUP_LOG_FILE}"
    )
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="JARVIS Personal AI Friend & Desktop Assistant")
    parser.add_argument("--startup", action="store_true", help="Launched from Windows login startup")
    parser.add_argument("--companion", action="store_true", help="Launch directly into Compact Companion Panel mode")
    parser.add_argument("--silent", action="store_true", help="Silent start without spoken greeting")
    parser.add_argument("--cli", action="store_true", help="Run interactive terminal CLI mode instead of GUI")
    parser.add_argument("--test-greeting", action="store_true", help="Test startup greeting text and voice")
    args = parser.parse_args()

    jarvis_logger.info("Initializing JARVIS...")

    if args.test_greeting:
        from jarvis.startup.greeting_service import greeting_service
        greeting = greeting_service.get_greeting_text()
        print(f"\n[JARVIS Startup Greeting Preview]\n{greeting}\n")
        tts_engine.speak(greeting)
        import time
        time.sleep(3)
        return

    if args.cli:
        from jarvis.conversation.conversation_manager import conversation_manager
        print(f"\n=== JARVIS CLI MODE (Active User: {active_config.user.user_name}) ===")
        print("Type your message (or 'exit' to quit):\n")
        while True:
            try:
                user_input = input(f"{active_config.user.preferred_address} > ")
                if not user_input.strip():
                    continue
                if user_input.lower().strip() in ["exit", "quit", "bye"]:
                    print("Alvida Rehan bhai! Take care.")
                    break
                response = conversation_manager.process_message(user_input)
                print(f"\nJARVIS > {response}\n")
            except (KeyboardInterrupt, EOFError):
                print("\nGoodbye Rehan bhai!")
                break
        return

    # PySide6 GUI Mode
    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import Qt
        from PySide6.QtNetwork import QLocalServer, QLocalSocket
        from jarvis.ui.main_window import MainWindow

        app = QApplication(sys.argv)
        app.setApplicationName("JARVIS")
        app.setOrganizationName("JARVIS_AI")

        SOCKET_NAME = "JARVIS_APP_SINGLE_INSTANCE_IPC"

        # Check if already running (Single-Instance check)
        socket = QLocalSocket()
        socket.connectToServer(SOCKET_NAME)
        if socket.waitForConnected(400):
            cmd = "COMPANION" if args.companion else "SHOW"
            socket.write(cmd.encode("utf-8"))
            socket.waitForBytesWritten(1000)
            socket.disconnectFromServer()
            msg = f"JARVIS is already running. Sent '{cmd}' signal to existing instance."
            print(msg)
            jarvis_logger.info(msg)
            sys.exit(0)

        # Primary instance: create IPC server
        ipc_server = QLocalServer()
        ipc_server.removeServer(SOCKET_NAME)  # Clean up any stale lock
        ipc_server.listen(SOCKET_NAME)

        window = MainWindow(
            is_startup_launch=args.startup,
            start_as_companion=args.companion,
            silent_greeting=args.silent
        )

        def _on_ipc_client_connected():
            client = ipc_server.nextPendingConnection()
            if client:
                client.waitForReadyRead(500)
                data = bytes(client.readAll()).decode("utf-8").strip()
                if data == "COMPANION":
                    window._show_companion_mode()
                else:
                    window._show_dashboard()
                client.disconnectFromServer()

        ipc_server.newConnection.connect(_on_ipc_client_connected)

        if not args.companion:
            window.show()

        gui_ready_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{gui_ready_time}] PySide6 GUI window displayed successfully.")
        jarvis_logger.info("JARVIS GUI window displayed successfully.")

        exit_code = app.exec()

        # Clean shutdown
        ipc_server.close()
        ipc_server.removeServer(SOCKET_NAME)
        wake_word_service.stop()
        tts_engine.stop()
        sys.exit(exit_code)

    except Exception as e:
        jarvis_logger.critical(f"Fatal error starting JARVIS GUI: {e}", exc_info=True)
        print(f"Error launching JARVIS GUI: {e}")
        traceback.print_exc()
        show_fatal_startup_dialog(
            "JARVIS — GUI Launch Failure",
            f"Failed to launch the JARVIS interface:\n\n{e}\n\n"
            f"Please check the log at:\n{STARTUP_LOG_FILE}"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
