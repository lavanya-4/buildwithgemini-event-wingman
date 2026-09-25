"""Memory storage and retrieval for Event Wingman."""

import json
import os
import re
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

DB_PATH = os.environ.get("EVENT_WINGMAN_DB", "/tmp/event_wingman.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS people (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL COLLATE NOCASE,
                company TEXT,
                role TEXT,
                topics TEXT DEFAULT '[]',
                recommendations TEXT DEFAULT '[]',
                created_at TEXT
            )
        """)
        conn.commit()


init_db()


def save_person(name: str, company: str = "", role: str = "", topics: Optional[List[str]] = None) -> str:
    """Save or update information about a person met at an event.

    Args:
        name: The person's name (e.g. 'Sarah').
        company: The company or organization they work for (e.g. 'Google').
        role: Their job role or domain (e.g. 'Voice AI engineer').
        topics: List of topics, technologies, or subjects discussed (e.g. ['voice AI', 'Gemini Live']).

    Returns:
        A JSON string confirming the person was saved.
    """
    topics_list = topics or []
    with get_db() as conn:
        row = conn.execute("SELECT * FROM people WHERE LOWER(name) = ?", (name.strip().lower(),)).fetchone()
        now = datetime.now(timezone.utc).isoformat()
        if row:
            existing_topics = json.loads(row["topics"] or "[]")
            for t in topics_list:
                if t.lower() not in [x.lower() for x in existing_topics]:
                    existing_topics.append(t)
            new_company = company if company else row["company"]
            new_role = role if role else row["role"]
            conn.execute(
                "UPDATE people SET company = ?, role = ?, topics = ? WHERE id = ?",
                (new_company, new_role, json.dumps(existing_topics), row["id"]),
            )
            pid = row["id"]
        else:
            pid = f"person_{uuid.uuid4().hex[:8]}"
            conn.execute(
                "INSERT INTO people (id, name, company, role, topics, recommendations, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (pid, name.strip(), company.strip(), role.strip(), json.dumps(topics_list), "[]", now),
            )
        conn.commit()
    return json.dumps({"status": "saved", "person_id": pid, "name": name, "company": company, "topics": topics_list})


def save_recommendation(person_name: str, recommendation: str, context: str = "") -> str:
    """Save a tool, book, framework, or idea recommended by a person.

    Args:
        person_name: The name of the person who gave the recommendation (e.g. 'Sarah').
        recommendation: What was recommended (e.g. 'Gemini Live').
        context: Context or reason for the recommendation.

    Returns:
        A JSON string confirming the recommendation was saved.
    """
    with get_db() as conn:
        row = conn.execute("SELECT * FROM people WHERE LOWER(name) = ?", (person_name.strip().lower(),)).fetchone()
        if not row:
            save_person(name=person_name)
            row = conn.execute("SELECT * FROM people WHERE LOWER(name) = ?", (person_name.strip().lower(),)).fetchone()
        recs = json.loads(row["recommendations"] or "[]")
        if recommendation.strip() not in recs:
            recs.append(recommendation.strip())
            conn.execute("UPDATE people SET recommendations = ? WHERE id = ?", (json.dumps(recs), row["id"]))
            conn.commit()
    return json.dumps({"status": "saved", "person_name": person_name, "recommendation": recommendation})


def search_memory(query: str) -> str:
    """Search stored event memories for people, companies, topics discussed, or recommendations.

    Args:
        query: The search term or question keyword (e.g. 'Google', 'Sarah', 'voice AI', 'Gemini Live').

    Returns:
        A JSON string containing matching people and their associated companies, topics, and recommendations.
    """
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

    results = {}
    with get_db() as conn:
        for term in terms:
            q = f"%{term}%"
            rows = conn.execute(
                """
                SELECT * FROM people
                WHERE LOWER(name) LIKE ?
                   OR LOWER(COALESCE(company, '')) LIKE ?
                   OR LOWER(COALESCE(role, '')) LIKE ?
                   OR LOWER(topics) LIKE ?
                   OR LOWER(recommendations) LIKE ?
                """,
                (q, q, q, q, q),
            ).fetchall()
            for r in rows:
                results[r["id"]] = {
                    "name": r["name"],
                    "company": r["company"],
                    "role": r["role"],
                    "topics": json.loads(r["topics"] or "[]"),
                    "recommendations": json.loads(r["recommendations"] or "[]"),
                }

    return json.dumps({"query": query, "matches": list(results.values())})


def get_person(name: str) -> str:
    """Retrieve all details about a specific person met at an event.

    Args:
        name: Name of the person (e.g. 'Sarah').

    Returns:
        A JSON string with the person's profile, company, topics, and recommendations.
    """
    with get_db() as conn:
        row = conn.execute("SELECT * FROM people WHERE LOWER(name) = ?", (name.strip().lower(),)).fetchone()
        if not row:
            return json.dumps({"status": "not_found", "message": f"No record found for {name}."})
        return json.dumps({
            "name": row["name"],
            "company": row["company"],
            "role": row["role"],
            "topics": json.loads(row["topics"] or "[]"),
            "recommendations": json.loads(row["recommendations"] or "[]"),
        })


def find_people_by_topic(topic: str) -> str:
    """Find all people working on or interested in a specific topic.

    Args:
        topic: The topic or technology to look up (e.g. 'voice AI').

    Returns:
        A JSON string listing people associated with the topic.
    """
    return search_memory(topic)
