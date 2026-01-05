from langchain_community.embeddings import OllamaEmbeddings
import yaml
from pathlib import Path

CONFIG_PATH = Path(__file__).parent.parent.parent / "config/settings.yaml"
with open(CONFIG_PATH) as f:
    config = yaml.safe_load(f)

def get_embedding_model():
    """Returns the Nomic embedding interface"""
    return OllamaEmbeddings(
        model=config['embeddings']['model_name'],
        base_url=config['embeddings']['base_url']
    )