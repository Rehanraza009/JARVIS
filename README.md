# JARVIS 2.0 — NATURAL MALE & FEMALE AI FRIEND & WINDOWS ASSISTANT
### *Companion, Intellectual Confidant & Real Windows Automation for Rehan Raza*

JARVIS 2.0 is a complete, production-grade upgrade built in Python and PySide6. It features a natural female persona, real-time context-aware conversation in Hindi, Hinglish, and English, a pleasant multilingual neural female voice, hands-free continuous interaction, and real Windows computer control.

---

## 🌟 What's New in JARVIS 2.0

1. **Natural Female AI Persona & Language Matching**:
   - Speaks with natural feminine verb endings in Hindi and Hinglish (*"Arey Rehan bhai, kya hua? ... Batao, sun rahi hoon"*, *"Samajh sakti hoon bhai"*, *"Windows Settings khol rahi hoon"*).
   - **Strict Language Matching**: Hindi/Hinglish input receives natural Hinglish/Hindi replies; English queries (e.g. *"What is a dictionary in Python?"*) receive fluent, structured English replies with runnable code examples.
2. **Pleasant Natural Neural Female Voice**:
   - Default TTS powered by Microsoft Edge Neural Voices: **`hi-IN-SwaraNeural`** (Warm, natural Hindi/Hinglish female voice) and **`en-IN-NeerjaNeural`** (Fluent Indian English female voice).
   - Offline fallback automatically selects **Microsoft Zira** on Windows SAPI5.
   - Automatic language-adaptive voice selection matching the response language.
   - Guaranteed state recovery: TTS failures or player interruptions never leave the application stuck in `SPEAKING`.
3. **Hands-Free Conversation (3 Distinct Modes)**:
   - **Mode 1: Push-to-Talk**: Click microphone button, speak, and release.
   - **Mode 2: Continuous Conversation**: Automatically listens, transcribes, processes, speaks, and resumes listening without clicking.
   - **Mode 3: Wake-Word Detection**: Activates on *"Hey Jarvis"*, *"Jarvis bhai"*, or *"Jarvis, sun rahi ho?"*.
   - **Acoustic Echo Guard**: Automatically mutes the microphone while the assistant is speaking or thinking to prevent feedback loops and duplicate command execution.
   - **Mic Mute Button**: Easily mute/unmute the microphone with one click.
4. **Real Windows Command Execution & Automation**:
   - **Windows Settings**: *"Settings kholo"*, *"Setting on karo"*, *"Windows settings open karo"*, *"Bluetooth settings kholo"*, *"Wi-Fi settings kholo"*, *"Display settings kholo"*, *"Sound settings kholo"*.
   - **Application Control**: *"Chrome kholo"*, *"Paint kholo"*, *"Notepad open karo"*, *"Calculator kholo"*, *"VS Code open karo"*, *"File Explorer kholo"*, *"Terminal kholo"*.
   - **Unknown App Handling**: Verifies if an application exists on the system; if not found, reports an honest error instead of pretending to launch it.
   - **Window Management**: *"Window minimize karo"*, *"Window maximize karo"*, *"Active window close karo"*.
   - **System Power Actions (with Confirmation)**: *"Laptop shutdown karo"* and *"Laptop restart karo"* require explicit confirmation dialogs before initiating action.
   - **App Navigation**: *"Jarvis settings kholo"* flips to the in-app Settings tab; *"Voice change karo"* guides voice selection.
5. **One-Click Windows Desktop Shortcut & Silent Launch**:
   - Includes `JARVIS.vbs` for completely silent background launch without a black console window.
   - Includes `create_desktop_shortcut.py` which places a one-click **JARVIS.lnk** directly onto your Windows Desktop.

---

## 🏗️ Architecture

```
JARVIS/
├── run_jarvis.py                   # Main entry point (GUI, CLI, --startup, --test-greeting)
├── JARVIS.vbs                      # Silent VBScript launcher (no console window)
├── run_jarvis.bat                  # Standard Windows batch launcher
├── create_desktop_shortcut.py      # Desktop shortcut generator
├── requirements.txt                # Production dependencies
├── .env.example                    # Environment variable template
├── jarvis/
│   ├── core/
│   │   ├── config.py               # Settings, female voice defaults, listening mode
│   │   ├── logger.py               # Rotating file and console structured logging
│   │   └── events.py               # Qt event bus and assistant states
│   ├── memory/
│   │   ├── database.py             # SQLite connection pooling with contextmanager
│   │   └── memory_service.py       # Personal memory CRUD, search, intent detection
│   ├── llm/
│   │   ├── base.py                 # Abstract LLM provider interface
│   │   ├── gemini_provider.py      # Google Gemini integration
│   │   ├── openai_provider.py      # OpenAI / Groq / DeepSeek / Ollama integration
│   │   ├── offline_provider.py     # Built-in female companion fallback engine
│   │   └── provider_factory.py     # Dynamic factory with resilient fallback
│   ├── conversation/
│   │   ├── prompt_templates.py     # System persona tailored for Rehan bhai (Female)
│   │   ├── context_manager.py      # Multi-turn rolling history and session manager
│   │   └── conversation_manager.py # Orchestrator linking memory, tools, and LLMs
│   ├── speech/
│   │   ├── audio_player.py         # Interruptible QtMultimedia audio player with error recovery
│   │   ├── tts_engine.py           # Edge-TTS neural female voice & pyttsx3 fallback
│   │   ├── stt_engine.py           # SpeechRecognition with Continuous & Push-to-Talk modes
│   │   └── wake_word.py            # Wake-word detection listener with mic contention guard
│   ├── tools/
│   │   ├── action_registry.py      # Real Windows command classification and dispatcher
│   │   ├── system_tools.py         # ms-settings: URIs, Chrome, Paint, win32gui window control
│   │   ├── web_search.py           # DuckDuckGo search with citations
│   │   ├── doc_reader.py           # Text & PDF document reader
│   │   └── tasks_manager.py        # SQLite task and reminder manager
│   ├── startup/
│   │   ├── windows_startup.py      # Windows Registry HKCU startup integration
│   │   └── greeting_service.py     # Time-aware natural female greeting generator
│   └── ui/
│       ├── styles.py               # Futuristic Dark Navy QSS design system
│       ├── orb_widget.py           # Custom animated AI Orb with QPainter
│       ├── chat_widget.py          # Message history, timestamps, mode combo, mute mic
│       ├── memory_widget.py        # Memory inspector, search, CRUD, JSON import/export
│       ├── tasks_widget.py         # Task checklist and due-date tracker
│       ├── tools_widget.py         # Quick launchers, doc preview, audit logs
│       ├── settings_widget.py      # Settings panel for models, female voices, startup
│       └── main_window.py          # Master application window
└── tests/
    ├── test_config.py              # Configuration tests
    ├── test_memory.py              # Memory CRUD, search, and intent extraction tests
    ├── test_conversation.py        # Language matching, female tone, context, and action tests
    ├── test_llm_providers.py       # Female offline provider and LLM fallback tests
    ├── test_tools.py               # Settings commands, apps, window control, shutdown tests
    ├── test_speech_system.py       # Female voice resolution, mute, and player stop tests
    └── test_startup_greeting.py    # Time-of-day greeting and startup tests
```

---

## 🚀 Quick Start Guide

### 1. Requirements
- Windows 10 or Windows 11
- Python 3.10+ (Tested on Python 3.13)
- Microphone and speakers/headphones

### 2. Installation
Open PowerShell in the project directory:
```powershell
pip install -r requirements.txt
```

### 3. Launching JARVIS Desktop Application
You have multiple reliable ways to launch JARVIS:
1. **Desktop Shortcut**: Double-click the **JARVIS** icon on your Desktop (`C:\Users\REAHAN\Desktop\JARVIS.lnk`), which executes via `wscript.exe` with full path resolution and startup logging.
2. **Silent Windows Launcher**: Double-click `JARVIS.vbs` in the project root (runs completely windowless in the background, logs diagnostics, and shows informative error popups if startup fails).
3. **Batch Launcher with Console Output**: Double-click `run_jarvis.bat` (ideal for checking real-time console messages and error codes).
4. **Direct Python Launch**:
   ```powershell
   python run_jarvis.py
   ```

> [!NOTE]
> All launcher and startup diagnostics are automatically captured in `data/startup_launcher.log` and `data/jarvis.log`. If any startup error occurs, a native Windows alert dialog will immediately inform you of the issue and point to the log file.

### 4. Windows Sign-in Startup
You can configure JARVIS to open automatically upon Windows login:
- Open JARVIS, navigate to **⚙️ Settings**, check **"Launch JARVIS automatically on Windows sign-in"**, and click **💾 Save Configuration**.
- It registers `wscript.exe` with `JARVIS.vbs --startup` into `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`.

### 5. Interactive Terminal CLI Mode (Optional)
```powershell
python run_jarvis.py --cli
```

### 6. Preview Female Startup Greeting
```powershell
python run_jarvis.py --test-greeting
```

---

## 🎙️ Voice & Hands-Free Interaction

### Listening Modes
Switch modes easily from the dropdown in the **💬 Conversation** tab or in **⚙️ Settings**:
1. **🎙️ Push-to-Talk**: Click the mic button to speak a single phrase.
2. **🔄 Continuous Hands-Free**: JARVIS listens automatically, responds in female voice, and immediately resumes listening.
3. **⚡ Wake Word ('Hey Jarvis')**: Activates background listening on phrases like *"Hey Jarvis"*, *"Jarvis bhai"*, or *"Jarvis, sun rahi ho?"*.

### Mute Control
Click **🎙️ Mic Active** in the chat bar to mute the microphone (**🔇 Muted**).

### Emergency Stop
While JARVIS is speaking, click the red **⏹ Stop** button to cut off speech instantly.

---

## 💻 Supported Windows Commands

Speak or type these commands naturally:

| Category | Voice / Text Commands | Real Action Performed |
| :--- | :--- | :--- |
| **Settings** | *"Setting on karo"*<br>*"Settings kholo"*<br>*"Windows settings open karo"* | Opens Windows Settings (`ms-settings:`) |
| **Bluetooth & Wi-Fi** | *"Bluetooth settings kholo"*<br>*"Wi-Fi settings kholo"* | Opens Bluetooth / Wi-Fi Settings directly |
| **In-App Settings** | *"JARVIS settings kholo"*<br>*"JARVIS settings band karo"* | Navigates between Settings and Chat tabs |
| **Applications** | *"Chrome kholo"*<br>*"Chrome on karo"*<br>*"WhatsApp kholo"*<br>*"Notepad kholo"*<br>*"Calculator open karo"* | Resolves executable path / registry and launches application |
| **Close Applications** | *"Chrome band karo"*<br>*"Chrome close karo"*<br>*"Notepad band karo"* | Safely closes target application window without terminating unrelated processes |
| **Folders** | *"Downloads folder kholo"*<br>*"Documents folder kholo"*<br>*"Desktop folder kholo"* | Opens folder directly in Windows File Explorer |
| **Volume Control** | *"Volume badhao"*<br>*"Volume kam karo"*<br>*"Audio mute karo"* | Real hardware volume adjustment via Windows multimedia keys |
| **Voice Listening Control**| *"Jarvis, stop listening"*<br>*"Jarvis, listen again"* | Mutes/pauses or unmutes/resumes microphone processing by voice |
| **Daily Plan & Tasks** | *"Aaj ka plan batao"*<br>*"Maine aaj kya-kya complete kiya?"*<br>*"Meri pending tasks batao"* | Queries SQLite tasks, prioritizes by deadline, and formats realistic daily plan |
| **Personal Memory & Goals**| *"Mere current goals kya hain?"*<br>*"Ye information yaad rakhna"*<br>*"Is memory ko bhool jao"* | Stores, updates, searches, and deletes approved long-term personal context |
| **Websites & Research** | *"GitHub kholo"*<br>*"YouTube kholo"*<br>*"Google par Python search karo"* | Opens bookmarks or executes real-time web research |
| **Window Control** | *"Window minimize karo"*<br>*"Window maximize karo"*<br>*"Active window close karo"* | Controls active foreground window via win32gui |
| **System Power** | *"Laptop shutdown karo"*<br>*"Laptop restart karo"* | Prompts for confirmation before initiating shutdown/restart |

---

## 🧪 Automated Testing

Run the complete test suite:
```powershell
python -m pytest -v
```

All **53 automated unit & integration tests** pass with 100% success:
- Fast action local command router ("Chrome kholo", "WhatsApp kholo", "Chrome band karo", "Windows Settings kholo")
- Folder opening ("Downloads folder kholo", "Documents folder kholo")
- Native volume controls ("Volume badhao", "Volume kam karo", "Volume mute karo")
- Voice listening controls ("Jarvis, stop listening", "Jarvis, listen again")
- Daily planning and completed tasks ("Aaj ka plan batao", "Maine aaj kya-kya complete kiya?")
- Memory goals and personal context ("Mere current goals kya hain?")
- Single-instance IPC socket with foreground window elevation (`SetForegroundWindow`)
- Floating Companion widget state and drag interactions
- Edge-TTS natural female voice resolution (`hi-IN-SwaraNeural`, `en-IN-NeerjaNeural`)
- STT echo guard and turn completion race-condition prevention
- Time-of-day greeting deduplication and Windows startup registry integration
- Destructive actions security confirmations (shutdown / restart)
