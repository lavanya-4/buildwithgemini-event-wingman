"""Follow-Up Assistant Service for Event Wingman.

Generates contextual, conversation-grounded follow-up messages and manages
the human-in-the-loop approval workflow (Draft, Edit, Regenerate, Approve, Cancel).
Never sends messages automatically.
"""

from typing import Any, Dict, List, Optional
from services.memory_service import MemoryService


class FollowUpService:
    def __init__(self, memory_service: MemoryService, gemini_client=None):
        self.memory = memory_service
        self.gemini = gemini_client

    def draft_followup(
        self,
        person_name_or_id: str,
        custom_instructions: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Draft a contextual follow-up message strictly grounded in conversation memory."""
        person = self.memory.get_person_by_name(person_name_or_id)
        if not person:
            person = self.memory.get_person_by_id(person_name_or_id)

        if not person:
            return {
                "status": "error",
                "message": f"Could not find any contact matching '{person_name_or_id}'.",
            }

        # Retrieve relevant recommendations, topics, and conversations
        recs = self.memory.list_recommendations(person["id"])
        convs = [
            c for c in self.memory.list_conversations()
            if person["id"] in c.get("personIds", [])
        ]

        name = person["name"]
        company = person.get("company")
        topics = person.get("topics", [])

        # Build grounded context
        topic_phrase = f"about {', '.join(topics[:2])}" if topics else ""
        if len(topics) > 2:
            topic_phrase += f" and {topics[2]}"

        rec_phrase = ""
        if recs:
            rec_content = recs[0]["content"]
            rec_phrase = f" Your suggestion regarding '{rec_content}' was especially insightful."

        # Grounded template draft
        if company:
            draft_text = (
                f"Hi {name}, great meeting you at the event! I really enjoyed our conversation "
                f"{topic_phrase}.{rec_phrase} "
                f"I'd love to stay connected and follow up on what you're building at {company}."
            )
        else:
            draft_text = (
                f"Hi {name}, great meeting you at the event! I really enjoyed our conversation "
                f"{topic_phrase}.{rec_phrase} "
                f"I'd love to stay in touch as our projects progress."
            )

        action_summary = f"Connect with {name} regarding {', '.join(topics[:2]) if topics else 'event discussion'}"

        # Persist as draft in follow_ups
        followup = self.memory.create_followup(
            person_id=person["id"],
            action=action_summary,
            context=f"Discussion at event about {', '.join(topics)}",
            draft_message=draft_text,
        )

        return {
            "status": "success",
            "followup": followup,
            "person": person,
            "draftMessage": draft_text,
        }

    def regenerate_followup(
        self,
        followup_id: str,
        tone: str = "friendly_professional",
    ) -> Optional[Dict[str, Any]]:
        """Regenerate a draft follow-up with variation while maintaining grounded facts."""
        followup = self.memory.get_followup_by_id(followup_id)
        if not followup:
            return None

        person = self.memory.get_person_by_id(followup["personId"])
        if not person:
            return None

        name = person["name"]
        company = person.get("company", "your team")
        topics = person.get("topics", [])
        recs = self.memory.list_recommendations(person["id"])

        topics_str = ", ".join(topics) if topics else "innovative AI tech"
        rec_mention = f" I've already made a note to test out your advice on {recs[0]['content']}." if recs else ""

        if tone == "casual":
            new_draft = (
                f"Hey {name}! It was awesome chatting today about {topics_str}.{rec_mention} "
                f"Let's grab a virtual coffee sometime next week to keep the conversation going."
            )
        else:
            new_draft = (
                f"Hi {name}, it was a pleasure connecting with you today. "
                f"Our discussion surrounding {topics_str} was one of the highlights of my event.{rec_mention} "
                f"Looking forward to keeping in touch."
            )

        return self.memory.update_followup(
            followup_id=followup_id,
            status="draft",
            draft_message=new_draft,
        )

    def edit_followup(self, followup_id: str, updated_message: str) -> Optional[Dict[str, Any]]:
        """Edit the draft text before approval."""
        return self.memory.update_followup(
            followup_id=followup_id,
            status="draft",
            draft_message=updated_message,
        )

    def approve_followup(self, followup_id: str) -> Optional[Dict[str, Any]]:
        """Approve follow-up for external action (does not auto-send)."""
        return self.memory.update_followup(
            followup_id=followup_id,
            status="approved",
        )

    def cancel_followup(self, followup_id: str) -> Optional[Dict[str, Any]]:
        """Cancel follow-up."""
        return self.memory.update_followup(
            followup_id=followup_id,
            status="cancelled",
        )
