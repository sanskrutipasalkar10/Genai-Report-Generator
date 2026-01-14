import requests
import json
import os
import time  # 🟢 Added for sleep/backoff
from typing import List, Optional, Any
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
from langchain_core.language_models import BaseChatModel
from langchain_core.outputs import ChatResult, ChatGeneration

class OllamaRestChatModel(BaseChatModel):
    """
    A Custom LangChain wrapper that uses the REST API (requests) directly.
    Includes Retry Logic for System Stability (503/Timeout handling).
    """
    model_name: str
    base_url: str = "http://localhost:11434"
    temperature: float = 0.0
    api_key: Optional[str] = None
    
    # 🟢 NEW CONFIGURATIONS FOR LARGE DATASETS
    timeout: int = 360      # Increased default to 6 minutes
    num_ctx: int = 8192     # Increased context window for large inputs

    def _generate(self, messages: List[BaseMessage], stop: Optional[List[str]] = None, **kwargs: Any) -> ChatResult:
        # 1. Convert LangChain Messages to Ollama API Format
        ollama_messages = []
        for msg in messages:
            role = "user"
            if isinstance(msg, SystemMessage):
                role = "system"
            elif isinstance(msg, AIMessage):
                role = "assistant"
            
            ollama_messages.append({"role": role, "content": msg.content})

        # 2. Prepare Payload
        payload = {
            "model": self.model_name,
            "messages": ollama_messages,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_ctx": self.num_ctx  # 🟢 Pass context window size to API
            }
        }

        # 3. Define Headers
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        # 4. Execute with Retry Logic
        endpoint = f"{self.base_url}/api/chat"
        
        # Check Debug Mode
        debug_mode = os.environ.get("DEBUG_MODE", "False").lower() == "true"
        if debug_mode:
            last_msg = ollama_messages[-1]['content'] if ollama_messages else "No content"
            print(f"\n🧠 [LLM INPUT]: {last_msg[:200]}...\n")

        # 🟢 RETRY LOOP SETTINGS
        max_retries = 3
        backoff_seconds = 3 

        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    print(f"⚡ Retrying Request ({attempt+1}/{max_retries})...")
                else:
                    print(f"⚡ Sending REST Request to {self.model_name}...")

                # 🟢 USE SELF.TIMEOUT (360s)
                response = requests.post(endpoint, json=payload, headers=headers, timeout=self.timeout)
                response.raise_for_status() # Raises Error for 400, 401, 500, 503
                
                # 5. Parse Response
                result_json = response.json()
                content = result_json.get("message", {}).get("content", "")
                
                if debug_mode:
                    print(f"🤖 [LLM OUTPUT]: {content[:200]}...\n")
                
                # Success - Return Result
                generation = ChatGeneration(message=AIMessage(content=content))
                return ChatResult(generations=[generation])

            except requests.exceptions.RequestException as e:
                # 🟢 HANDLE FAILURES
                print(f"   ⚠️ LLM Connection Failed (Attempt {attempt+1}): {e}")
                
                if attempt < max_retries - 1:
                    print(f"   ⏳ Waiting {backoff_seconds}s before retry...")
                    time.sleep(backoff_seconds)
                else:
                    print("   ❌ Max retries reached. Service Unavailable.")
                    error_msg = f"Error: AI Analysis Unavailable after {max_retries} attempts. ({e})"
                    return ChatResult(generations=[ChatGeneration(message=AIMessage(content=error_msg))])
        
        # Fallback (Should not be reached due to loop logic, but safe to keep)
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content="Error: Unknown LLM Failure"))])

    @property
    def _llm_type(self) -> str:
        return "ollama-rest-custom"

def get_llm(model_type="reasoning"):
    """
    Factory function to return our custom REST-based LLM.
    """
    # Your API Key
    MY_OLLAMA_KEY = "b3bfd14261204ff2b1d2b4f36a1ecebb.3xPoI7VU9fetGthvocHnHrVs" 

    return OllamaRestChatModel(
        model_name="qwen3-coder:480b-cloud",
        base_url="http://localhost:11434",
        api_key=MY_OLLAMA_KEY,
        temperature=0.0,
        # 🟢 OVERRIDE DEFAULTS HERE
        timeout=360,      # 6 Minutes timeout
        num_ctx=8192      # Large context window for big Excel files
    )