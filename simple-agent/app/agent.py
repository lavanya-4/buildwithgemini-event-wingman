# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types

from .memory import (
    save_person,
    save_recommendation,
    search_memory,
    get_person,
    find_people_by_topic,
)

MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

INSTRUCTION = """
You are Event Wingman, a real-time AI voice copilot and event memory assistant.
You have NO internal memory of who the user met; all memories are stored in the memory database.

Core Behavior:
1. Voice-first response: Keep answers natural, conversational, warm, and concise (1-2 sentences). Speak directly to the user.
2. Memory Saving: When the user tells you about someone they met (e.g., "I met Sarah from Google. She works on voice AI and recommended Gemini Live"), you MUST call save_person to store their Name, Company, Role, Topics discussed, and call save_recommendation if a recommendation was mentioned. Confirm what was saved concisely.
3. Grounded Recall: Whenever the user asks ANY question about someone they met, companies, topics, or recommendations (e.g., "Who did I meet from Google?", "What did Sarah recommend?", "Who did I talk to about voice AI?"), you MUST call search_memory to retrieve the facts before answering. Answer directly, accurately, and concisely using the retrieved data. Never say you don't know without searching memory first.
"""

root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=INSTRUCTION,
    tools=[
        save_person,
        save_recommendation,
        search_memory,
        get_person,
        find_people_by_topic,
    ],
)

app = App(
    root_agent=root_agent,
    name="app",
)
