# GenAI Multimodal Report Generator

Production-grade RAG system for analyzing CSV, PDF, and Excel files.

## Setup
1. Install Poetry: `pip install poetry`
2. Install dependencies: `poetry install`
3. Run Local LLM: `ollama run llama3`
4. Start Server: `poetry run uvicorn src.app.main:app --reload`
