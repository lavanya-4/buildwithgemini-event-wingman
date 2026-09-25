"""Main FastAPI Application for Event Wingman."""

import base64
import json
import os
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, File, HTTPException, Request, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from database import init_db
from services.event_recap_service import EventRecapService
from services.extraction_service import MemoryExtractionService
from services.followup_service import FollowUpService
from services.gemini_voice_service import GeminiVoiceService
from services.memory_service import MemoryService
from services.relationship_service import RelationshipService
from services.tts_service import TTSService

# Initialize database
init_db()

# Initialize core services
memory_service = MemoryService()
relationship_service = RelationshipService(memory_service)
followup_service = FollowUpService(memory_service)
event_recap_service = EventRecapService(memory_service, relationship_service)
extraction_service = MemoryExtractionService(memory_service)
tts_service = TTSService()

gemini_voice_service = GeminiVoiceService(
    memory_service=memory_service,
    relationship_service=relationship_service,
    followup_service=followup_service,
    recap_service=event_recap_service,
    extraction_service=extraction_service,
)

app = FastAPI(
    title="Event Wingman API",
    description="Real-time Gemini-powered voice agent and temporary event memory for networking.",
    version="1.0.0",
)

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class ChatRequest(BaseModel):
    message: str
    include_audio: bool = True


class FollowUpUpdateRequest(BaseModel):
    draft_message: Optional[str] = None
    status: Optional[str] = None
    action: Optional[str] = None


class FollowUpRegenerateRequest(BaseModel):
    tone: Optional[str] = "friendly_professional"


class TTSRequest(BaseModel):
    text: str


# -------------------------------------------------------------
# Real-Time Voice & Chat Endpoints
# -------------------------------------------------------------
@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    """Process natural speech/text turn, execute tools, extract memory, and return response."""
    result = gemini_voice_service.process_user_message(req.message)
    response_text = result["response_text"]

    audio_base64 = None
    if req.include_audio and response_text:
        audio_bytes = tts_service.synthesize(response_text)
        if audio_bytes:
            audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")

    return {
        "responseText": response_text,
        "toolCalls": result.get("tool_calls", []),
        "extracted": result.get("extracted", {}),
        "audioBase64": audio_base64,
    }


@app.post("/api/voice/process-audio")
async def process_audio_endpoint(file: UploadFile = File(...)):
    """Accepts recorded audio from microphone, transcribes with Cloud Speech or Gemini, and responds."""
    try:
        content = await file.read()
        mime_type = file.content_type or "audio/webm"

        # Transcribe with SpeechClient if available
        transcript = ""
        try:
            from google.cloud import speech
            speech_client = speech.SpeechClient()
            audio = speech.RecognitionAudio(content=content)
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS if "webm" in mime_type else speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=48000 if "webm" in mime_type else 16000,
                language_code="en-US",
                enable_automatic_punctuation=True,
            )
            response = speech_client.recognize(config=config, audio=audio)
            for res in response.results:
                transcript += res.alternatives[0].transcript + " "
            transcript = transcript.strip()
        except Exception as e:
            print(f"[process_audio] Cloud Speech transcription fallback: {e}")

        # If Cloud Speech failed on webm format, use Gemini multimodal audio
        if not transcript and gemini_voice_service.client:
            try:
                from google.genai import types
                audio_part = types.Part.from_bytes(data=content, mime_type=mime_type)
                gem_resp = gemini_voice_service.client.models.generate_content(
                    model=gemini_voice_service.model_name,
                    contents=[
                        audio_part,
                        "Transcribe the audio speech accurately without extra commentary.",
                    ],
                )
                transcript = gem_resp.text.strip()
            except Exception as e:
                print(f"[process_audio] Gemini audio transcription error: {e}")

        if not transcript:
            raise HTTPException(status_code=400, detail="Could not transcribe audio.")

        # Process through voice agent loop
        result = gemini_voice_service.process_user_message(transcript)
        response_text = result["response_text"]
        audio_bytes = tts_service.synthesize(response_text) if response_text else None

        return {
            "transcript": transcript,
            "responseText": response_text,
            "toolCalls": result.get("tool_calls", []),
            "extracted": result.get("extracted", {}),
            "audioBase64": base64.b64encode(audio_bytes).decode("utf-8") if audio_bytes else None,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/voice/tts")
async def tts_endpoint(req: TTSRequest):
    """Synthesize text to MP3 audio."""
    audio_bytes = tts_service.synthesize(req.text)
    if not audio_bytes:
        raise HTTPException(status_code=500, detail="TTS synthesis failed.")
    return Response(content=audio_bytes, media_type="audio/mpeg")


# -------------------------------------------------------------
# WebSocket for Live Audio / Real-Time Transcripts & Barge-in
# -------------------------------------------------------------
@app.websocket("/api/ws/voice")
async def websocket_voice_endpoint(websocket: WebSocket):
    """WebSocket for bidirectional real-time transcript streaming, state sync, and barge-in."""
    await websocket.accept()
    try:
        while True:
            msg_text = await websocket.receive_text()
            data = json.loads(msg_text)
            msg_type = data.get("type")

            if msg_type == "interrupt":
                # User spoke or clicked while agent was speaking: barge-in signal
                await websocket.send_json({
                    "type": "state_change",
                    "state": "LISTENING",
                    "message": "Playback interrupted by user.",
                })

            elif msg_type == "user_transcript":
                user_text = data.get("text", "").strip()
                if not user_text:
                    continue

                # Notify client agent is thinking
                await websocket.send_json({"type": "state_change", "state": "THINKING"})

                # Process message
                result = gemini_voice_service.process_user_message(user_text)
                response_text = result["response_text"]

                # Generate voice audio
                audio_base64 = None
                if response_text:
                    audio_bytes = tts_service.synthesize(response_text)
                    if audio_bytes:
                        audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")

                # Send agent response
                await websocket.send_json({
                    "type": "agent_response",
                    "responseText": response_text,
                    "toolCalls": result.get("tool_calls", []),
                    "audioBase64": audio_base64,
                })

                # Return to IDLE or LISTENING
                await websocket.send_json({
                    "type": "state_change",
                    "state": "SPEAKING" if audio_base64 else "IDLE",
                })

    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"[WebSocket] Error: {e}")


# -------------------------------------------------------------
# Structured Memory REST Endpoints
# -------------------------------------------------------------
@app.get("/api/memory/people")
async def get_people():
    return memory_service.list_people()


@app.get("/api/memory/people/{person_id}")
async def get_person_details(person_id: str):
    p = memory_service.get_person_by_id(person_id)
    if not p:
        raise HTTPException(status_code=404, detail="Person not found")
    p["recommendations"] = memory_service.list_recommendations(person_id)
    p["followups"] = memory_service.list_followups(person_id)
    return p


@app.delete("/api/memory/people/{person_id}")
async def delete_person(person_id: str):
    success = memory_service.delete_person(person_id)
    if not success:
        raise HTTPException(status_code=404, detail="Person not found")
    return {"status": "deleted", "personId": person_id}


@app.get("/api/memory/conversations")
async def get_conversations():
    return memory_service.list_conversations()


@app.get("/api/memory/topics")
async def get_topics():
    return memory_service.list_topics()


@app.get("/api/memory/ideas")
async def get_ideas():
    return memory_service.list_ideas()


@app.get("/api/memory/recommendations")
async def get_recommendations():
    return memory_service.list_recommendations()


@app.get("/api/memory/followups")
async def get_followups():
    return memory_service.list_followups()


@app.post("/api/memory/followups/{fid}/approve")
async def approve_followup(fid: str):
    updated = followup_service.approve_followup(fid)
    if not updated:
        raise HTTPException(status_code=404, detail="Followup not found")
    return updated


@app.post("/api/memory/followups/{fid}/cancel")
async def cancel_followup(fid: str):
    updated = followup_service.cancel_followup(fid)
    if not updated:
        raise HTTPException(status_code=404, detail="Followup not found")
    return updated


@app.put("/api/memory/followups/{fid}")
async def update_followup(fid: str, req: FollowUpUpdateRequest):
    updated = memory_service.update_followup(
        followup_id=fid,
        status=req.status,
        draft_message=req.draft_message,
        action=req.action,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Followup not found")
    return updated


@app.post("/api/memory/followups/{fid}/regenerate")
async def regenerate_followup(fid: str, req: FollowUpRegenerateRequest):
    updated = followup_service.regenerate_followup(fid, tone=req.tone or "friendly_professional")
    if not updated:
        raise HTTPException(status_code=404, detail="Followup not found")
    return updated


@app.post("/api/memory/clear")
async def clear_all_memories():
    memory_service.clear_all_data()
    gemini_voice_service.reset_chat()
    return {"status": "cleared", "message": "All event memories have been permanently cleared."}


# -------------------------------------------------------------
# Demo Mode Endpoints
# -------------------------------------------------------------
@app.post("/api/memory/demo/seed")
async def seed_demo():
    res = memory_service.seed_demo_data()
    gemini_voice_service.reset_chat()
    return res


@app.post("/api/memory/demo/clear")
async def clear_demo():
    memory_service.clear_demo_data()
    gemini_voice_service.reset_chat()
    return {"status": "cleared", "message": "Demo data cleared."}


# -------------------------------------------------------------
# Networking Intelligence & Graph Endpoints
# -------------------------------------------------------------
@app.get("/api/network/graph")
async def get_network_graph():
    return relationship_service.get_network_graph()


@app.get("/api/network/related")
async def get_related_people(query: str):
    return relationship_service.find_related_people(query)


@app.get("/api/network/insights")
async def get_insights():
    return relationship_service.get_proactive_insights()


# -------------------------------------------------------------
# Event Recap Endpoint
# -------------------------------------------------------------
@app.get("/api/recap")
async def get_event_recap():
    return event_recap_service.generate_recap()


# -------------------------------------------------------------
# Static Frontend Files Mount (when built)
# -------------------------------------------------------------
FRONTEND_DIST = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "dist"
)

if os.path.exists(FRONTEND_DIST):
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="static")
else:
    @app.get("/")
    async def index_fallback():
        return {
            "name": "Event Wingman API",
            "status": "online",
            "docs": "/docs",
            "message": "Frontend build is in progress.",
        }


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    print(f"Starting Event Wingman on {host}:{port}")
    uvicorn.run("main:app", host=host, port=port, reload=True)
