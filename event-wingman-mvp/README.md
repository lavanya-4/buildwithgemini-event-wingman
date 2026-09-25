# 🎙️ Event Wingman — Real-Time Gemini AI Networking Copilot

> **An intelligent, voice-first networking copilot for conferences, hackathons, meetups, and networking events.**  
> Powered by Google Gemini 2.5 Flash on Vertex AI, Google Cloud Neural Text-to-Speech, SQLite relational memory, and an interactive force-directed relationship graph.

---

## 🌟 Product Vision

People attend events, meet dozens of people, exchange ideas, and make promises to follow up. By the end of the day, key details blur:
- *Who did I meet?*
- *What were they working on?*
- *What specific tools or ideas did they recommend?*
- *Who else had overlapping interests?*
- *What follow-ups did I commit to?*

**Event Wingman** acts as your real-time networking copilot and temporary event memory. Instead of manual note-taking, you simply **talk naturally** to the agent between conversations.

### The Pipeline
```text
  VOICE (Speech Recognition & Barge-In)
    ↓
  GEMINI 2.5 FLASH (Reasoning & Multi-Tool Calling)
    ↓
  STRUCTURED EVENT MEMORY (Relational Knowledge Graph)
    ↓
  CONTEXTUAL REASONING (Explainable Matchmaking)
    ↓
  HUMAN-IN-THE-LOOP ACTIONS (Drafted Follow-ups & Recap)
    ↓
  VOICE FEEDBACK (Google Cloud Journey Neural TTS)
```

---

## 🏛️ System Architecture

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React 19 + Vite)                      │
│                                                                        │
│  ┌───────────────────────┐  ┌────────────────────────────────────────┐  │
│  │   Animated Voice Orb  │  │  Live Transcript & Tool Execution      │  │
│  │  (IDLE/LISTEN/THINK/  │  │  • Real-time speech interim text       │  │
│  │   SPEAK + Waveform)   │  │  • Tool execution pill badges          │  │
│  └───────────┬───────────┘  └───────────────────┬────────────────────┘  │
│              │ (Barge-in / Mic)                 │                       │
│  ┌───────────▼───────────┐  ┌───────────────────▼────────────────────┐  │
│  │  Relationship Graph   │  │  Follow-Up Assistant & Memory Explorer │  │
│  │  (Force-Directed SVG/ │  │  • Edit / Regenerate / Approve drafts  │  │
│  │   Canvas + "Why?" UX) │  │  • Contacts, Topics, Recs, Ideas       │  │
│  └───────────────────────┘  └────────────────────────────────────────┘  │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │ REST / WebSocket (/api/*)
┌────────────────────────────────────▼───────────────────────────────────┐
│                     BACKEND ENGINE (FastAPI + Python)                  │
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  Gemini Voice Service (google-genai on Vertex AI gemini-2.5-flash)│  │
│  │  • 12 Native Function Tools for Memory & Graph Traversal         │  │
│  │  • Dual-Pass Structured Entity Extraction (People, Recs, Ideas)  │  │
│  └───────────────────┬───────────────────────────────┬──────────────┘  │
│                      │                               │                 │
│  ┌───────────────────▼────────────┐    ┌─────────────▼──────────────┐  │
│  │   Relationship Service         │    │   Follow-Up Service        │  │
│  │   • Token & Semantic Matching  │    │   • Grounded Email Drafts  │  │
│  │   • Explainable "Why?" Engine  │    │   • Strict Human-in-the-Loop│ │
│  │   • Proactive Event Insights   │    │   • Approval State Machine │  │
│  └───────────────────┬────────────┘    └─────────────┬──────────────┘  │
│                      │                               │                 │
│  ┌───────────────────▼───────────────────────────────▼──────────────┐  │
│  │   SQLite Persistent Event Store (WAL Mode, RowFactory)           │  │
│  │   Tables: people, companies, topics, conversations, ideas,       │  │
│  │           recommendations, follow_ups, relationships             │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │   Google Cloud Neural Text-to-Speech (en-US-Journey-F)           │  │
│  │   • Low-latency high-fidelity voice response generation          │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────┘
```

---

## ⚡ Core Features

1. **Voice-First Interaction & Animated Orb**
   - 4 visual states: `IDLE` (soft glow), `LISTENING` (pulsing blue/violet), `THINKING` (shimmering amber), `SPEAKING` (soundwave reactive magenta/indigo).
   - Natural audio reactivity driven by real-time Web Audio API RMS amplitude.
   - Click-to-interrupt / barge-in: Speaking cuts off immediately when the user talks or clicks the orb.

2. **Grounded Memory Extraction & Deduplication**
   - Natural spoken input automatically updates contacts, companies, topics, and recommendations without keyword rigidity.
   - Case-insensitive entity deduplication: Mentioning Sarah again enhances her existing profile rather than duplicating records.

3. **Multi-Hop Semantic & Topic Recall**
   - Queries like *"Who did I talk to about voice agents?"* or *"What did Sarah recommend?"* directly inspect relational memory tables and cite exact context.

4. **Explainable Relationship Matching**
   - Identifies overlapping technical domains (e.g., Sarah's healthcare voice agents and Priya's multimodal voice AI).
   - Every connection provides an explicit **"Why?"** explanation (e.g., *"Sarah (Acme AI) and Daniel (Startup X) both share interests in Voice Agents"*).

5. **Human-in-the-Loop Follow-Up Assistant**
   - Generates contextual follow-up emails grounded in actual conversations.
   - **Guaranteed Safety**: Wingman **never** sends emails automatically. Users can review, edit inline, regenerate tones, approve, or dismiss.

6. **Event Recap & Intelligence Dashboard**
   - Aggregates event metrics: People Met, Conversations, Topics, Ideas Captured, Follow-ups Pending, and Potential Introductions.
   - Generates a natural spoken summary ready to be read aloud via Cloud TTS.

7. **Privacy & Data Governance**
   - Clear visual indicator for microphone status (`MIC LIVE` vs `MIC MUTED`).
   - One-click memory inspection and selective record deletion.
   - Complete data purge button with confirmation.
   - Built-in synthetic **Demo Mode** toggle clearly labeled for demonstrations.

---

## 🚀 Quickstart & Setup

### Prerequisites
- Python 3.10+ (tested with Python 3.14)
- Node.js 18+ (tested with Node 24)
- Google Cloud Project with Vertex AI & Cloud Text-to-Speech APIs enabled

### 1. Environment Configuration
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Ensure your `.env` contains:
```ini
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_GENAI_USE_VERTEXAI=true
GEMINI_MODEL=gemini-2.5-flash
TTS_VOICE_NAME=en-US-Journey-F
PORT=8000
HOST=0.0.0.0
```

### 2. Install Backend Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 3. Install Frontend & Build Bundle
```bash
cd ../frontend
npm install
npm run build
```

### 4. Run the Application
Start the FastAPI server:
```bash
cd ../backend
python main.py
```
Open your browser at:
👉 **`http://localhost:8000`** (FastAPI serves the React application directly)  
Or for frontend hot-reloading:
👉 `npm run dev` at `http://localhost:5173`

---

## 🎯 End-to-End Demo Walkthrough

Try speaking (or typing via the Quick Prompt chips) the following exact sequence:

1. **Log Meeting with Sarah**:
   > *"I just met Sarah from Acme AI. She's building voice agents for healthcare. We talked about Gemini Live and she recommended exploring interruption handling. I told her I'd connect with her after the event."*  
   - **Result**: Wingman confirms saving Sarah, records Acme AI, tags topics `voice agents`, `healthcare`, `Gemini Live`, saves the recommendation, and prepares a draft follow-up.

2. **Recall by Topic**:
   > *"Who did I talk to about voice agents?"*  
   - **Result**: *"You talked to Sarah from Acme AI about voice agents. She's building voice agents for healthcare."*

3. **Recall Recommendation**:
   > *"What did she recommend?"*  
   - **Result**: *"Sarah recommended exploring interruption handling, specifically in the context of Gemini Live."*

4. **Draft Follow-up**:
   > *"Draft a follow-up to Sarah."*  
   - **Result**: Generates a grounded draft in the Actions tab:  
     `"Hi Sarah, great meeting you at the event! I really enjoyed our conversation about healthcare, Gemini Live and voice agents. Your suggestion regarding 'exploring interruption handling' was especially insightful. I'd love to stay connected and follow up on what you're building at Acme AI."`

5. **Meet Another Person**:
   > *"I met Priya from Google. She is working on multimodal voice AI."*  
   - **Result**: Priya is added to the network graph.

6. **Find Overlapping Connections**:
   > *"Who have I met with interests similar to Sarah?"*  
   - **Result**: Wingman identifies Priya and explains: *"Priya (Google) and Sarah (Acme AI) both share interests in Voice Agents."*

7. **Event Recap**:
   > Click the **Event Recap** button or say *"Give me my event recap."*  
   - **Result**: Opens the Retrospective Modal showing metrics (People Met: 2, Topics: 5, Recs: 1, Follow-ups: 1) and speaks the recap aloud!

---

## 🧪 Automated Testing

Run the comprehensive pytest suite verifying all 6 core memory, recall, and relationship requirements:
```bash
pytest backend/tests/test_scenarios.py -v
```

Verified test results:
```text
backend/tests/test_scenarios.py::test_scenario_1_natural_capture_and_recall PASSED
backend/tests/test_scenarios.py::test_scenario_2_deduplication_and_memory_update PASSED
backend/tests/test_scenarios.py::test_scenario_3_recommendation_recall PASSED
backend/tests/test_scenarios.py::test_scenario_4_grounded_followup_lifecycle PASSED
backend/tests/test_scenarios.py::test_scenario_5_networking_similarity_with_why_reasoning PASSED

============================== 5 passed in 0.05s ===============================
```

---

## 🛡️ Privacy & Human-in-the-Loop Design

- **Temporary Event Scope**: Memory is designed specifically for event duration and can be wiped with one click.
- **Explicit User Approval**: The agent never sends an email, SMS, or LinkedIn message autonomously.
- **Microphone Visibility**: Clear UI indicator when listening, with instant tap-to-mute.
- **No Third-Party Exfiltration**: Data resides in the local SQLite database.

---

## 📄 License

Apache 2.0. Built with Google Gemini 2.5 Flash on Vertex AI.
