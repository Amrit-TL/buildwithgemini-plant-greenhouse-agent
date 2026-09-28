# 🌿 Plant & Greenhouse Concierge

An intelligent, conversational houseplant assistant and greenhouse concierge built with **Google Agent Development Kit (ADK)** and deployed on **Google Cloud Vertex AI Agent Runtime**. 

The concierge helps home gardeners and plant enthusiasts look up plant care requirements, check real-time greenhouse inventory stock, calculate tailored watering schedules, and generate visual preview photos and videos.

![Plant & Greenhouse Concierge Demo](demo.gif)

---

## 🚀 Built-in Capabilities & Services

The agent integrates the following Google Cloud services, APIs, and tools:

* **🧠 Vertex AI Memory Bank**: Persists user context, plant care history, skill levels, lighting conditions, and critical plant allergies across chat sessions using `PreloadMemoryTool` and session extraction callbacks.
* **🔥 Google Cloud Firestore**: Stores real-time greenhouse inventory, stock levels, sunlight requirements, care difficulty ratings, and historical care notes.
* **📦 Google Cloud Storage**: Public bucket storing AI-generated plant visual previews and short video clips accessible via public HTTPS URLs.
* **🖼️ Vertex AI Image Generation**: Generates high-definition plant preview photos using `gemini-2.5-flash-image` and `gemini-3.1-flash-lite-image`.
* **🎬 Vertex AI Video Generation**: Creates short video clips of plants and greenhouse items using Google's `gemini-omni-flash-preview` model.
* **💻 Agent Engine Code Sandbox**: Safely executes Python scripts in an isolated sandbox (`AgentEngineSandboxCodeExecutor`) to compute customized watering schedules based on temperature, humidity, and pot volume.
* **🎨 Agent User Interface (A2UI v0.8)**: Renders structured, compact display UI cards, columns, text, and images inside the frontend.
* **🗺️ Google Maps Platform & Public Botany APIs**:
  * **Geocoding API**: Converts street addresses or cities into latitude/longitude coordinates.
  * **Google Places API (New)**: Finds nearby florists, garden centers, and greenhouses.
  * **iNaturalist API**: Queries public botanical database records for species taxonomy, scientific names, and observation counts.

---

## 🛠️ Project Structure

```
plant-greenhouse-agent/
├── app/
│   ├── agent.py               # Root ADK Agent configuration, Memory Bank & instruction definitions
│   ├── tools.py               # Firestore, Cloud Storage, Imagen, Omni, Maps, and Botany tool implementations
│   ├── a2ui_utils.py          # A2UI response formatting callback
│   └── fast_api_app.py        # FastAPI A2A proxy server
├── frontend/
│   ├── main.py                # Standalone FastAPI web app proxying browser requests to Agent Engine
│   └── templates/
│       └── index.html         # Custom dark glassmorphic web UI with interactive prompt chips
├── seed_db.py                 # Script to populate Firestore 'plants' collection
├── agents-cli-manifest.yaml   # ADK agent manifest
├── deployment_metadata.json   # Deployed Agent Engine runtime resource references
├── pyproject.toml             # Python dependencies and project settings
└── demo.gif                   # Looping preview recording of the agent in action
```

---

## 💻 Local Setup & Execution

### 1. Prerequisites & Environment Setup

Ensure you have **Python 3.11+**, `uv`, and `gcloud` CLI installed and authenticated.

```bash
# Authenticate Google Cloud CLI & Application Default Credentials
gcloud auth login
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID
```

Create a `.env` file in the project root:

```ini
GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID
GOOGLE_MAPS_API_KEY=YOUR_GOOGLE_MAPS_API_KEY
```

### 2. Install Dependencies & Seed Database

```bash
# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate
uv sync

# Seed the Firestore database with initial greenhouse plant inventory
python seed_db.py
```

### 3. Run the Backend Agent Locally

Start the local ADK Web interface:

```bash
adk web --port 8000 app
```

### 4. Run the Custom FastAPI Web Frontend

To test the custom web frontend locally:

```bash
export AGENT_ENGINE_RESOURCE_NAME="projects/YOUR_PROJECT_ID/locations/us-east1/reasoningEngines/YOUR_ENGINE_ID"
export AGENT_DIRECTORY="app"

python frontend/main.py
```

Open a browser and navigate to port `8080` to interact with the concierge.

---

## 🧪 Running Tests

Run the unit test suite to verify tool execution and database connectivity:

```bash
pytest
```
