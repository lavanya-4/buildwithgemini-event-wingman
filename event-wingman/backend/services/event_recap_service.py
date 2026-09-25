"""Event Recap Service for Event Wingman.

Generates comprehensive metrics, top topic summaries, actionable recommendations,
and a concise spoken script for the voice orb.
"""

from typing import Any, Dict, List
from services.memory_service import MemoryService
from services.relationship_service import RelationshipService


class EventRecapService:
    def __init__(self, memory_service: MemoryService, relationship_service: RelationshipService):
        self.memory = memory_service
        self.relationship = relationship_service

    def generate_recap(self) -> Dict[str, Any]:
        """Aggregate event memories into visual metrics and spoken recap."""
        people = self.memory.list_people()
        conversations = self.memory.list_conversations()
        topics = self.memory.list_topics()
        ideas = self.memory.list_ideas()
        recs = self.memory.list_recommendations()
        followups = self.memory.list_followups()

        # Potential connections (clusters of people sharing topics)
        clusters = self.relationship._find_general_clusters(people)

        # Pending follow-ups
        pending_followups = [f for f in followups if f.get("status") in ("draft", "approved")]

        # Top topics by mention count or occurrences
        sorted_topics = sorted(topics, key=lambda t: t.get("mentionCount", 0), reverse=True)

        metrics = {
            "peopleMet": len(people),
            "conversations": len(conversations),
            "topics": len(topics),
            "ideasCaptured": len(ideas),
            "followups": len(followups),
            "potentialConnections": len(clusters),
        }

        # Formulate concise spoken script for voice orb
        spoken_script = self._build_spoken_script(
            people=people,
            metrics=metrics,
            top_topics=sorted_topics[:3],
            pending_followups=pending_followups,
        )

        return {
            "metrics": metrics,
            "topTopics": sorted_topics[:5],
            "recommendations": recs[:5],
            "ideas": ideas[:5],
            "pendingFollowups": pending_followups,
            "potentialConnections": clusters[:3],
            "spokenScript": spoken_script,
        }

    def _build_spoken_script(
        self,
        people: List[Dict[str, Any]],
        metrics: Dict[str, int],
        top_topics: List[Dict[str, Any]],
        pending_followups: List[Dict[str, Any]],
    ) -> str:
        if not people:
            return "You haven't logged any conversations yet. Start by telling me who you meet!"

        topic_str = ", ".join(t["name"] for t in top_topics) if top_topics else "innovative AI technology"
        names_str = ", ".join(p["name"] for p in people[:3])
        if len(people) > 3:
            names_str += f", and {len(people) - 3} others"

        script = (
            f"Here is your event recap: You've met {metrics['peopleMet']} people including {names_str}. "
            f"Your most discussed topics were {topic_str}. "
            f"You captured {metrics['ideasCaptured']} ideas and have {len(pending_followups)} follow-ups pending."
        )
        return script
