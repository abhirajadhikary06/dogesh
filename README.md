# Dogesh Assistant

Dogesh is a FastAPI-based voice assistant backend with a lightweight web frontend.
It supports:

- User signup/login with JWT auth
- Post-login voice calibration
- LLM-backed assistant chat
- Voice transcription using Hugging Face Whisper API
- Per-user provider API key storage

## Project Structure

```text
dogesh/
  app/
    main.py
    database.py
    llm_service.py
    models.py
    schemas.py
    security.py
    routers/
      auth.py
      assistant.py
  frontend/
    index.html
    styles.css
    app.js
  requirements.txt
  run.bat
```

## Requirements

- Python 3.10+
- A PostgreSQL database URL (or any SQLAlchemy-compatible URL supported by SQLModel)
- A Hugging Face token for inference API (for `/assistant/transcribe`)

## Setup

1. Open terminal in the project root:

```bash
cd dogesh
```

2. Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Windows (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Environment Variables

Create a `.env` file in the project root (`dogesh/.env`).

Example:

```env
DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/DBNAME
SECRET_KEY=replace-with-a-long-random-secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Optional provider keys (can also be saved per-user from frontend)
GROQ_API_KEY=
OPENROUTER_API_KEY=
NVIDIA_API_KEY=
FIREWORKSAI_API_KEY=
BASETEN_API_KEY=
HUGGINGFACE_API_TOKEN=
HF_WHISPER_MODEL=openai/whisper-large-v3-turbo

# Optional typo fallback supported by code
NIVIDIA_API_KEY=

# Optional alias also accepted by backend
HF_API_TOKEN=
```

Important:

- Do not commit real API keys or secrets.
- If credentials were committed before, rotate them immediately.

## Whisper API Setup

The transcribe endpoint calls Hugging Face Inference API using:

- `openai/whisper-large-v3-turbo`

Set in `.env`:

- `HUGGINGFACE_API_TOKEN` (or `HF_API_TOKEN`)
- `HF_WHISPER_MODEL` (optional override, defaults to `openai/whisper-large-v3-turbo`)

If no token is configured, `/assistant/transcribe` returns HTTP 400.

## Run Backend

Linux/macOS:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Windows CMD:

```bat
run.bat
```

API root:

- `http://127.0.0.1:8000/`

Swagger docs:

- `http://127.0.0.1:8000/docs`

## Run Frontend

The frontend is static HTML/CSS/JS and should be served over HTTP.

From project root:

```bash
python -m http.server 5500 -d frontend
```

Then open:

- `http://127.0.0.1:5500`

In the UI, set Backend URL to:

- `http://127.0.0.1:8000`

## Authentication Flow

- Signup: `POST /auth/signup`
- Login: `POST /auth/login`
- Both return:

```json
{
  "access_token": "...",
  "token_type": "bearer"
}
```

Protected assistant routes require header:

```http
Authorization: Bearer <access_token>
```

## Assistant Endpoints

Base prefix: `/assistant`

1. `POST /assistant/query`
- Body:

```json
{
  "text": "What is the weather?",
  "history": [
    {"role": "user", "content": "Hi"},
    {"role": "assistant", "content": "Hello!"}
  ]
}
```

- Response shape:

```json
{
  "response_text": "...",
  "intent": "general_qa",
  "action": null,
  "action_data": null
}
```

2. `POST /assistant/calibrate-voice`
- Body:

```json
{
  "calibrated": true
}
```

3. `PUT /assistant/api-keys`
- Body:

```json
{
  "api_keys": {
    "GROQ_API_KEY": "..."
  }
}
```

4. `POST /assistant/transcribe`
- Multipart form-data with field `file` (WAV works best)
- Response:

```json
{
  "text": "transcribed speech"
}
```

## Frontend Behavior

- Login or signup first.
- Post-login setup requires:
  - 10-second voice enrollment (must detect "Dogesh" at least once)
  - Saving at least one provider API key
- After setup completion:
  - Chat input and mic controls are enabled
  - Wake-word flow listens for "Hey Dogesh"

## Notes

- CORS is currently open (`allow_origins=["*"]`) for development convenience.
- Password hashing uses `pbkdf2_sha256`.
- JWT token extraction expects subject in `sub` claim.

## Quick Test (curl)

Signup:

```bash
curl -X POST "http://127.0.0.1:8000/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"yourpassword"}'
```

Assistant query:

```bash
curl -X POST "http://127.0.0.1:8000/assistant/query" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"text":"Hello Dogesh","history":[]}'
```

## Troubleshooting

- `Missing Hugging Face token...`
  - Set `HUGGINGFACE_API_TOKEN` or `HF_API_TOKEN` in `.env`.
- `Could not validate credentials`
  - Ensure token is present and not expired.
- `Request failed (401)` from frontend
  - Re-login and verify backend URL in the UI.
- DB connection errors on startup
  - Check `DATABASE_URL` and network access to your database.
