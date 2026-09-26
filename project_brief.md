# Project Brief: EventWingman Voice Agent

**One-liner**: A real-time, voice-first AI networking copilot and temporary event memory that helps conference, hackathon, and meetup attendees capture who they met, remember recommendations and topics, discover explainable connections, and prepare human-approved follow-ups without manual note-taking.

---

## 1. Executive Summary & Vision

During conferences, hackathons, and professional summits, attendees meet dozens of people, exchange ideas, receive advice, and promise to follow up. By the end of an event, critical context is often lost:
- *Who did I meet?*
- *What were they working on?*
- *What specific tools or ideas did they recommend?*
- *Who else had overlapping interests?*
- *What follow-ups did I commit to?*

**Event Wingman** solves this by acting as a real-time voice copilot and temporary event memory. Between conversations, the user speaks naturally to the agent. Event Wingman automatically extracts structured entities, links relationships in a graph, provides grounded semantic recall, calculates explainable connection recommendations, and drafts contextual follow-ups that require explicit user approval before sending.

---

## 2. Tool Coverage & Workshop Alignment

| Workshop Dimension | How Event Wingman Implements It |
| :--- | :--- |
| **Sessions & Memory** | Persistent SQLite relational knowledge graph with WAL mode tracking `people`, `companies`, `topics`, `conversations`, `ideas`, `recommendations`, `follow_ups`, and `relationships` (`MET`, `WORKS_AT`, `INTERESTED_IN`, `DISCUSSED`, `RECOMMENDED`). Case-insensitive deduplication ensures subsequent interactions enrich existing profiles rather than duplicating them. |
| **Function Tools** | 12 native Gemini function tools: `save_person`, `update_person`, `save_recommendation`, `save_idea`, `create_followup`, `draft_followup`, `search_memory`, `get_person`, `find_people_by_topic`, `find_related_people`, `get_followups`, `generate_event_recap`. |
| **Catalog & Rich UI** | Interactive force-directed relationship graph, Memory Explorer with tabbed card catalogs for People, Topics, Recommendations, and Ideas, Follow-up Action dashboard, and Event Retrospective modal. |
| **Voice & Speech** | Real-time speech input via Web Speech API with live interim streaming, Web Audio API RMS amplitude soundwave reactivity, click-to-interrupt / barge-in handling, and natural voice response synthesis using **Google Cloud Neural Text-to-Speech** (`en-US-Journey-F`). |
| **Compute & Reasoning** | Dual-pass extraction pipeline, token-level keyword intersection for related contact matching, and explainable matchmaking generating explicit "Why?" reasoning strings. |
| **Safety & Privacy** | Strict human-in-the-loop guarantee (Event Wingman **never** sends emails or external messages automatically), live microphone status indicators, one-click memory purger, and toggleable synthetic Demo Mode. |

---

## 3. End-to-End System Pipeline

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

## 4. Key Components & Implementation

### A. Backend Architecture (`/backend`)
- **FastAPI Application (`main.py`)**: REST endpoints (`/api/chat`, `/api/voice/*`, `/api/memory/*`, `/api/network/*`, `/api/recap`) and WebSocket streaming endpoint (`/api/ws/voice`) with static React bundle mount.
- **Gemini Agent Service (`services/gemini_voice_service.py`)**: Powered by Google GenAI on Vertex AI using `gemini-2.5-flash` with system instructions enforcing concise voice replies, grounded recall, and proactive tool execution.
- **Dual-Pass Extraction Service (`services/extraction_service.py`)**: Extracts people, roles, companies, topics, recommendations, ideas, and follow-up commitments without rigid user commands.
- **Relational Memory Service (`services/memory_service.py`)**: SQLite database with foreign keys, WAL mode, entity deduplication, multi-table semantic search, demo data seeder, and complete privacy wipe.
- **Relationship Service (`services/relationship_service.py`)**: Analyzes shared topics and companies, generates force-directed graph node-link models, and provides explainable "Why?" recommendations (e.g., *"Sarah (Acme AI) and Daniel (Startup X) both share interests in Voice Agents"*).
- **Follow-Up Service (`services/followup_service.py`)**: Contextually drafts personalized follow-up emails grounded in actual conversation notes and recommendations. Supports inline editing, tone adjustments, approval, and dismissal.
- **Event Recap Service (`services/event_recap_service.py`)**: Aggregates event metrics (People Met, Conversations, Topics, Ideas Captured, Follow-ups, Potential Connections) and generates spoken recap scripts.
- **Text-to-Speech Service (`services/tts_service.py`)**: Generates high-fidelity MP3 audio bytes using Google Cloud Neural TTS (`en-US-Journey-F`).

### B. Frontend Architecture (`/frontend`)
- **Voice Orb (`VoiceOrb.tsx`)**: 4-state visual orb (`IDLE`, `LISTENING`, `THINKING`, `SPEAKING`) with Canvas soundwave reactivity and barge-in click handler.
- **Live Transcript (`LiveTranscript.tsx`)**: Real-time interim voice transcription, speech bubbles, and tool execution pill badges (e.g. `💾 Saved contact`, `🔍 Searched memory`).
- **Quick Actions & Text Input (`QuickActions.tsx`)**: Pre-configured demo prompts for rapid voice/text interaction.
- **Relationship Graph (`RelationshipGraph.tsx`)**: Force-directed network graph visualizing connections between User, People, Companies, Topics, and Ideas with an interactive node inspector.
- **Memory Explorer (`MemoryExplorer.tsx`)**: Tabbed interface for browsing, inspecting, and deleting stored event memories.
- **Follow-Up Actions (`FollowUpActions.tsx`)**: Action dashboard with inline message editor, tone regenerator, human approval buttons, and safety badges.
- **Event Recap Modal (`EventRecapModal.tsx`)**: Metrics grid and spoken retrospective audio trigger.
- **Privacy Banner (`PrivacyBanner.tsx`)**: Real-time microphone status (`MIC LIVE` vs `MIC MUTED`), Demo Mode toggle, and clear-all memory button.

---

## 5. Core Demo Scenarios (Verified)

1. **Natural Meeting Capture**:
   - User speaks: *"I just met Sarah from Acme AI. She's building voice agents for healthcare. We talked about Gemini Live and she recommended exploring interruption handling. I told her I'd connect with her after the event."*
   - System records Sarah, Acme AI, topics, the recommendation, and prepares a draft follow-up. Cloud TTS responds with natural voice audio.
2. **Topic-Based Semantic Recall**:
   - User asks: *"Who did I talk to about voice agents?"*
   - Wingman recalls Sarah from Acme AI and her work on healthcare voice agents.
3. **Recommendation Recall**:
   - User asks: *"What did she recommend?"*
   - Wingman cites exploring interruption handling with Gemini Live.
4. **Contextual Follow-Up Drafting**:
   - User says: *"Draft a follow-up to Sarah."*
   - Wingman crafts a grounded follow-up message ready for review and editing in the Actions tab.
5. **Explainable Networking Similarity**:
   - User adds Priya from Google working on multimodal voice AI.
   - User asks: *"Who have I met with interests similar to Sarah?"*
   - Wingman connects Sarah and Priya, explaining: *"Priya (Google) and Sarah (Acme AI) both share interests in Voice Agents."*
6. **Event Retrospective & Recap**:
   - User requests event recap.
   - Wingman calculates aggregated metrics and reads out the spoken retrospective summary.

---

## 6. Verification & Automated Testing

- **Automated Pytest Suite (`backend/tests/test_scenarios.py`)**: 5 out of 5 scenario test suites passed with 100% success rate.
- **Live Service Verification**: Verified with Vertex AI `gemini-2.5-flash` and Google Cloud Text-to-Speech using Application Default Credentials (ADC) on project `qwiklabs-gcp-01-9c5a198b6a9e`.
- **Live Server**: Running on port `8000` (FastAPI serving the React build) and port `5173` (Vite dev server).
