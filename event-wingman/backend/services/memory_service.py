"""Structured Event Memory Service for Event Wingman.

Provides CRUD, deduplication, search, and relationship graph management.
"""

import json
import re
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from database import get_db, init_db


class MemoryService:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path
        if db_path:
            init_db(db_path)
        else:
            init_db()

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    # -------------------------------------------------------------
    # People Management & Deduplication
    # -------------------------------------------------------------
    def save_person(
        self,
        name: str,
        company: Optional[str] = None,
        role: Optional[str] = None,
        topics: Optional[List[str]] = None,
        notes: Optional[List[str]] = None,
        is_demo: bool = False,
    ) -> Dict[str, Any]:
        """Save a person with automatic deduplication by name."""
        name_clean = name.strip()
        existing = self.get_person_by_name(name_clean)

        now = self._now_iso()
        topics = topics or []
        notes = notes or []

        with get_db(self.db_path) as conn:
            cursor = conn.cursor()

            if existing:
                # Deduplication: Update existing person record
                existing_topics = set(existing.get("topics", []))
                for t in topics:
                    existing_topics.add(t.strip())

                existing_notes = list(existing.get("notes", []))
                for n in notes:
                    if n.strip() and n.strip() not in existing_notes:
                        existing_notes.append(n.strip())

                updated_company = company.strip() if company else existing.get("company")
                updated_role = role.strip() if role else existing.get("role")

                cursor.execute(
                    """
                    UPDATE people
                    SET company = ?, role = ?, topics = ?, notes = ?, last_interaction_at = ?
                    WHERE id = ?
                    """,
                    (
                        updated_company,
                        updated_role,
                        json.dumps(list(existing_topics)),
                        json.dumps(existing_notes),
                        now,
                        existing["id"],
                    ),
                )
                person_id = existing["id"]
            else:
                person_id = f"person_{uuid.uuid4().hex[:8]}"
                cursor.execute(
                    """
                    INSERT INTO people (id, name, company, role, topics, notes, first_met_at, last_interaction_at, is_demo)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        person_id,
                        name_clean,
                        company.strip() if company else None,
                        role.strip() if role else None,
                        json.dumps([t.strip() for t in topics if t.strip()]),
                        json.dumps([n.strip() for n in notes if n.strip()]),
                        now,
                        now,
                        1 if is_demo else 0,
                    ),
                )

                # Add User -> MET -> Person relationship
                self._add_relationship(
                    cursor,
                    source_id="user_me",
                    source_type="User",
                    target_id=person_id,
                    target_type="Person",
                    relation_type="MET",
                    context=f"Met {name_clean} at event",
                )

            # Ensure Company and Person -> WORKS_AT -> Company
            final_company = company.strip() if company else (existing.get("company") if existing else None)
            if final_company:
                comp_id = f"comp_{final_company.lower().replace(' ', '_')}"
                cursor.execute(
                    "INSERT OR IGNORE INTO companies (id, name) VALUES (?, ?)",
                    (comp_id, final_company),
                )
                self._add_relationship(
                    cursor,
                    source_id=person_id,
                    source_type="Person",
                    target_id=comp_id,
                    target_type="Company",
                    relation_type="WORKS_AT",
                    context=f"{name_clean} works at {final_company}",
                )

            # Ensure Topics and Person -> INTERESTED_IN -> Topic
            final_topics = topics if not existing else list(existing_topics)
            for topic in final_topics:
                t_clean = topic.strip()
                if not t_clean:
                    continue
                t_id = f"topic_{t_clean.lower().replace(' ', '_')}"
                cursor.execute(
                    """
                    INSERT INTO topics (id, name, mention_count)
                    VALUES (?, ?, 1)
                    ON CONFLICT(id) DO UPDATE SET mention_count = mention_count + 1
                    """,
                    (t_id, t_clean),
                )
                self._add_relationship(
                    cursor,
                    source_id=person_id,
                    source_type="Person",
                    target_id=t_id,
                    target_type="Topic",
                    relation_type="INTERESTED_IN",
                    context=f"{name_clean} interested in {t_clean}",
                )

        return self.get_person_by_id(person_id)

    def get_person_by_id(self, person_id: str) -> Optional[Dict[str, Any]]:
        with get_db(self.db_path) as conn:
            row = conn.execute("SELECT * FROM people WHERE id = ?", (person_id,)).fetchone()
            if not row:
                return None
            return self._row_to_person(row)

    def get_person_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        with get_db(self.db_path) as conn:
            # Case-insensitive search
            row = conn.execute(
                "SELECT * FROM people WHERE LOWER(name) = LOWER(?)", (name.strip(),)
            ).fetchone()
            if not row:
                # Substring match if full match fails
                row = conn.execute(
                    "SELECT * FROM people WHERE LOWER(name) LIKE LOWER(?) LIMIT 1",
                    (f"%{name.strip()}%",),
                ).fetchone()
            if not row:
                return None
            return self._row_to_person(row)

    def list_people(self, is_demo: Optional[bool] = None) -> List[Dict[str, Any]]:
        with get_db(self.db_path) as conn:
            if is_demo is None:
                rows = conn.execute("SELECT * FROM people ORDER BY last_interaction_at DESC").fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM people WHERE is_demo = ? ORDER BY last_interaction_at DESC",
                    (1 if is_demo else 0,),
                ).fetchall()
            people = [self._row_to_person(r) for r in rows]
            for p in people:
                recs = conn.execute(
                    "SELECT content FROM recommendations WHERE recommended_by_person_id = ? ORDER BY created_at DESC",
                    (p["id"],),
                ).fetchall()
                p["recommendations"] = [r["content"] for r in recs]
            return people

    def _row_to_person(self, row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "id": row["id"],
            "name": row["name"],
            "company": row["company"],
            "role": row["role"],
            "topics": json.loads(row["topics"] or "[]"),
            "notes": json.loads(row["notes"] or "[]"),
            "firstMetAt": row["first_met_at"],
            "lastInteractionAt": row["last_interaction_at"],
            "isDemo": bool(row["is_demo"]),
        }

    # -------------------------------------------------------------
    # Conversations
    # -------------------------------------------------------------
    def save_conversation(
        self,
        person_ids: List[str],
        summary: str,
        topics: Optional[List[str]] = None,
        recommendations: Optional[List[str]] = None,
        ideas: Optional[List[str]] = None,
        raw_transcript: Optional[str] = None,
        is_demo: bool = False,
    ) -> Dict[str, Any]:
        cid = f"conv_{uuid.uuid4().hex[:8]}"
        now = self._now_iso()
        topics = topics or []
        recs = recommendations or []
        ide = ideas or []

        with get_db(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO conversations (id, person_ids, timestamp, summary, topics, recommendations, ideas, raw_transcript, is_demo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    cid,
                    json.dumps(person_ids),
                    now,
                    summary,
                    json.dumps(topics),
                    json.dumps(recs),
                    json.dumps(ide),
                    raw_transcript,
                    1 if is_demo else 0,
                ),
            )

            # Link Conversation -> DISCUSSED -> Topic
            for t in topics:
                t_clean = t.strip()
                if not t_clean:
                    continue
                t_id = f"topic_{t_clean.lower().replace(' ', '_')}"
                self._add_relationship(
                    cursor,
                    source_id=cid,
                    source_type="Conversation",
                    target_id=t_id,
                    target_type="Topic",
                    relation_type="DISCUSSED",
                    context=f"Discussed {t_clean} in conversation",
                )

        return self.get_conversation_by_id(cid)

    def get_conversation_by_id(self, cid: str) -> Optional[Dict[str, Any]]:
        with get_db(self.db_path) as conn:
            row = conn.execute("SELECT * FROM conversations WHERE id = ?", (cid,)).fetchone()
            if not row:
                return None
            return {
                "id": row["id"],
                "personIds": json.loads(row["person_ids"] or "[]"),
                "timestamp": row["timestamp"],
                "summary": row["summary"],
                "topics": json.loads(row["topics"] or "[]"),
                "recommendations": json.loads(row["recommendations"] or "[]"),
                "ideas": json.loads(row["ideas"] or "[]"),
                "rawTranscript": row["raw_transcript"],
                "isDemo": bool(row["is_demo"]),
            }

    def list_conversations(self) -> List[Dict[str, Any]]:
        with get_db(self.db_path) as conn:
            rows = conn.execute("SELECT * FROM conversations ORDER BY timestamp DESC").fetchall()
            return [
                {
                    "id": r["id"],
                    "personIds": json.loads(r["person_ids"] or "[]"),
                    "timestamp": r["timestamp"],
                    "summary": r["summary"],
                    "topics": json.loads(r["topics"] or "[]"),
                    "recommendations": json.loads(r["recommendations"] or "[]"),
                    "ideas": json.loads(r["ideas"] or "[]"),
                    "rawTranscript": r["raw_transcript"],
                    "isDemo": bool(r["is_demo"]),
                }
                for r in rows
            ]

    # -------------------------------------------------------------
    # Recommendations & Ideas
    # -------------------------------------------------------------
    def save_recommendation(
        self,
        content: str,
        recommended_by_person_id: Optional[str] = None,
        context: Optional[str] = None,
        is_demo: bool = False,
    ) -> Dict[str, Any]:
        rec_id = f"rec_{uuid.uuid4().hex[:8]}"
        now = self._now_iso()

        with get_db(self.db_path) as conn:
            cursor = conn.cursor()
            # Deduplication
            if recommended_by_person_id:
                existing_rec = cursor.execute(
                    "SELECT * FROM recommendations WHERE LOWER(content) = LOWER(?) AND recommended_by_person_id = ?",
                    (content.strip(), recommended_by_person_id),
                ).fetchone()
                if existing_rec:
                    return {
                        "id": existing_rec["id"],
                        "content": existing_rec["content"],
                        "recommendedByPersonId": existing_rec["recommended_by_person_id"],
                        "context": existing_rec["context"],
                        "createdAt": existing_rec["created_at"],
                        "isDemo": bool(existing_rec["is_demo"]),
                    }

            cursor.execute(
                """
                INSERT INTO recommendations (id, content, recommended_by_person_id, context, created_at, is_demo)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (rec_id, content.strip(), recommended_by_person_id, context, now, 1 if is_demo else 0),
            )

            if recommended_by_person_id:
                self._add_relationship(
                    cursor,
                    source_id=recommended_by_person_id,
                    source_type="Person",
                    target_id=rec_id,
                    target_type="Recommendation",
                    relation_type="RECOMMENDED",
                    context=content.strip(),
                )

        return {
            "id": rec_id,
            "content": content.strip(),
            "recommendedByPersonId": recommended_by_person_id,
            "context": context,
            "createdAt": now,
            "isDemo": is_demo,
        }

    def list_recommendations(self, person_id: Optional[str] = None) -> List[Dict[str, Any]]:
        with get_db(self.db_path) as conn:
            if person_id:
                rows = conn.execute(
                    "SELECT * FROM recommendations WHERE recommended_by_person_id = ? ORDER BY created_at DESC",
                    (person_id,),
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM recommendations ORDER BY created_at DESC").fetchall()
            return [
                {
                    "id": r["id"],
                    "content": r["content"],
                    "recommendedByPersonId": r["recommended_by_person_id"],
                    "context": r["context"],
                    "createdAt": r["created_at"],
                    "isDemo": bool(r["is_demo"]),
                }
                for r in rows
            ]

    def save_idea(
        self,
        title: str,
        description: Optional[str] = None,
        source_person_id: Optional[str] = None,
        is_demo: bool = False,
    ) -> Dict[str, Any]:
        idea_id = f"idea_{uuid.uuid4().hex[:8]}"
        now = self._now_iso()

        with get_db(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO ideas (id, title, description, source_person_id, created_at, is_demo)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (idea_id, title.strip(), description, source_person_id, now, 1 if is_demo else 0),
            )

            if source_person_id:
                self._add_relationship(
                    cursor,
                    source_id=source_person_id,
                    source_type="Person",
                    target_id=idea_id,
                    target_type="Idea",
                    relation_type="RECOMMENDED",
                    context=title.strip(),
                )

        return {
            "id": idea_id,
            "title": title.strip(),
            "description": description,
            "sourcePersonId": source_person_id,
            "createdAt": now,
            "isDemo": is_demo,
        }

    def list_ideas(self) -> List[Dict[str, Any]]:
        with get_db(self.db_path) as conn:
            rows = conn.execute("SELECT * FROM ideas ORDER BY created_at DESC").fetchall()
            return [
                {
                    "id": r["id"],
                    "title": r["title"],
                    "description": r["description"],
                    "sourcePersonId": r["source_person_id"],
                    "createdAt": r["created_at"],
                    "isDemo": bool(r["is_demo"]),
                }
                for r in rows
            ]

    # -------------------------------------------------------------
    # Follow-Ups
    # -------------------------------------------------------------
    def create_followup(
        self,
        person_id: str,
        action: str,
        context: Optional[str] = None,
        draft_message: Optional[str] = None,
        is_demo: bool = False,
    ) -> Dict[str, Any]:
        f_id = f"followup_{uuid.uuid4().hex[:8]}"
        now = self._now_iso()

        with get_db(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO follow_ups (id, person_id, action, context, status, draft_message, created_at, is_demo)
                VALUES (?, ?, ?, ?, 'draft', ?, ?, ?)
                """,
                (f_id, person_id, action.strip(), context, draft_message, now, 1 if is_demo else 0),
            )

            self._add_relationship(
                cursor,
                source_id="user_me",
                source_type="User",
                target_id=person_id,
                target_type="Person",
                relation_type="FOLLOW_UP_WITH",
                context=action.strip(),
            )

        return self.get_followup_by_id(f_id)

    def update_followup(
        self,
        followup_id: str,
        status: Optional[str] = None,
        draft_message: Optional[str] = None,
        action: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        with get_db(self.db_path) as conn:
            cursor = conn.cursor()
            current = self.get_followup_by_id(followup_id)
            if not current:
                return None

            new_status = status if status is not None else current["status"]
            new_draft = draft_message if draft_message is not None else current.get("draftMessage")
            new_action = action if action is not None else current.get("action")

            cursor.execute(
                """
                UPDATE follow_ups
                SET status = ?, draft_message = ?, action = ?
                WHERE id = ?
                """,
                (new_status, new_draft, new_action, followup_id),
            )

        return self.get_followup_by_id(followup_id)

    def get_followup_by_id(self, fid: str) -> Optional[Dict[str, Any]]:
        with get_db(self.db_path) as conn:
            row = conn.execute("SELECT * FROM follow_ups WHERE id = ?", (fid,)).fetchone()
            if not row:
                return None
            return {
                "id": row["id"],
                "personId": row["person_id"],
                "action": row["action"],
                "context": row["context"],
                "status": row["status"],
                "draftMessage": row["draft_message"],
                "createdAt": row["created_at"],
                "isDemo": bool(row["is_demo"]),
            }

    def list_followups(self, person_id: Optional[str] = None) -> List[Dict[str, Any]]:
        with get_db(self.db_path) as conn:
            if person_id:
                rows = conn.execute(
                    "SELECT * FROM follow_ups WHERE person_id = ? ORDER BY created_at DESC",
                    (person_id,),
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM follow_ups ORDER BY created_at DESC").fetchall()

            # Enrich with person name
            results = []
            for r in rows:
                p = self.get_person_by_id(r["person_id"])
                results.append({
                    "id": r["id"],
                    "personId": r["person_id"],
                    "personName": p["name"] if p else "Unknown",
                    "personCompany": p["company"] if p else None,
                    "action": r["action"],
                    "context": r["context"],
                    "status": r["status"],
                    "draftMessage": r["draft_message"],
                    "createdAt": r["created_at"],
                    "isDemo": bool(r["is_demo"]),
                })
            return results

    # -------------------------------------------------------------
    # Topics
    # -------------------------------------------------------------
    def list_topics(self) -> List[Dict[str, Any]]:
        with get_db(self.db_path) as conn:
            rows = conn.execute("SELECT * FROM topics ORDER BY mention_count DESC").fetchall()
            return [{"id": r["id"], "name": r["name"], "mentionCount": r["mention_count"]} for r in rows]

    # -------------------------------------------------------------
    # Relationships
    # -------------------------------------------------------------
    def _add_relationship(
        self,
        cursor: sqlite3.Cursor,
        source_id: str,
        source_type: str,
        target_id: str,
        target_type: str,
        relation_type: str,
        context: Optional[str] = None,
    ) -> None:
        rel_id = f"rel_{source_id}_{relation_type}_{target_id}"
        now = self._now_iso()
        cursor.execute(
            """
            INSERT OR REPLACE INTO relationships (id, source_id, source_type, target_id, target_type, relation_type, context, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (rel_id, source_id, source_type, target_id, target_type, relation_type, context, now),
        )

    def list_relationships(self) -> List[Dict[str, Any]]:
        with get_db(self.db_path) as conn:
            rows = conn.execute("SELECT * FROM relationships ORDER BY created_at ASC").fetchall()
            return [
                {
                    "id": r["id"],
                    "sourceId": r["source_id"],
                    "sourceType": r["source_type"],
                    "targetId": r["target_id"],
                    "targetType": r["target_type"],
                    "relationType": r["relation_type"],
                    "context": r["context"],
                    "createdAt": r["created_at"],
                }
                for r in rows
            ]

    # -------------------------------------------------------------
    # Search & Semantic Recall Queries
    # -------------------------------------------------------------
    def search_memory(self, query: str) -> Dict[str, Any]:
        """Comprehensive search across people, topics, conversations, ideas, and recommendations."""
        stop_words = {
            "who", "did", "i", "meet", "from", "at", "the", "what", "about",
            "recommend", "recommended", "talk", "to", "people", "person", "is",
            "a", "an", "and", "or", "my", "any", "anyone"
        }
        words = [w for w in re.findall(r'\b\w+\b', query.lower()) if len(w) > 1 and w not in stop_words]
        terms = [query.strip().lower()]
        for w in words:
            if w not in terms:
                terms.append(w)

        people_dict = {}
        rec_dict = {}
        idea_dict = {}
        conv_dict = {}
        followup_dict = {}

        with get_db(self.db_path) as conn:
            for term in terms:
                q = f"%{term}%"
                # Match people by name, company, role, topics, notes
                p_rows = conn.execute(
                    """
                    SELECT * FROM people
                    WHERE LOWER(name) LIKE ?
                       OR LOWER(COALESCE(company, '')) LIKE ?
                       OR LOWER(COALESCE(role, '')) LIKE ?
                       OR LOWER(topics) LIKE ?
                       OR LOWER(notes) LIKE ?
                    """,
                    (q, q, q, q, q),
                ).fetchall()
                for r in p_rows:
                    people_dict[r["id"]] = r

                # Match recommendations
                r_rows = conn.execute(
                    """
                    SELECT * FROM recommendations
                    WHERE LOWER(content) LIKE ? OR LOWER(COALESCE(context, '')) LIKE ?
                    """,
                    (q, q),
                ).fetchall()
                for r in r_rows:
                    rec_dict[r["id"]] = r

                # Match ideas
                i_rows = conn.execute(
                    """
                    SELECT * FROM ideas
                    WHERE LOWER(title) LIKE ? OR LOWER(COALESCE(description, '')) LIKE ?
                    """,
                    (q, q),
                ).fetchall()
                for r in i_rows:
                    idea_dict[r["id"]] = r

                # Match conversations
                c_rows = conn.execute(
                    """
                    SELECT * FROM conversations
                    WHERE LOWER(summary) LIKE ? OR LOWER(topics) LIKE ? OR LOWER(COALESCE(raw_transcript, '')) LIKE ?
                    """,
                    (q, q, q),
                ).fetchall()
                for r in c_rows:
                    conv_dict[r["id"]] = r

                # Match followups
                f_rows = conn.execute(
                    """
                    SELECT * FROM follow_ups
                    WHERE LOWER(action) LIKE ? OR LOWER(COALESCE(context, '')) LIKE ? OR LOWER(COALESCE(draft_message, '')) LIKE ?
                    """,
                    (q, q, q),
                ).fetchall()
                for r in f_rows:
                    followup_dict[r["id"]] = r

        people = [self._row_to_person(r) for r in people_dict.values()]
        for p in people:
            p["recommendations"] = self.list_recommendations(p["id"])
            p["followups"] = self.list_followups(p["id"])

        return {
            "query": query,
            "people": people,
            "recommendations": [
                {
                    "id": r["id"],
                    "content": r["content"],
                    "recommendedByPersonId": r["recommended_by_person_id"],
                    "context": r["context"],
                }
                for r in rec_dict.values()
            ],
            "ideas": [
                {"id": r["id"], "title": r["title"], "description": r["description"]}
                for r in idea_dict.values()
            ],
            "conversations": [
                {"id": r["id"], "summary": r["summary"], "topics": json.loads(r["topics"] or "[]")}
                for r in conv_dict.values()
            ],
            "followups": [
                {"id": r["id"], "personId": r["person_id"], "action": r["action"], "status": r["status"]}
                for r in followup_dict.values()
            ],
        }

    def find_people_by_topic(self, topic_query: str) -> List[Dict[str, Any]]:
        """Find people associated with a specific topic or keyword."""
        q = f"%{topic_query.strip().lower()}%"
        with get_db(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT * FROM people
                WHERE LOWER(topics) LIKE ?
                   OR LOWER(COALESCE(role, '')) LIKE ?
                   OR LOWER(notes) LIKE ?
                """,
                (q, q, q),
            ).fetchall()
            people = [self._row_to_person(r) for r in rows]
            for p in people:
                p["recommendations"] = self.list_recommendations(p["id"])
            return people

    # -------------------------------------------------------------
    # Demo Mode Seeder & Purger
    # -------------------------------------------------------------
    def seed_demo_data(self) -> Dict[str, Any]:
        """Seed realistic synthetic conference contacts and discussions."""
        self.clear_demo_data()

        # Contact 1: Sarah
        p_sarah = self.save_person(
            name="Sarah",
            company="Acme AI",
            role="Lead Voice AI Engineer",
            topics=["Voice Agents", "Healthcare AI", "Gemini Live", "Interruption Handling"],
            notes=["Passionate about real-time clinician assistance and low-latency voice UX."],
            is_demo=True,
        )
        self.save_recommendation(
            content="Explore interruption handling with Gemini Live",
            recommended_by_person_id=p_sarah["id"],
            context="Crucial for clinical voice workflows where doctors interrupt the assistant.",
            is_demo=True,
        )
        self.save_conversation(
            person_ids=[p_sarah["id"]],
            summary="Discussed Gemini Live, healthcare voice agents, and handling user barge-in effectively.",
            topics=["Voice Agents", "Healthcare AI", "Gemini Live"],
            recommendations=["Explore interruption handling with Gemini Live"],
            ideas=["Real-time doctor note transcription with interruption safeguards"],
            is_demo=True,
        )
        self.create_followup(
            person_id=p_sarah["id"],
            action="Connect after the event regarding interruption handling and voice benchmarks",
            context="Build with Gemini Track 3 conference",
            draft_message=(
                "Hi Sarah, great meeting you at Build with Gemini! I really enjoyed our chat about "
                "healthcare voice agents and Gemini Live. Your suggestion around interruption handling was "
                "super insightful. Would love to stay connected and compare notes as our prototypes progress."
            ),
            is_demo=True,
        )

        # Contact 2: Priya
        p_priya = self.save_person(
            name="Priya",
            company="Google",
            role="Research Engineer",
            topics=["Multimodal Agents", "Persistent Memory", "Voice Agents"],
            notes=["Working on long-term memory architectures and cross-session memory banks."],
            is_demo=True,
        )
        self.save_recommendation(
            content="Look into persistent memory banks for multi-session agent recall",
            recommended_by_person_id=p_priya["id"],
            context="Prevents the agent from losing context across days of an event.",
            is_demo=True,
        )
        self.save_conversation(
            person_ids=[p_priya["id"]],
            summary="Explored persistent agent memory and grounding voice interactions in past sessions.",
            topics=["Multimodal Agents", "Persistent Memory", "Voice Agents"],
            recommendations=["Look into persistent memory banks for multi-session agent recall"],
            ideas=["Cross-session memory synthesis using Vertex AI Memory Bank"],
            is_demo=True,
        )

        # Contact 3: Daniel
        p_daniel = self.save_person(
            name="Daniel",
            company="Startup X",
            role="Founder & CTO",
            topics=["Agent Infrastructure", "Evaluation Benchmarks", "Voice Agents"],
            notes=["Building observability pipelines for real-time AI agents."],
            is_demo=True,
        )
        self.save_idea(
            title="Automated latency eval for live voice agents",
            description="Benchmark end-to-end audio roundtrip latency across providers.",
            source_person_id=p_daniel["id"],
            is_demo=True,
        )
        self.save_conversation(
            person_ids=[p_daniel["id"]],
            summary="Talked about latency benchmarks and agent deployment architectures.",
            topics=["Agent Infrastructure", "Evaluation Benchmarks", "Voice Agents"],
            ideas=["Automated latency eval for live voice agents"],
            is_demo=True,
        )

        return {
            "status": "success",
            "message": "Seeded synthetic contacts: Sarah, Priya, Daniel",
            "peopleCount": 3,
        }

    def clear_demo_data(self) -> None:
        """Remove only synthetic demo data."""
        with get_db(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM people WHERE is_demo = 1")
            cursor.execute("DELETE FROM conversations WHERE is_demo = 1")
            cursor.execute("DELETE FROM recommendations WHERE is_demo = 1")
            cursor.execute("DELETE FROM ideas WHERE is_demo = 1")
            cursor.execute("DELETE FROM follow_ups WHERE is_demo = 1")
            # Clean orphaned relationships
            cursor.execute(
                """
                DELETE FROM relationships
                WHERE source_id NOT IN (SELECT id FROM people)
                  AND source_id != 'user_me'
                  AND source_id NOT IN (SELECT id FROM conversations)
                """
            )

    def clear_all_data(self) -> None:
        """Purge all event data for privacy / fresh start."""
        with get_db(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM people")
            cursor.execute("DELETE FROM companies")
            cursor.execute("DELETE FROM topics")
            cursor.execute("DELETE FROM conversations")
            cursor.execute("DELETE FROM recommendations")
            cursor.execute("DELETE FROM ideas")
            cursor.execute("DELETE FROM follow_ups")
            cursor.execute("DELETE FROM relationships")

    def delete_person(self, person_id: str) -> bool:
        """Delete a person and associated relationships/followups."""
        with get_db(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM people WHERE id = ?", (person_id,))
            cursor.execute("DELETE FROM follow_ups WHERE person_id = ?", (person_id,))
            cursor.execute("DELETE FROM recommendations WHERE recommended_by_person_id = ?", (person_id,))
            cursor.execute("DELETE FROM ideas WHERE source_person_id = ?", (person_id,))
            cursor.execute("DELETE FROM relationships WHERE source_id = ? OR target_id = ?", (person_id, person_id))
            return cursor.rowcount > 0
