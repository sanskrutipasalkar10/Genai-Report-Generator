from functools import lru_cache
# 🟢 UPDATED: Modern Import
from langchain_ollama import ChatOllama 
import yaml
from pathlib import Path

# Load config once
CONFIG_PATH = Path(__file__).parent.parent.parent / "config/settings.yaml"
with open(CONFIG_PATH) as f:
    config = yaml.safe_load(f)

@lru_cache(maxsize=4)
def get_llm(model_type="reasoning"):
    """
    Factory to get the correct LLM instance.
    args:
        model_type: 'reasoning' (Llama3) or 'extraction' (Llama3)
    """
    model_name = config['llm']['reasoning_model']
    
    print(f"🔌 Connecting to Local LLM: {model_name}")
    
    llm = ChatOllama(
        model=model_name,
        base_url=config['llm']['base_url'],
        temperature=config['llm']['temperature'],
        keep_alive="5m"
    )
    return llm