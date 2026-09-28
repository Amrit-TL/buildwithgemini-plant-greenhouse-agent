# ruff: noqa
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

import datetime
import json
from pathlib import Path
from zoneinfo import ZoneInfo

from a2ui.basic_catalog.provider import BasicCatalog
from a2ui.schema.manager import A2uiSchemaManager

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.memory.vertex_ai_memory_bank_service import VertexAiMemoryBankService
from google.adk.models import Gemini
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types

from app.a2ui_utils import a2ui_callback
from app.tools import (
    list_plants,
    get_plant_details,
    update_plant_stock,
    add_care_note,
    generate_plant_image,
    generate_domain_image,
    generate_domain_video,
    search_botany_database,
    geocode_address,
    search_nearby_places,
)

# Hardcoded GCP Project ID and Memory Bank ID (Agent Engine ID)
PROJECT_ID = "qwiklabs-gcp-01-68d0c980599a"
LOCATION = "us-east1"
MEMORY_BANK_ID = "485955552174669824"

# Load Agent Engine deployment metadata to attach sandbox code execution
deployment_meta_path = Path(__file__).resolve().parent.parent / "deployment_metadata.json"
sandbox_resource_name = None
agent_engine_resource_name = None

if deployment_meta_path.exists():
    try:
        with open(deployment_meta_path, "r") as f:
            meta = json.load(f)
            sandbox_resource_name = meta.get("sandbox_resource_name")
            agent_engine_resource_name = meta.get("remote_agent_runtime_id")
    except Exception:
        pass

# Initialize AgentEngineSandboxCodeExecutor with deployment metadata
code_executor = AgentEngineSandboxCodeExecutor(
    sandbox_resource_name=sandbox_resource_name,
    agent_engine_resource_name=agent_engine_resource_name,
)

# Initialize A2UI Schema Manager for version 0.8
schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

instruction = schema_manager.generate_system_prompt(
    role_description=(
        "You are the Plant & Greenhouse Concierge assistant. You help plant enthusiasts care for "
        "their plants, look up plant details, search greenhouse inventory, manage stock levels, "
        "generate visual preview photos, search public botanical databases, geocode locations, "
        "find nearby florists and greenhouses, and execute Python calculations safely in a code sandbox. "
        "You remember user preferences, facts, and ALL user allergies across sessions."
    ),
    workflow_description=(
        "Analyze the request, invoke tools when needed, and return structured UI when appropriate. "
        "Always review preloaded memories for user allergies before suggesting plants, inventory, or care advice, "
        "and warn the user if a plant or care product poses an allergy risk."
    ),
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        '{"Image": {"url": {"literalString": "https://..."}}}. Never point an '
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)


def memory_bank_service_builder():
    """
    Builder function for VertexAiMemoryBankService so the app uses Memory Bank when deployed.
    """
    return VertexAiMemoryBankService(
        project=PROJECT_ID,
        location=LOCATION,
        agent_engine_id=MEMORY_BANK_ID,
    )


async def generate_memories_callback(callback_context: CallbackContext):
    """
    Callback that sends turn session events to Memory Bank for cross-session extraction.
    """
    await callback_context.add_session_to_memory()
    return None


def get_weather(query: str) -> str:
    """Simulates a web search. Use it get information on weather.

    Args:
        query: A string containing the location to get weather information for.

    Returns:
        A string with the simulated weather information for the queried location.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        return "It's 60 degrees and foggy."
    return "It's 90 degrees and sunny."


def get_current_time(query: str) -> str:
    """Simulates getting the current time for a city.

    Args:
        city: The name of the city to get the current time for.

    Returns:
        A string with the current time information.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        tz_identifier = "America/Los_Angeles"
    else:
        return f"Sorry, I don't have timezone information for query: {query}."

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    return f"The current time for query {query} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-2.5-flash",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=instruction,
    code_executor=code_executor,
    tools=[
        PreloadMemoryTool(),
        list_plants,
        get_plant_details,
        update_plant_stock,
        add_care_note,
        generate_plant_image,
        generate_domain_image,
        generate_domain_video,
        search_botany_database,
        geocode_address,
        search_nearby_places,
        get_weather,
        get_current_time,
    ],
    after_model_callback=a2ui_callback,
    after_agent_callback=generate_memories_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)
