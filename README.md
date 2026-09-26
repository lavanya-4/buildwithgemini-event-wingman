# 🎙️ EventWingman Voice Agent

> **Real-time, voice-first AI networking copilot and temporary event memory for conference and meetup attendees.**

[![Built with Gemini](https://img.shields.io/badge/Built%20with-Gemini%202.5%20Flash-4285F4?logo=google&logoColor=white)](https://deepmind.google/technologies/gemini/)
[![Google Cloud Agent Platform](https://img.shields.io/badge/Google%20Cloud-Agent%20Platform-34A853?logo=googlecloud&logoColor=white)](https://cloud.google.com/products/agent-platform)
[![ADK](https://img.shields.io/badge/Agent%20Development%20Kit-ADK%202.6+-EA4335)](https://google.github.io/adk-docs/)
[![Protocol](https://img.shields.io/badge/Protocol-A2A-blue)](https://github.com/google/a2a)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

---

## 💡 Executive Summary & Vision

During conferences, hackathons, and professional summits, attendees meet dozens of people, exchange ideas, receive advice, and promise to follow up. By the end of an event, critical context is often lost:
- *Who did I meet?*
- *What were they working on?*
- *What specific tools or ideas did they recommend?*
- *Who else had overlapping interests?*
- *What follow-ups did I commit to?*

**Event Wingman** solves this by acting as a real-time voice copilot and temporary event memory. Between conversations, the user speaks naturally to the agent. Event Wingman automatically extracts structured entities, links relationships in a graph, provides grounded semantic recall, calculates explainable connection recommendations, and drafts contextual follow-ups that require explicit user approval before sending.

---

## 🛠️ Tool Coverage & Workshop Alignment

| Workshop Dimension | How Event Wingman Implements It |
| :--- | :--- |
| **Sessions & Memory** | Persistent SQLite relational knowledge graph with WAL mode tracking `people`, `companies`, `topics`, `conversations`, `ideas`, `recommendations`, `follow_ups`, and `relationships` (`MET`, `WORKS_AT`, `INTERESTED_IN`, `DISCUSSED`, `RECOMMENDED`). Case-insensitive deduplication ensures subsequent interactions enrich existing profiles rather than duplicating them. |
| **Function Tools** | 12 native Gemini function tools: `save_person`, `update_person`, `save_recommendation`, `save_idea`, `create_followup`, `draft_followup`, `search_memory`, `get_person`, `find_people_by_topic`, `find_related_people`, `get_followups`, `generate_event_recap`. |
| **Catalog & Rich UI** | Interactive force-directed relationship graph, Memory Explorer with tabbed card catalogs for People, Topics, Recommendations, and Ideas, Follow-up Action dashboard, and Event Retrospective modal. |
| **Voice & Speech** | Real-time speech input via Web Speech API with live interim streaming, Web Audio API RMS amplitude soundwave reactivity, click-to-interrupt / barge-in handling, and natural voice response synthesis using **Google Cloud Neural Text-to-Speech** (`en-US-Journey-F`). |
| **Compute & Reasoning** | Dual-pass extraction pipeline, token-level keyword intersection for related contact matching, and explainable matchmaking generating explicit "Why?" reasoning strings. |
| **Safety & Privacy** | Strict human-in-the-loop guarantee (Event Wingman **never** sends emails or external messages automatically), live microphone status indicators, one-click memory purger, and toggleable synthetic Demo Mode. |

---

## 🔄 End-to-End System Pipeline

```text
  VOICE (Speech Recognition & Barge-In)
    ↓
  GEMINI 2.5 FLASH (Reasoning & Multi-Tool Calling)
    ↓
  STRUCTURED EVENT MEMORY (Relational SQLite Knowledge Graph)
    ↓
  CONTEXTUAL REASONING (Explainable Matchmaking Engine)
    ↓
  HUMAN-IN-THE-LOOP ACTIONS (Drafted Follow-ups & Event Recap)
    ↓
  VOICE FEEDBACK (Google Cloud Journey Neural TTS)
```

---

## 🏗️ Architecture & Implementation

### A. Agent Platform (Vertex AI Agent Runtime)
- **Framework**: Built with Google ADK (Agent Development Kit) & `agents-cli`.
- **Protocol**: A2A (Agent-to-Agent) with standardized `.well-known/agent-card.json`.
- **Reasoning Engine**: Deployed to Vertex AI Reasoning Engines (`us-west1`).
- **Memory Tools**: Integrated ADK function tools for saving contacts, recommendations, and multi-field semantic recall.

### B. Full-Stack Web Application (`/event-wingman-mvp`)
- **Backend (FastAPI)**:
  - REST endpoints (`/api/chat`, `/api/voice/*`, `/api/memory/*`, `/api/network/*`, `/api/recap`).
  - Google Cloud Neural Text-to-Speech (`en-US-Journey-F`) for high-fidelity spoken responses.
  - Multi-pass entity extraction pipeline grounded with Gemini.
- **Frontend (React + Vite + Tailwind CSS)**:
  - **Voice Orb**: Real-time microphone capture with animated 4-state visualizer (`IDLE`, `LISTENING`, `THINKING`, `SPEAKING`).
  - **Live Transcript**: Speech recognition stream and pill badges for executed tools.
  - **Relationship Graph**: Force-directed network diagram showing connections between people, companies, and topics.
  - **Memory Explorer**: Catalog to review and manage saved contacts and discussions.

---

## 🎯 Core Demo Scenarios

1. **Natural Meeting Capture**:
   - User speaks: *"I just met Sarah from Acme AI. She's building voice agents for healthcare. We talked about Gemini Live and she recommended exploring interruption handling. I told her I'd connect with her after the event."*
   - Wingman records Sarah, Acme AI, topics, and recommendations, and prepares a draft follow-up with natural voice audio confirmation.
2. **Topic-Based Semantic Recall**:
   - User asks: *"Who did I talk to about voice agents?"*
   - Wingman recalls Sarah from Acme AI and her work on healthcare voice agents.
3. **Recommendation Recall**:
   - User asks: *"What did she recommend?"*
   - Wingman cites exploring interruption handling with Gemini Live.
4. **Contextual Follow-Up Drafting**:
   - User says: *"Draft a follow-up to Sarah."*
   - Wingman drafts a personalized follow-up grounded in conversation notes.
5. **Explainable Networking Similarity**:
   - User asks: *"Who have I met with interests similar to Sarah?"*
   - Wingman connects Sarah and Priya, explaining: *"Priya (Google) and Sarah (Acme AI) both share interests in Voice Agents."*
6. **Event Retrospective & Recap**:
   - User requests event recap: Wingman computes metrics and narrates a spoken summary.

---

## 🚀 Running Locally

### 1. Backend Server
```bash
cd event-wingman-mvp/backend
pip install -r ../requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### 2. Frontend Server
```bash
cd event-wingman-mvp/frontend
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 🧪 Testing

Run the automated scenario test suite:
```bash
pytest event-wingman-mvp/backend/tests/test_scenarios.py -v
```
