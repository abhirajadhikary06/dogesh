from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlmodel import Session, select
from ..database import get_session
from ..models import User
from ..schemas import AssistantQuery, AssistantResponse, VoiceCalibration, ApiKeysUpdate
from ..llm_service import LLMService
from ..security import get_current_user
from dotenv import load_dotenv
import os
import json
from urllib import request, error

load_dotenv()
router = APIRouter(prefix="/assistant", tags=["assistant"])

def _transcribe_with_model(audio_bytes: bytes, content_type: str, user_api_keys: dict) -> str:
    model_id = os.getenv("HF_WHISPER_MODEL", "openai/whisper-large-v3-turbo")
    api_token = (
        (user_api_keys or {}).get("HUGGINGFACE_API_TOKEN")
        or (user_api_keys or {}).get("HUGGINGFACE_API_KEY")
        or (user_api_keys or {}).get("HF_API_TOKEN")
        or os.getenv("HUGGINGFACE_API_TOKEN")
        or os.getenv("HUGGINGFACE_API_KEY")
        or os.getenv("HF_API_TOKEN")
    )

    if not api_token:
        raise HTTPException(
            400,
            "Missing Hugging Face token. Set HUGGINGFACE_API_TOKEN, HUGGINGFACE_API_KEY, or HF_API_TOKEN.",
        )

    endpoint = f"https://api-inference.huggingface.co/models/{model_id}"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": content_type or "application/octet-stream",
    }

    req = request.Request(endpoint, data=audio_bytes, headers=headers, method="POST")

    try:
        with request.urlopen(req, timeout=90) as resp:
            payload = resp.read().decode("utf-8")

        data = json.loads(payload)
        if isinstance(data, dict) and data.get("error"):
            raise HTTPException(502, f"Hugging Face transcription error: {data['error']}")

        text = data.get("text") if isinstance(data, dict) else ""
        return (text or "").strip()
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise HTTPException(502, f"Hugging Face HTTP error {exc.code}: {detail}")
    except error.URLError as exc:
        raise HTTPException(502, f"Hugging Face connection failed: {str(exc.reason)}")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(502, f"Transcription failed: {str(exc)}")

@router.post("/query", response_model=AssistantResponse)
def query_dogesh(
    query: AssistantQuery,
    current_email: str = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    user = session.exec(select(User).where(User.email == current_email)).first()
    if not user:
        raise HTTPException(404, "User not found")

    llm_service = LLMService(user_api_keys=user.api_keys)
    result = llm_service.send_prompt(query.text, query.history)

    if result.get("intent") == "google_search" and result.get("action") == "open_browser":
        url = f"https://www.google.com/search?q={query.text.replace(' ', '+')}"
        result["action_data"] = {"url": url}

    return AssistantResponse(
        response_text=result["response_text"],
        intent=result["intent"],
        action=result.get("action"),
        action_data=result.get("action_data")
    )

@router.post("/calibrate-voice")
def calibrate_voice(
    data: VoiceCalibration,
    current_email: str = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    user = session.exec(select(User).where(User.email == current_email)).first()
    user.is_calibrated = data.calibrated
    session.add(user)
    session.commit()
    return {"status": "Voice calibrated successfully"}

@router.put("/api-keys")
def update_api_keys(
    keys: ApiKeysUpdate,
    current_email: str = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    user = session.exec(select(User).where(User.email == current_email)).first()
    user.api_keys = keys.api_keys
    session.add(user)
    session.commit()
    return {"status": "API keys updated securely"}


@router.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    current_email: str = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    user = session.exec(select(User).where(User.email == current_email)).first()
    if not user:
        raise HTTPException(404, "User not found")

    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(400, "Empty audio payload")

    try:
        text = _transcribe_with_model(audio_bytes, file.content_type or "application/octet-stream", user.api_keys or {})
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(502, f"Transcription failed: {str(exc)}")

    return {"text": text}
