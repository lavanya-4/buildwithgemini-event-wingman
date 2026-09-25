"""Extraction Service for analyzing conversational turns and extracting structured event entities."""

import json
import os
import re
from typing import Any, Dict, List, Optional
from google import genai
from google.genai import types
from services.memory_service import MemoryService


EXTRACTION_PROMPT = """
You are an expert event information extraction engine for Event Wingman.
Analyze the user utterance from a conference/hackathon/meetup.
Determine if the user is sharing past or new information about someone they met, a conversation, a recommendation, an idea, or a promised follow-up.

IMPORTANT: If the user is asking a command or query (e.g., "Draft a follow-up to Sarah", "Who did I talk to about voice agents?", "Give me my event recap", "What did Sarah recommend?"), this is NOT an event memory report. Set "has_event_info": false and all other fields to null or empty lists.

Respond with ONLY valid JSON adhering to this schema:
{
  "has_event_info": boolean,
  "person": {
    "name": string or null,
    "company": string or null,
    "role": string or null,
    "topics": [string]
  } or null,
  "conversation": {
    "summary": string or null,
    "topics": [string]
  } or null,
  "recommendations": [
    {
      "content": string,
      "recommended_by": string or null,
      "context": string or null
    }
  ],
  "ideas": [
    {
      "title": string,
      "description": string or null
    }
  ],
  "follow_up": {
    "person_name": string or null,
    "action": string or null,
    "context": string or null
  } or null
}
"""


class MemoryExtractionService:
    def __init__(self, memory_service: MemoryService):
        self.memory = memory_service
        self.client = None
        self._init_gemini()

    def _init_gemini(self):
        project = os.environ.get("GOOGLE_CLOUD_PROJECT", "qwiklabs-gcp-01-9c5a198b6a9e")
        location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
        use_vertex = os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "true").lower() in ("true", "1")
        api_key = os.environ.get("GEMINI_API_KEY")

        try:
            if api_key:
                self.client = genai.Client(api_key=api_key)
            else:
                self.client = genai.Client(vertexai=use_vertex, project=project, location=location)
        except Exception as e:
            print(f"[ExtractionService] Warning: Could not initialize Gemini client: {e}")

    def extract_and_persist(self, user_utterance: str) -> Dict[str, Any]:
        """Extract structured memory from natural speech and persist into MemoryService."""
        if not self.client:
            return {"status": "skipped", "reason": "Gemini client not initialized"}

        try:
            response = self.client.models.generate_content(
                model=os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"),
                contents=[
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_text(text=f"{EXTRACTION_PROMPT}\n\nUser utterance:\n\"{user_utterance}\"")
                        ],
                    )
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1,
                ),
            )

            raw_text = response.text.strip()
            # Clean possible markdown fence
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.startswith("```"):
                raw_text = raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]

            data = json.loads(raw_text.strip())
            if not data.get("has_event_info"):
                return {"has_event_info": False}

            saved_entities = {}

            # 1. Person
            person_data = data.get("person")
            saved_person = None
            if person_data and person_data.get("name"):
                saved_person = self.memory.save_person(
                    name=person_data["name"],
                    company=person_data.get("company"),
                    role=person_data.get("role"),
                    topics=person_data.get("topics", []),
                )
                saved_entities["person"] = saved_person

            # 2. Recommendations
            for rec in data.get("recommendations", []):
                rec_by = rec.get("recommended_by")
                target_person_id = None
                if rec_by:
                    p = self.memory.get_person_by_name(rec_by)
                    if p:
                        target_person_id = p["id"]
                elif saved_person:
                    target_person_id = saved_person["id"]

                s_rec = self.memory.save_recommendation(
                    content=rec["content"],
                    recommended_by_person_id=target_person_id,
                    context=rec.get("context"),
                )
                saved_entities.setdefault("recommendations", []).append(s_rec)

            # 3. Ideas
            for idea in data.get("ideas", []):
                s_idea = self.memory.save_idea(
                    title=idea["title"],
                    description=idea.get("description"),
                    source_person_id=saved_person["id"] if saved_person else None,
                )
                saved_entities.setdefault("ideas", []).append(s_idea)

            # 4. Conversation
            conv_data = data.get("conversation")
            if conv_data and (conv_data.get("summary") or saved_person):
                p_ids = [saved_person["id"]] if saved_person else []
                s_conv = self.memory.save_conversation(
                    person_ids=p_ids,
                    summary=conv_data.get("summary") or f"Conversation with {saved_person['name'] if saved_person else 'contact'}",
                    topics=conv_data.get("topics", []) or (saved_person.get("topics", []) if saved_person else []),
                    raw_transcript=user_utterance,
                )
                saved_entities["conversation"] = s_conv

            # 5. Follow-up
            fu_data = data.get("follow_up")
            if fu_data and fu_data.get("action"):
                fu_person_name = fu_data.get("person_name")
                fu_person = None
                if fu_person_name:
                    fu_person = self.memory.get_person_by_name(fu_person_name)
                if not fu_person and saved_person:
                    fu_person = saved_person

                if fu_person:
                    # Generate contextual draft message for this follow-up
                    p_topics = fu_person.get("topics", [])
                    p_name = fu_person["name"]
                    p_comp = fu_person.get("company")
                    p_recs = self.memory.list_recommendations(fu_person["id"])

                    topic_mention = f" about {p_topics[0]}" if p_topics else ""
                    rec_mention = f" Your suggestion regarding '{p_recs[0]['content']}' was especially helpful." if p_recs else ""
                    comp_mention = f" on {p_comp}" if p_comp else ""

                    draft_text = (
                        f"Hi {p_name}, great meeting you at the event! I really enjoyed our conversation{topic_mention}."
                        f"{rec_mention} I'd love to stay connected and follow up{comp_mention}."
                    )

                    s_fu = self.memory.create_followup(
                        person_id=fu_person["id"],
                        action=fu_data["action"],
                        context=fu_data.get("context") or "Conversation follow-up",
                        draft_message=draft_text,
                    )
                    saved_entities["follow_up"] = s_fu

            return {
                "has_event_info": True,
                "saved_entities": saved_entities,
                "raw_extracted": data,
            }

        except Exception as e:
            print(f"[ExtractionService] Extraction error: {e}")
            return {"has_event_info": False, "error": str(e)}
