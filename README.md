# 🎙️ Dogesh Assistant

> Your personal AI-powered voice assistant — wake word activated, multi-provider LLM, beautiful dark UI.

---

## ✨ Features

| Feature | Details |
|---|---|
| 🔐 Auth | Per-user login / register (SQLite, local) |
| 🎙️ Wake Word | **"Hey Dogesh"** — always listening in background |
| 🔊 Voice Pipeline | Mic → STT → llmsays LLM → Tool → TTS |
| 🌐 Web Search | Speaks intent → opens Google in browser |
| 💬 Chat UI | Full ChatGPT-style message history |
| ⚡ Multi-Provider | Groq · OpenRouter · NIM · Fireworks · Baseten |
| 🧠 llmsays | Auto-selects model tier & fastest provider |

---

## 🗂️ Architecture

```
dogesh_assistant/
│
├── main.py                   ← flet run main.py
├── config.py                 ← colours, constants, system prompt
├── database.py               ← SQLite auth + JSON key store
├── requirements.txt
├── .env.example              ← copy → .env and fill keys
│
├── ui/
│   └── flet_ui.py            ← All screens: Login, Register, Calibration, API Setup, Chat
│
├── core/
│   └── app_state.py          ← Reactive state dataclass (user, status, history)
│
├── voice/
│   ├── wake_word.py          ← Background thread: listens for "Hey Dogesh"
│   ├── stt.py                ← SpeechRecognition wrapper (Google STT)
│   └── tts.py                ← pyttsx3 TTS engine (offline)
│
├── llm/
│   └── llm_service.py        ← LLMService class — wraps llmsays, manages chat history
│
└── tools/
    ├── search.py             ← search_web() → opens Google
    └── tool_router.py        ← intent → tool function dispatcher
```

---

## 🔄 User Journey

```
Install → Register/Login → Voice Calibration → API Key Setup → Chat Interface
                                                                     ↕
                                                          "Hey Dogesh, …"
                                                          Wake → STT → LLM
                                                          → Tool → TTS → Done
```

---

## 🧠 LLM Backend: `llmsays`

`llmsays` is a PyPI package that:
- Accepts a **single string prompt**
- Auto-routes to `small / medium / large / extra_large` model tier based on query complexity
- Tries providers in latency order with **automatic failover**
- Reads API keys from environment variables

```python
from llmsays import llmsays

response = llmsays(
    query="What's the weather in Paris?",
    max_tokens=512,
    temperature=0.3,
    provider_preference=["Groq", "Openrouter"],
)
```

### Provider env vars (set in `.env` or via GUI):

| Provider | Env Variable |
|---|---|
| Groq | `GROQ_API_KEY` |
| OpenRouter | `OPENROUTER_API_KEY` |
| NVIDIA NIM | `NIVIDIA_API_KEY` |
| Fireworks AI | `FIREWORKSAI_API_KEY` |
| Baseten | `BASETEN_API_KEY` |

---

## 🔧 Tool Execution System

The LLM is prompted to return structured JSON:

```json
{
  "intent": "search_web",
  "parameters": { "query": "latest AI news" },
  "response": "Searching Google for latest AI news…"
}
```

`tool_router.py` maps `intent` → Python function:

| Intent | Action |
|---|---|
| `search_web` | Opens `https://google.com/search?q=…` |
| `general_chat` | No tool — response is spoken/displayed |
| `open_url` | Opens arbitrary URL |

---

## ⚡ Quick Start

### Linux / macOS
```bash
git clone <repo>
cd dogesh_assistant
chmod +x setup.sh && ./setup.sh
source .venv/bin/activate
flet run main.py
```

### Windows
```
setup_windows.bat   ← double-click
flet run main.py
```

### Manual
```bash
pip install -r requirements.txt
cp .env.example .env   # edit with your keys
flet run main.py
```

### Linux audio fix (if mic not working)
```bash
sudo apt install portaudio19-dev libespeak1 espeak
pip install PyAudio
```

---

## 🎨 UI Pages

1. **Login** — username + password, routes to correct next step
2. **Register** — creates local account, goes to calibration
3. **Voice Calibration** — adjusts mic sensitivity, sample recordings
4. **API Setup** — enter provider keys, stored in `~/.dogesh/keys.json`
5. **Chat** — full assistant interface with mic, wake word toggle, status bar

---

## 🔮 Future Improvements

- [ ] Custom wake word ML model (Porcupine / openWakeWord)
- [ ] WhatsApp / email tool integration
- [ ] Streaming TTS (word-by-word playback)
- [ ] Multi-language STT (Whisper local)
- [ ] Persistent cloud sync of conversations
- [ ] Plugin system for user-defined tools
- [ ] Mobile build via Flet packaging (`flet build apk`)
- [ ] Voice profile biometric lock

---

## 📦 Key Dependencies

| Package | Purpose |
|---|---|
| `flet` | Cross-platform desktop/web UI |
| `llmsays` | Multi-provider LLM with auto-routing |
| `SpeechRecognition` | Microphone → text (Google STT) |
| `pyttsx3` | Offline text-to-speech |
| `PyAudio` | Low-level microphone capture |
| `openai` | OpenAI-compat SDK (provider fallback) |
