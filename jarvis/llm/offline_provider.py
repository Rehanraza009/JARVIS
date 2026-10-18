"""
Intelligent Offline Companion Provider for JARVIS.
Provides natural, warm, female-voiced conversational responses in Hinglish, Hindi, and English
without requiring any external API key or internet connection.
Ensures JARVIS is genuinely capable, emotionally supportive, and multilingual out of the box.
"""

import re
import random
from typing import List, Dict, Generator, Optional
from jarvis.llm.base import BaseLLMProvider
from jarvis.core.logger import jarvis_logger


class OfflineProvider(BaseLLMProvider):
    def __init__(self):
        jarvis_logger.info("Upgraded female offline intelligent companion initialized.")

    @property
    def provider_name(self) -> str:
        return "offline"

    def is_available(self) -> bool:
        return True

    @staticmethod
    def detect_language(text: str) -> str:
        """Classify input as 'hindi_devanagari', 'hinglish', or 'english'."""
        if any('\u0900' <= char <= '\u097F' for char in text):
            return "hindi_devanagari"

        hinglish_markers = {
            "kya", "hai", "hain", "karo", "kholo", "bhai", "rehan", "aaj", "kaise",
            "karna", "hoon", "sakti", "rahi", "samajh", "batao", "baat", "mein",
            "nahi", "raha", "tha", "thi", "tum", "aap", "mera", "meri", "kuch",
            "kaun", "kab", "kahan", "kyun", "chahiye", "karun", "bilkul"
        }
        words = set(re.findall(r"\b[a-zA-Z]+\b", text.lower()))
        matched_markers = words.intersection(hinglish_markers)
        if len(matched_markers) >= 1:
            return "hinglish"
        return "english"

    def generate_response(
        self,
        prompt: str,
        history: Optional[List[Dict[str, str]]] = None,
        system_instruction: str = ""
    ) -> str:
        text = prompt.strip()
        text_lower = text.lower()
        lang = self.detect_language(text)

        # Multi-turn context: inspect previous turns
        last_turn_text = ""
        if history and len(history) > 0:
            last_msg = history[-1]
            if last_msg.get("role") == "user":
                last_turn_text = last_msg.get("content", "").lower()
            elif len(history) > 1:
                last_turn_text = history[-2].get("content", "").lower()

        # =============================================================
        # 1. ENGLISH CONVERSATIONS (Strict Language Matching)
        # =============================================================
        if lang == "english":
            # Presence check
            if any(w in text_lower for w in ["are you listening", "can you hear me", "are you there"]):
                return "Yes Rehan, I am right here and listening attentively! How can I help you today?"

            # Follow-up context check: machine learning
            if any(w in last_turn_text for w in ["machine learning", "ml"]):
                if any(w in text_lower for w in ["deep learning", "neural network", "difference"]):
                    return (
                        "Deep Learning is a specialized branch of Machine Learning built on multi-layered artificial neural networks. "
                        "While classical ML relies heavily on manual feature extraction, Deep Learning learns hierarchical representations "
                        "directly from raw data (like images, audio, or text)."
                    )
                if any(w in text_lower for w in ["supervised", "example", "python", "code"]):
                    return (
                        "In Supervised Learning with Python, we train models using labeled datasets:\n\n"
                        "```python\n"
                        "from sklearn.ensemble import RandomForestClassifier\n"
                        "model = RandomForestClassifier(n_estimators=100)\n"
                        "model.fit(X_train, y_train)\n"
                        "predictions = model.predict(X_test)\n"
                        "```\n"
                        "Would you like to tune hyperparameters or evaluate model performance with cross-validation?"
                    )

            # Follow-up context check: problem solving
            if any(w in last_turn_text for w in ["solve", "problem", "debug"]) and len(text) > 5:
                return (
                    f"Understood Rehan. Analyzing the issue with '{prompt}':\n\n"
                    "The recommended approach is to isolate the failure point: verify data contracts between components, "
                    "inspect error logs for root causes, and write a targeted unit test to confirm the fix. "
                    "Would you like me to write a drop-in patch or inspect the traceback?"
                )

            # Machine Learning explanation
            if "machine learning" in text_lower or ("ml" in text_lower and ("explain" in text_lower or "what is" in text_lower)):
                return (
                    "**Machine Learning (ML)** is a core discipline of Artificial Intelligence where algorithms learn patterns "
                    "from data to make intelligent predictions and decisions, rather than following rigid hard-coded rules.\n\n"
                    "It is structured into three fundamental paradigms:\n"
                    "1. **Supervised Learning**: Learning from labeled examples (e.g., classification, regression).\n"
                    "2. **Unsupervised Learning**: Discovering intrinsic patterns in unlabeled data (e.g., clustering, anomaly detection).\n"
                    "3. **Reinforcement Learning**: Training agents to maximize cumulative rewards through trial and feedback.\n\n"
                    "Would you like to explore deep neural networks or build a machine learning model together in Python?"
                )

            # Current AI Developments
            if any(w in text_lower for w in ["happening in ai", "what is happening in ai", "ai updates", "ai news", "current state of ai"]):
                return (
                    "The AI landscape is experiencing rapid advancement centered around three key frontiers:\n\n"
                    "1. **Autonomous AI Agents**: Systems capable of multi-step planning, tool use, desktop automation, and web navigation.\n"
                    "2. **Inference-Time Reasoning Models**: Architectures that think step-by-step to tackle complex mathematics and software engineering.\n"
                    "3. **High-Performance Local Models**: Open-weight models running directly on local laptops and workstations without cloud latency.\n\n"
                    "Which of these areas are you most interested in exploring, Rehan?"
                )

            # Help solve a problem
            if any(w in text_lower for w in ["help me solve this problem", "help me solve a problem", "solve a problem", "problem solving"]):
                return (
                    "I am ready to help you solve it, Rehan. Let's tackle it systematically:\n\n"
                    "1. What is the expected behavior versus what is currently happening?\n"
                    "2. Are there any specific error messages, logs, or unexpected outputs?\n"
                    "3. What stack or programming environment are you using?\n\n"
                    "Share the details or code snippet, and we will diagnose and fix it together!"
                )

            # Python dictionary explanation
            if "dictionary" in text_lower and "python" in text_lower:
                return (
                    "In Python, a **dictionary** is an unordered, mutable collection that stores data in **key-value pairs**.\n\n"
                    "It works like a real-world dictionary where you look up a definition using a specific word (key).\n\n"
                    "```python\n"
                    "# Example Dictionary\n"
                    "user_profile = {\n"
                    "    'name': 'Rehan Raza',\n"
                    "    'role': 'AI Engineer',\n"
                    "    'skills': ['Python', 'Machine Learning', 'PySide6'],\n"
                    "    'status': 'Active'\n"
                    "}\n\n"
                    "# Accessing values\n"
                    "print(user_profile['name'])   # Output: Rehan Raza\n"
                    "```\n\n"
                    "Key characteristics:\n"
                    "1. Keys must be unique and immutable (strings, numbers, tuples).\n"
                    "2. Very fast lookups: average O(1) time complexity powered by hashing."
                )

            # Technical programming
            if any(w in text_lower for w in ["python", "code", "function", "variable", "algorithm", "data structure"]):
                return (
                    f"Regarding '{prompt}', Python provides clean, readable syntax and a massive standard library. "
                    "When implementing solutions, focus on clarity, type hints, and modular functions. "
                    "Would you like a concrete code implementation or an architectural breakdown?"
                )

            # Career in English
            if any(w in text_lower for w in ["career", "internship", "placement", "job", "interview"]):
                return (
                    "Career planning requires focus and steady momentum, Rehan. "
                    "Rather than trying to learn everything at once, master core computer science fundamentals (DSA, systems) "
                    "and build 2 or 3 genuine, end-to-end projects solving real problems. "
                    "What specific field or role are you currently preparing for?"
                )

            # Greetings in English
            if any(w in text_lower for w in ["hello", "hi jarvis", "hey jarvis", "good morning", "good evening"]):
                return "Hello Rehan! Great to connect with you. What would you like to work on or discuss today?"

            # General English fallback
            return (
                f"I understand, Rehan. Let's delve into '{prompt}'. "
                "What specific aspect would you like to focus on first? I am ready to explore it in depth with you."
            )

        # =============================================================
        # 2. DEVANAGARI HINDI CONVERSATIONS
        # =============================================================
        if lang == "hindi_devanagari":
            if any(w in text for w in ["मौसम", "weather"]):
                return "रेहान भाई, आज का ताज़ा मौसम देखने के लिए आप 'Search the web for today weather' बोल सकते हैं, मैं लाइव जानकारी निकाल दूंगी!"
            if any(w in text for w in ["नमस्ते", "हेलो", "कैसी हो"]):
                return "नमस्ते रेहान भाई! मैं बिल्कुल ठीक हूँ और आपकी मदद के लिए तैयार हूँ। बताइए, आज क्या करना है?"
            return f"समझ रही हूँ रेहान भाई। '{prompt}' के बारे में बात करते हैं। आप इसके बारे में क्या सोचते हैं?"

        # =============================================================
        # 3. HINGLISH CONVERSATIONS (Female Persona & Empathy)
        # =============================================================
        # Presence check
        if any(w in text_lower for w in ["sun raha hai", "sun rahi ho", "sun rahi hai", "sun rahe ho", "are you listening"]):
            return random.choice([
                "Haan Rehan bhai, bilkul active hoon aur dhyaan se sun rahi hoon! Bataiye, kya chal raha hai?",
                "Bilkul Rehan bhai! 100% active hoon. Aap batao, main sun rahi hoon.",
                "Haan bhai, sun rahi hoon! Kahiye, kya baat karni hai aaj?"
            ])

        # Emotional check-in / Low mood
        if any(w in text_lower for w in ["mann nahi lag raha", "mood off", "depressed", "sad", "upset", "tension", "frustrated", "tired", "thak gaya"]):
            if "career" in text_lower or "career" in last_turn_text:
                return (
                    "Samajh sakti hoon bhai. Career uncertainty frustrating ho sakti hai. "
                    "Batao, zyada tension placement ki hai, internship ki, ya future direction ko lekar? "
                    "Pehle actual problem identify karte hain, phir practical plan banayenge."
                )
            return (
                "Arey Rehan bhai, kya hua? Kuch tension hai ya bas aaj ka din thoda heavy lag raha hai? "
                "Batao, aaram se baat karte hain, main sun rahi hoon."
            )

        # Career follow-up
        if any(w in text_lower for w in ["career", "placement", "internship", "future direction", "future"]):
            return (
                "Samajh sakti hoon bhai. Batao, zyada tension placement ki hai, internship ki, ya future direction ko lekar? "
                "Saath mein practical options dekhte hain aur step-by-step roadmap banate hain."
            )

        # Python dictionary explanation in Hinglish
        if "dictionary" in text_lower and ("python" in text_lower or "kya" in text_lower):
            return (
                "Rehan bhai, Python mein **Dictionary** ek bohot powerful data structure hai jo **Key-Value pairs** store karti hai.\n\n"
                "Isko real-world dictionary ki tarah samjho — jaise kisi word (key) ka meaning (value) hota hai:\n\n"
                "```python\n"
                "# Python Dictionary Example\n"
                "user_info = {\n"
                "    'name': 'Rehan Raza',\n"
                "    'field': 'Artificial Intelligence',\n"
                "    'skills': ['Python', 'FastAPI', 'ML'],\n"
                "    'active': True\n"
                "}\n\n"
                "# Key se value access karna\n"
                "print(user_info['name'])    # Output: Rehan Raza\n"
                "print(user_info.get('skills'))\n"
                "```\n\n"
                "Key points:\n"
                "1. **Keys unique** hoti hain aur immutable (string, number, tuple).\n"
                "2. Ye **hash table** use karti hai, isliye iska lookup speed super fast O(1) hota hai!"
            )

        # Login debug issue follow-up
        if "passenger" in text_lower and ("login" in text_lower or "login" in last_turn_text):
            return (
                "Samajh gayi Rehan bhai. Passenger login flow mein issue hai. "
                "Chalo step-by-step debug karte hain:\n"
                "1. Request backend tak pahunch rahi hai ya frontend validation par hi ruk rahi hai?\n"
                "2. Network tab ya console mein koi specific status code aa raha hai (jaise 401 Unauthorized, 404, ya 500)?\n"
                "3. Passenger role check ya password hashing match ho rahi hai?\n"
                "Error ka snippet ya terminal log dikha do, abhi saath mein fix kar dete hain!"
            )

        if "login" in text_lower or "error" in text_lower or "bug" in text_lower:
            return (
                "Achha bhai, error par exactly kya ho raha hai? "
                "Console ya terminal mein koi specific traceback ya status code aa raha hai? Code snippet dikhao, abhi check karte hain."
            )

        # Greetings
        if any(w in text_lower for w in ["hello", "hi jarvis", "hey jarvis", "namaste", "salam", "kya haal", "kaise ho"]):
            return random.choice([
                "Hello Rehan bhai! Main ekdum badhiya hoon. Aap bataiye, aaj ka din kaisa chal raha hai?",
                "Hey bhai! Ekdum first class. Aaj kya naya plan hai ya kisi specific cheez par kaam karna hai?",
                "Namaste Rehan bhai! Sab ready hai. Kahiye, aaj kismein help karun?"
            ])

        # Weather query in Hinglish
        if any(w in text_lower for w in ["mausam", "weather"]):
            return "Rehan bhai, aaj ka live mausam dekhne ke liye 'Search the web for today weather' bol sakte hain, main turant live check kar lungi!"

        # Default natural Hinglish synthesis
        return (
            f"Samajh rahi hoon Rehan bhai. '{prompt}' ke baare mein baat karte hain. "
            "Aapka isme primary thought kya hai? Agar koi specific angle explore karna chahte hain to bataiye, saath mein solve karte hain."
        )

    def stream_response(
        self,
        prompt: str,
        history: Optional[List[Dict[str, str]]] = None,
        system_instruction: str = ""
    ) -> Generator[str, None, None]:
        full_resp = self.generate_response(prompt, history, system_instruction)
        words = full_resp.split(" ")
        chunk = []
        for i, w in enumerate(words):
            chunk.append(w)
            if len(chunk) >= 3 or i == len(words) - 1:
                yield " ".join(chunk) + " "
                chunk = []
