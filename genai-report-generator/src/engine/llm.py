import requests
import json
import os
from typing import List, Optional, Any
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
from langchain_core.language_models import BaseChatModel
from langchain_core.outputs import ChatResult, ChatGeneration

class OllamaRestChatModel(BaseChatModel):
    """
    A Custom LangChain wrapper that uses the REST API (requests) directly.
    This bypasses auth issues in standard libraries by allowing full header control.
    """
    model_name: str
    base_url: str = "http://localhost:11434"
    temperature: float = 0.0
    api_key: Optional[str] = None

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

        # 2. Prepare Payload (Like in the Notebook)
        payload = {
            "model": self.model_name,
            "messages": ollama_messages,
            "stream": False,  # We want the full response at once for agents
            "options": {
                "temperature": self.temperature
            }
        }

        # 3. Define Headers (Inject Key if exists)
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        # 4. Send Request (The REST API Call)
        endpoint = f"{self.base_url}/api/chat"
        
        try:
            print(f"⚡ Sending REST Request to {self.model_name}...")
            response = requests.post(endpoint, json=payload, headers=headers, timeout=120)
            response.raise_for_status() # Raise error for 401/500
            
            # 5. Parse Response
            result_json = response.json()
            content = result_json.get("message", {}).get("content", "")
            
            # 6. Return as LangChain Result
            generation = ChatGeneration(message=AIMessage(content=content))
            return ChatResult(generations=[generation])

        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP Error {e.response.status_code}: {e.response.text}"
            print(f"❌ {error_msg}")
            # Return a safe fallback message so the app doesn't crash completely
            return ChatResult(generations=[ChatGeneration(message=AIMessage(content=f"Error: {error_msg}"))])
        except Exception as e:
            print(f"❌ Request Failed: {e}")
            return ChatResult(generations=[ChatGeneration(message=AIMessage(content=f"Error: {str(e)}"))])

    @property
    def _llm_type(self) -> str:
        return "ollama-rest-custom"

def get_llm(model_type="reasoning"):
    """
    Factory function to return our custom REST-based LLM.
    """
    # 🟢 PASTE YOUR KEY HERE (Using the key you provided)
    # This ensures it is sent in the headers just in case localhost requires it.
    MY_OLLAMA_KEY = "b3bfd14261204ff2b1d2b4f36a1ecebb.3xPoI7VU9fetGthvocHnHrVs" 

    return OllamaRestChatModel(
        model_name="qwen3-coder:480b-cloud", # Matches your pulled model
        base_url="http://localhost:11434",
        api_key=MY_OLLAMA_KEY,
        temperature=0.0
    )