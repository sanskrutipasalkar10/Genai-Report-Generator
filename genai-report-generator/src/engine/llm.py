import requests
import json
import os
import time
from typing import List, Optional, Any
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
from langchain_core.language_models import BaseChatModel
from langchain_core.outputs import ChatResult, ChatGeneration

class OllamaRestChatModel(BaseChatModel):
    """
    A Custom LangChain wrapper that uses the REST API (requests) directly.
    """
    model_name: str
    base_url: str = "http://localhost:11434"
    temperature: float = 0.0
    api_key: Optional[str] = None
    
    # Configuration for Large Datasets
    timeout: int = 360      
    num_ctx: int = 8192     

    def _generate(self, messages: List[BaseMessage], stop: Optional[List[str]] = None, **kwargs: Any) -> ChatResult:
        # 1. Convert LangChain Messages to Ollama API Format
        ollama_messages = []
        for msg in messages:
            role = "user"
            content = msg.content
            images = []

            # Handle Vision (Unwrap List if needed)
            if isinstance(content, list) and len(content) > 0 and isinstance(content[0], dict):
                content = content[0]

            # Check for Image Dict
            if isinstance(content, dict) and "image_base64" in content:
                text_part = content.get("text", "")
                img_part = content.get("image_base64")
                content = text_part
                if img_part:
                    images.append(img_part)

            if isinstance(msg, SystemMessage):
                role = "system"
            elif isinstance(msg, AIMessage):
                role = "assistant"
            
            msg_obj = {"role": role, "content": content}
            if images:
                msg_obj["images"] = images
            
            ollama_messages.append(msg_obj)

        # 2. Prepare Payload
        payload = {
            "model": self.model_name,
            "messages": ollama_messages,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_ctx": self.num_ctx
            }
        }

        # 3. Define Headers
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        # 4. Execute with Retry Logic
        # 🟢 CRITICAL FIX: Ensure this says '/api/chat'
        endpoint = f"{self.base_url}/api/chat"
        
        debug_mode = os.environ.get("DEBUG_MODE", "False").lower() == "true"
        if debug_mode:
            # Safe print (hide base64)
            debug_msgs = []
            for m in ollama_messages:
                dm = m.copy()
                if "images" in dm: dm["images"] = ["<BASE64_IMAGE_DATA>"]
                debug_msgs.append(dm)
            print(f"\n🧠 [LLM INPUT]: {str(debug_msgs)[:300]}...\n")

        max_retries = 3
        backoff_seconds = 3 

        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    print(f"⚡ Retrying Request ({attempt+1}/{max_retries})...")
                else:
                    # 🟢 DEBUG PRINT: This will confirm the URL in your console
                    print(f"⚡ Sending REST Request to {self.model_name} at {endpoint}...")

                response = requests.post(endpoint, json=payload, headers=headers, timeout=self.timeout)
                response.raise_for_status() 
                
                result_json = response.json()
                content = result_json.get("message", {}).get("content", "")
                
                if debug_mode:
                    print(f"🤖 [LLM OUTPUT]: {content[:200]}...\n")
                
                generation = ChatGeneration(message=AIMessage(content=content))
                return ChatResult(generations=[generation])

            except requests.exceptions.RequestException as e:
                print(f"   ⚠️ LLM Connection Failed (Attempt {attempt+1}): {e}")
                
                if attempt < max_retries - 1:
                    print(f"   ⏳ Waiting {backoff_seconds}s before retry...")
                    time.sleep(backoff_seconds)
                else:
                    print("   ❌ Max retries reached. Service Unavailable.")
                    return ChatResult(generations=[ChatGeneration(message=AIMessage(content=f"Error: {e}"))])
        
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content="Error: Unknown LLM Failure"))])

    @property
    def _llm_type(self) -> str:
        return "ollama-rest-custom"

# --- FACTORY FUNCTIONS ---

def get_llm():
    """Factory for Standard Reasoning/Text Analysis"""
    MY_OLLAMA_KEY = "b3bfd14261204ff2b1d2b4f36a1ecebb.3xPoI7VU9fetGthvocHnHrVs" 
    return OllamaRestChatModel(
        model_name="qwen3-coder:480b-cloud",
        base_url="http://localhost:11434",
        api_key=MY_OLLAMA_KEY,
        temperature=0.0,
        timeout=360,
        num_ctx=8192
    )

def get_vision_model():
    """Factory for Vision Model (Image Analysis)"""
    MY_OLLAMA_KEY = "b3bfd14261204ff2b1d2b4f36a1ecebb.3xPoI7VU9fetGthvocHnHrVs"
    return OllamaRestChatModel(
        model_name="qwen3-vl:235b-instruct-cloud", # Vision Model
        base_url="http://localhost:11434",
        api_key=MY_OLLAMA_KEY,
        temperature=0.1, 
        timeout=360,
        num_ctx=4096 
    )