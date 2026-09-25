"""End-to-end scenario tests for Event Wingman core flows."""

import os
import sys
import tempfile
import pytest

# Ensure backend directory is in python path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from services.event_recap_service import EventRecapService
from services.extraction_service import MemoryExtractionService
from services.followup_service import FollowUpService
from services.gemini_voice_service import GeminiVoiceService
from services.memory_service import MemoryService
from services.relationship_service import RelationshipService


@pytest.fixture
def test_services():
    """Create a temporary database and service bundle for tests."""
    temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    temp_db.close()
    db_path = temp_db.name

    memory = MemoryService(db_path=db_path)
    relationship = RelationshipService(memory)
    followup = FollowUpService(memory)
    recap = EventRecapService(memory, relationship)
    extraction = MemoryExtractionService(memory)
    voice = GeminiVoiceService(
        memory_service=memory,
        relationship_service=relationship,
        followup_service=followup,
        recap_service=recap,
        extraction_service=extraction,
    )

    yield {
        "db_path": db_path,
        "memory": memory,
        "relationship": relationship,
        "followup": followup,
        "recap": recap,
        "voice": voice,
        "extraction": extraction,
    }

    if os.path.exists(db_path):
        os.unlink(db_path)


def test_scenario_1_and_2(test_services):
    """TEST 1: Store Sarah with company and topics from speech.

    TEST 2: Retrieve Sarah when querying for healthcare voice agents.
    """
    voice = test_services["voice"]
    memory = test_services["memory"]

    # TEST 1
    utterance_1 = "I just met Sarah from Acme AI. She's building voice agents for healthcare."
    res1 = voice.process_user_message(utterance_1)
    assert res1["response_text"] is not None

    sarah = memory.get_person_by_name("Sarah")
    assert sarah is not None, "Sarah was not saved to memory"
    assert sarah["company"] == "Acme AI"
    assert any("voice" in t.lower() or "healthcare" in t.lower() for t in sarah["topics"])

    # TEST 2: Query for healthcare voice agents
    res2 = voice.process_user_message("Who did I meet working on healthcare voice agents?")
    assert "Sarah" in res2["response_text"] or "Acme AI" in res2["response_text"]

    search_res = memory.find_people_by_topic("healthcare")
    assert len(search_res) >= 1
    assert search_res[0]["name"] == "Sarah"


def test_scenario_3_and_4(test_services):
    """TEST 3: Update existing Sarah record with recommendation (deduplication).

    TEST 4: Retrieve Sarah's recommendation.
    """
    voice = test_services["voice"]
    memory = test_services["memory"]

    # Seed initial Sarah
    memory.save_person(
        name="Sarah",
        company="Acme AI",
        topics=["Voice Agents", "Healthcare AI"],
    )
    initial_count = len(memory.list_people())

    # TEST 3: User relates recommendation
    utterance_3 = "Sarah recommended that I explore interruption handling."
    res3 = voice.process_user_message(utterance_3)

    # Check deduplication: still exactly 1 person named Sarah
    all_people = memory.list_people()
    assert len(all_people) == initial_count, f"Expected 1 person, found {len(all_people)}"
    sarah = memory.get_person_by_name("Sarah")
    assert sarah is not None

    recs = memory.list_recommendations(sarah["id"])
    assert len(recs) >= 1
    assert any("interruption handling" in r["content"].lower() for r in recs)

    # TEST 4: Query what Sarah recommended
    res4 = voice.process_user_message("What did Sarah recommend?")
    assert "interruption" in res4["response_text"].lower()


def test_scenario_5_draft_followup(test_services):
    """TEST 5: Draft contextual follow-up to Sarah from stored conversation."""
    voice = test_services["voice"]
    followup_service = test_services["followup"]
    memory = test_services["memory"]

    sarah = memory.save_person(
        name="Sarah",
        company="Acme AI",
        topics=["Healthcare Voice Agents", "Gemini Live"],
    )
    memory.save_recommendation(
        content="Explore interruption handling",
        recommended_by_person_id=sarah["id"],
    )

    # TEST 5: Draft follow-up
    res5 = voice.process_user_message("Draft a follow-up to Sarah.")
    assert "Sarah" in res5["response_text"] or "follow" in res5["response_text"].lower()

    # Verify follow-up in database
    fus = memory.list_followups(sarah["id"])
    assert len(fus) >= 1
    draft_msg = fus[0]["draftMessage"]
    assert draft_msg is not None
    assert "Sarah" in draft_msg
    assert "Acme AI" in draft_msg or "voice" in draft_msg.lower() or "interruption" in draft_msg.lower()
    assert fus[0]["status"] == "draft"


def test_scenario_6_networking_similarity(test_services):
    """TEST 6: Find similar people and explain relationship."""
    relationship_service = test_services["relationship"]
    memory = test_services["memory"]

    p_sarah = memory.save_person(
        name="Sarah",
        company="Acme AI",
        topics=["Voice Agents", "Healthcare AI"],
    )
    p_priya = memory.save_person(
        name="Priya",
        company="Google",
        topics=["Voice Agents", "Multimodal Agents"],
    )

    related = relationship_service.find_related_people("Sarah")
    assert len(related["matches"]) >= 1
    match0 = related["matches"][0]
    assert match0["person"]["name"] == "Priya"
    assert "voice agents" in [t.lower() for t in match0["commonTopics"]]
    assert len(match0["explanation"]) > 0
    assert "Sarah" in match0["explanation"] and "Priya" in match0["explanation"]


def test_recap_and_graph(test_services):
    """Test Event Recap metrics generation and Network Graph formatting."""
    recap_service = test_services["recap"]
    relationship_service = test_services["relationship"]
    memory = test_services["memory"]

    memory.seed_demo_data()

    recap = recap_service.generate_recap()
    assert recap["metrics"]["peopleMet"] == 3
    assert recap["metrics"]["ideasCaptured"] >= 1
    assert len(recap["spokenScript"]) > 0

    graph = relationship_service.get_network_graph()
    assert len(graph["nodes"]) > 5
    assert any(n["id"] == "user_me" for n in graph["nodes"])
    assert any(n["label"] == "Sarah" for n in graph["nodes"])
