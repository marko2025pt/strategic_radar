# tests/create_trello_board.py
# Creates a full Trello board with lists and cards for the Strategic Radar project.
# Run once. Safe to re-run — creates a new board each time.

import os
import requests
from pathlib import Path
from dotenv import load_dotenv

# ─────────────────────────────────────────────
# Load environment variables
# ─────────────────────────────────────────────

load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env", override=True)

API_KEY   = os.getenv("TRELLO_API_KEY")
TOKEN     = os.getenv("TRELLO_TOKEN")
WORKSPACE = os.getenv("TRELLO_WORKSPACE")

AUTH = {"key": API_KEY, "token": TOKEN}

print(f"API Key loaded: {'yes' if API_KEY else 'NO'}")
print(f"Token loaded: {'yes' if TOKEN else 'NO'}")
print(f"Workspace: {WORKSPACE}")

# ─────────────────────────────────────────────
# Board data
# ─────────────────────────────────────────────

BOARD = {
    "name": "Strategic Radar — Project 3",
    "lists": [
        {
            "name": "📌 Decisions & Notes",
            "cards": [
                "Layered MVP: V1.0 → V1.1 → V1.2",
                "Fallback rule: if V1.2 not done demo V1.1, if V1.1 not done demo V1.0",
                "override=True in load_dotenv() — conda base env conflict",
                "Pinecone region: AWS us-east-1 (Virginia)",
                "Vector IDs must be ASCII — use make_ascii_id()",
                "Max 7 LLM calls per run (V1.0)",
                "Max 5 signals evaluated per run",
                "Competitor registry as JSON reconstructed as text for RAG",
            ]
        },
        {
            "name": "✅ Done",
            "cards": [
                "Industry selection — DOOH and Self-Service Kiosk",
                "Company selection — PARTTEAM & OEMKIOSKS",
                "Project scope and architecture defined",
                "Architecture decisions documented (11 decisions)",
                "GitHub repo created — strategic_radar",
                "Project folder structure created",
                "Python venv setup",
                "kb/business_profile.md — 5 chunks",
                "kb/strategic_direction.md — 6 chunks",
                "kb/competitor_registry.json — 6 chunks",
                "kb/technology_watchlist.md — 7 chunks",
                "Pinecone account and index created",
                "rag/ingest.py — complete and verified",
                "24 vectors upserted to Pinecone ✅",
                "tests/test_openai_key.py",
            ]
        },
        {
            "name": "🔨 In Progress",
            "cards": [
                "rag/retriever.py — Pinecone query layer",
            ]
        },
        {
            "name": "🧪 Testing",
            "cards": []
        },
        {
            "name": "📋 Backlog",
            "cards": [
                "agent/state.py — LangGraph TypedDict state schema",
                "agent/graph.py — LangGraph workflow definition",
                "agent/nodes.py — Node implementations",
                "agent/agent.py — Main agent entrypoint",
                "agent/tools/tavily.py — Web search tool (V1.0)",
                "agent/tools/newsapi.py — News search tool (V1.0)",
                "agent/tools/ted.py — EU tenders tool (V1.1)",
                "api/main.py — FastAPI server and endpoints",
                "api/main.py — Gradio UI mounted at /ui",
                "Gradio UI — competitor dropdown (registry-controlled)",
                "Gradio UI — intelligence type selector",
                "Gradio UI — time range selector (7 / 14 / 30 days)",
                "Gradio UI — snapshot display in browser",
                "n8n/workflow.json — N8N workflow export",
                ".env.example — Template for environment variables",
                "requirements.txt — Final dependencies list",
                "Generate sample reports (minimum 2-3)",
                "Deploy FastAPI to Railway",
                "Configure N8N Cloud workflow",
                "Demo video or presentation (5-7 min)",
            ]
        },
        {
            "name": "🚀 Deployed",
            "cards": []
        },
    ]
}

# ─────────────────────────────────────────────
# Create board
# ─────────────────────────────────────────────

print(f"\nCreating board: {BOARD['name']}...")

res = requests.post(
    "https://api.trello.com/1/boards/",
    params={
        **AUTH,
        "name": BOARD["name"],
        "idOrganization": WORKSPACE,
        "defaultLists": "false",
    }
)
res.raise_for_status()
board = res.json()
board_id = board["id"]
board_url = board["shortUrl"]
print(f"✅ Board created: {board_url}")

# ─────────────────────────────────────────────
# Create lists and cards
# ─────────────────────────────────────────────

for i, list_data in enumerate(BOARD["lists"]):
    print(f"\nCreating list: {list_data['name']}...")

    res = requests.post(
        "https://api.trello.com/1/lists",
        params={
            **AUTH,
            "name": list_data["name"],
            "idBoard": board_id,
            "pos": (i + 1) * 1000,
        }
    )
    res.raise_for_status()
    list_id = res.json()["id"]
    print(f"  ✅ List created")

    for card_name in list_data["cards"]:
        res = requests.post(
            "https://api.trello.com/1/cards",
            params={
                **AUTH,
                "name": card_name,
                "idList": list_id,
            }
        )
        res.raise_for_status()
        print(f"    → {card_name}")

# ─────────────────────────────────────────────
# Done
# ─────────────────────────────────────────────

print(f"\n✅ Trello board fully created.")
print(f"👉 Open it here: {board_url}")