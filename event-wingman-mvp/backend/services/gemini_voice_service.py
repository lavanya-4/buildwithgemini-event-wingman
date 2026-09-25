"""Gemini Voice Service for Event Wingman.

Provides natural voice conversational reasoning, native function calling / tool execution,
semantic recall grounded strictly in stored memories, and networking intelligence.
"""

import json
import os
from typing import Any, Callable, Dict, List, Optional
from google import genai
from google.genai import types

from services.event_recap_service import EventRecapService
from services.extraction_service import MemoryExtractionService
from services.followup_service import FollowUpService
from services.memory_service import MemoryService
from services.relationship_service import RelationshipService

SYSTEM_INSTRUCTION = """
You are Event Wingman, a real-time AI voice copilot and event memory assistant.
You have NO internal memory of who the user met; all memories are stored in the database.

Core Behavior:
1. Voice-first response: Keep answers natural, conversational, warm, and concise (1-2 sentences). Speak directly to the user.
2. Memory Saving: When the user tells you about someone they met (e.g., "I met Sarah from Google. She works on voice AI and recommended Gemini Live"), confirm what was saved concisely: Name, Company, Topics discussed, and Recommendations.
3. Grounded Recall: Whenever the user asks ANY question about someone they met, companies, topics, or recommendations (e.g., "Who did I meet from Google?", "What did Sarah recommend?", "Who did I talk to about voice AI?"), you MUST call search_memory to retrieve the facts before answering. Answer directly, accurately, and concisely using the retrieved data. Never say you don't know without searching memory first.
"""


class GeminiVoiceService:
    def __init__(
        self,
        memory_service: MemoryService,
        relationship_service: RelationshipService,
        followup_service: FollowUpService,
        recap_service: EventRecapService,
        extraction_service: MemoryExtractionService,
    ):
        self.memory = memory_service
        self.relationship = relationship_service
        self.followup = followup_service
        self.recap = recap_service
        self.extraction = extraction_service

        self.model_name = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
        self.client = None
        self._init_client()
        self.chat_session = None
        self._init_chat()

    def _init_client(self):
        project = os.environ.get("GOOGLE_CLOUD_PROJECT", "qwiklabs-gcp-01-9c5a198b6a9e")
        location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
        use_vertex = os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "true").lower() in ("true", "1")
        api_key = os.environ.get("GEMINI_API_KEY")

        if api_key:
            self.client = genai.Client(api_key=api_key)
        else:
            self.client = genai.Client(vertexai=use_vertex, project=project, location=location)

    def _get_tools(self) -> List[Callable]:
        """Define tool functions directly bound to service methods."""
        memory = self.memory
        relationship = self.relationship
        followup = self.followup
        recap = self.recap

        def save_person(
            name: str,
            company: str = "",
            role: str = "",
            topics: list[str] = [],
            notes: list[str] = [],
        ) -> str:
            """Save or update a person met at the event with company, role, topics, and notes."""
            res = memory.save_person(name=name, company=company, role=role, topics=topics, notes=notes)
            return json.dumps({"status": "success", "person": res})

        def update_person(
            name: str,
            company: str = "",
            role: str = "",
            add_topics: list[str] = [],
            add_notes: list[str] = [],
        ) -> str:
            """Update an existing person's details, adding topics or notes."""
            res = memory.save_person(
                name=name,
                company=company or None,
                role=role or None,
                topics=add_topics,
                notes=add_notes,
            )
            return json.dumps({"status": "success", "updated_person": res})

        def save_recommendation(
            content: str,
            recommended_by: str = "",
            context: str = "",
        ) -> str:
            """Save a recommendation or advice given by someone at the event."""
            person_id = None
            if recommended_by:
                p = memory.get_person_by_name(recommended_by)
                if p:
                    person_id = p["id"]
            res = memory.save_recommendation(
                content=content, recommended_by_person_id=person_id, context=context
            )
            return json.dumps({"status": "success", "recommendation": res})

        def save_idea(
            title: str,
            description: str = "",
            source_person_name: str = "",
        ) -> str:
            """Save an interesting project or startup idea heard at the event."""
            person_id = None
            if source_person_name:
                p = memory.get_person_by_name(source_person_name)
                if p:
                    person_id = p["id"]
            res = memory.save_idea(title=title, description=description, source_person_id=person_id)
            return json.dumps({"status": "success", "idea": res})

        def create_followup(
            person_name: str,
            action: str,
            context: str = "",
        ) -> str:
            """Create a follow-up action promise for a contact."""
            p = memory.get_person_by_name(person_name)
            if not p:
                return json.dumps({"status": "error", "message": f"Person '{person_name}' not found."})
            res = followup.draft_followup(person_name_or_id=p["id"])
            return json.dumps({"status": "success", "followup": res})

        def draft_followup(
            person_name: str,
            custom_context: str = "",
        ) -> str:
            """Draft a contextual follow-up message to a person from past conversation and recommendations."""
            p = memory.get_person_by_name(person_name)
            if not p:
                return json.dumps({"status": "error", "message": f"Person '{person_name}' not found."})
            res = followup.draft_followup(person_name_or_id=p["id"], custom_instructions=custom_context)
            return json.dumps({"status": "success", "followup": res, "draft_message": res.get("draftMessage")})

        def search_memory(query: str) -> str:
            """Search stored event memories for people, topics, companies, ideas, or recommendations."""
            results = memory.search_memory(query)
            return json.dumps(results)

        def get_person(name: str) -> str:
            """Retrieve detailed information and history about a person met at the event."""
            p = memory.get_person_by_name(name)
            if not p:
                return json.dumps({"status": "not_found", "message": f"No record for '{name}'."})
            p["recommendations"] = memory.list_recommendations(p["id"])
            p["followups"] = memory.list_followups(p["id"])
            return json.dumps(p)

        def find_people_by_topic(topic: str) -> str:
            """Find all people interested in or working on a given topic."""
            people = memory.find_people_by_topic(topic)
            return json.dumps({"topic": topic, "count": len(people), "people": people})

        def find_related_people(person_name: str) -> str:
            """Find people with shared interests to a given contact, with explainable 'Why?' reasons."""
            res = relationship.find_related_people(person_name)
            return json.dumps(res)

        def get_followups(person_name: str = "") -> str:
            """List pending follow-ups, optionally filtered by person name."""
            pid = None
            if person_name:
                p = memory.get_person_by_name(person_name)
                if p:
                    pid = p["id"]
            fu = memory.list_followups(pid)
            return json.dumps({"followups": fu})

        def generate_event_recap() -> str:
            """Generate complete recap metrics and spoken summary for the event."""
            rec = recap.generate_recap()
            return json.dumps(rec)

        return [
            save_person,
            update_person,
            save_recommendation,
            search_memory,
            get_person,
            find_people_by_topic,
        ]

    def _init_chat(self):
        """Initialize or reset Gemini chat session with tools."""
        if not self.client:
            return
        tools = self._get_tools()
        self.chat_session = self.client.chats.create(
            model=self.model_name,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                tools=tools,
                temperature=0.2,
            ),
        )

    def process_user_message(self, user_text: str) -> Dict[str, Any]:
        """Process natural user speech/text, execute tools, extract memory, and return response."""
        user_clean = user_text.strip()
        if not user_clean:
            return {"response_text": "I didn't catch that. Could you repeat?", "tool_calls": []}

        # 1. Background extraction pass: Guarantee multi-entity meeting notes are persisted
        extraction_result = {}
        try:
            extraction_result = self.extraction.extract_and_persist(user_clean)
        except Exception as e:
            print(f"[GeminiVoiceService] Extraction pass error: {e}")

        # 2. Conversational reasoning & tool execution via Gemini Chat
        tool_calls_executed = []
        response_text = ""

        try:
            if not self.chat_session:
                self._init_chat()

            response = self.chat_session.send_message(user_clean)
            response_text = response.text.strip() if response.text else ""

            # Check if tools were executed in this turn
            if hasattr(response, "function_calls") and response.function_calls:
                for fc in response.function_calls:
                    tool_calls_executed.append({
                        "name": fc.name,
                        "args": dict(fc.args) if hasattr(fc, "args") else {},
                    })

        except Exception as e:
            print(f"[GeminiVoiceService] Gemini chat error: {e}")
            # If chat session failed or rate limited, generate fallback response from extraction
            if extraction_result.get("has_event_info"):
                p = extraction_result.get("saved_entities", {}).get("person")
                if p:
                    response_text = f"Got it! I've noted down your meeting with {p['name']} from {p.get('company', 'their team')}."
                else:
                    response_text = "I've captured that in your event memory."
            else:
                # Direct memory search fallback
                search_res = self.memory.search_memory(user_clean)
                if search_res.get("people"):
                    p0 = search_res["people"][0]
                    response_text = f"You talked with {p0['name']} from {p0.get('company', 'their team')} about {', '.join(p0.get('topics', []))}."
                else:
                    response_text = "I checked your event notes, but didn't find a matching record yet."

        return {
            "response_text": response_text,
            "tool_calls": tool_calls_executed,
            "extracted": extraction_result,
        }

    def reset_chat(self):
        """Reset conversation session."""
        self._init_chat()
