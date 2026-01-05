import os
import shutil
from pathlib import Path

def create_file(path: Path, content: str = ""):
    """Creates a file with given content."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    print(f"✅ Created: {path}")

def setup_project():
    root = Path("genai-report-generator")
    
    if root.exists():
        print(f"⚠️  Directory '{root}' already exists. Merging/Overwriting...")
    
    # --- 1. Directory Structure ---
    dirs = [
        # CI/CD & Config
        ".github/workflows",
        "config",
        "infra/terraform",
        "infra/helm",
        
        # Data & Docs (Local Dev)
        "data/raw",
        "data/processed",
        "data/artifacts",
        "docs/diagrams",
        "notebooks",
        "scripts",
        
        # Source Code - App Layer
        "src/app/api/v1",
        "src/app/core",
        "src/app/schemas",
        
        # Source Code - Cognitive Layer (Engine)
        "src/engine/agents",
        "src/engine/chains",
        "src/engine/prompts",
        "src/engine/tools",
        
        # Source Code - RAG Layer
        "src/rag/parsers",
        "src/rag/embeddings",
        "src/rag/vector_store",
        
        # Tests
        "tests/unit",
        "tests/integration",
        "tests/evaluation",
    ]

    for d in dirs:
        (root / d).mkdir(parents=True, exist_ok=True)

    # --- 2. Create __init__.py for Packages ---
    # Any folder inside src or tests needs to be a package
    for path in (root / "src").rglob("*"):
        if path.is_dir():
            (path / "__init__.py").touch()
    for path in (root / "tests").rglob("*"):
        if path.is_dir():
            (path / "__init__.py").touch()

    # --- 3. Configuration Files ---
    
    # config/settings.yaml
    create_file(root / "config/settings.yaml", """
project_name: "GenAI Report Generator"
version: "1.0.0"

server:
  host: "0.0.0.0"
  port: 8000

llm:
  # The smart model for writing the final report
  cloud_model: 
    provider: "openai"  # or "azure", "anthropic"
    model_name: "gpt-4o"
    temperature: 0.2

  # The local model for summarization/privacy
  local_model:
    provider: "ollama"
    model_name: "llama3"
    base_url: "http://localhost:11434"

rag:
  chunk_size: 1000
  chunk_overlap: 200
  vector_db_path: "data/chroma_db"
""")

    # config/secrets.yaml (Gitignored usually)
    create_file(root / "config/secrets.yaml", """
OPENAI_API_KEY: "sk-..."
LANGCHAIN_API_KEY: "ls-..."
""")

    # --- 4. Core Application Files ---

    # src/app/main.py
    create_file(root / "src/app/main.py", """
from fastapi import FastAPI
from src.app.core.logger import logger

app = FastAPI(title="GenAI Report Generator API")

@app.on_event("startup")
async def startup_event():
    logger.info("Application is starting...")

@app.get("/health")
def health_check():
    return {"status": "active", "module": "genai-reporter"}
""")

    # src/app/core/logger.py
    create_file(root / "src/app/core/logger.py", """
import logging
import sys

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("genai-app")
""")

    # --- 5. Engine & Logic Files ---

    # src/engine/llm.py (Factory Pattern)
    create_file(root / "src/engine/llm.py", """
from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatOllama
import yaml

def get_llm(type="cloud"):
    # Load config (in real app, use a proper config loader)
    with open("config/settings.yaml") as f:
        cfg = yaml.safe_load(f)
    
    if type == "cloud":
        return ChatOpenAI(model=cfg['llm']['cloud_model']['model_name'])
    elif type == "local":
        return ChatOllama(model=cfg['llm']['local_model']['model_name'])
""")

    # src/engine/prompts/analyst.yaml
    create_file(root / "src/engine/prompts/analyst.yaml", """
role: "Senior Data Analyst"
instruction: |
  You are an expert Python data analyst. 
  You have access to a dataset containing business data.
  Your goal is to answer the user's question by WRITING CODE.
  
  Constraints:
  1. Do not hallucinate numbers.
  2. Use the provided dataframe `df`.
  3. Output only valid Python code inside ```python ``` blocks.
""")

    # src/engine/agents/analyst.py
    create_file(root / "src/engine/agents/analyst.py", """
# This file will contain the LangGraph node for the Analyst
def analyst_node(state):
    print("--- Analyst Agent: Generating Code ---")
    # Logic to load prompt and call LLM goes here
    return {"messages": ["Code generated"]}
""")

    # --- 6. Project Root Files ---

    # .gitignore
    create_file(root / ".gitignore", """
# Python
__pycache__/
*.py[cod]
venv/
.env

# Data
data/
!data/.gitkeep
config/secrets.yaml

# IDE
.vscode/
.idea/
""")

    # pyproject.toml (Modern dependency management)
    create_file(root / "pyproject.toml", """
[tool.poetry]
name = "genai-report-generator"
version = "0.1.0"
description = "Multimodal RAG Report Generator"
authors = ["Your Name <you@example.com>"]

[tool.poetry.dependencies]
python = "^3.10"
fastapi = "^0.109.0"
uvicorn = "^0.27.0"
langchain = "^0.1.0"
langgraph = "^0.0.26"
langchain-openai = "^0.0.8"
langchain-community = "^0.0.20"
chromadb = "^0.4.22"
unstructured = {extras = ["all-docs"], version = "^0.12.0"}
pandas = "^2.2.0"
openpyxl = "^3.1.2"
pypdf = "^4.0.0"
python-multipart = "^0.0.9"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
""")

    # README.md
    create_file(root / "README.md", """
# GenAI Multimodal Report Generator

Production-grade RAG system for analyzing CSV, PDF, and Excel files.

## Setup
1. Install Poetry: `pip install poetry`
2. Install dependencies: `poetry install`
3. Run Local LLM: `ollama run llama3`
4. Start Server: `poetry run uvicorn src.app.main:app --reload`
""")

    print(f"\n🚀 Scaffolding complete! Project created at: {root.absolute()}")
    print("Next Step: Run 'cd genai-report-generator && poetry install' (or pip install -r requirements.txt if you create one)")

if __name__ == "__main__":
    setup_project()