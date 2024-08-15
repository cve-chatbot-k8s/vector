from transformers import AutoTokenizer
from embedding import VectorEmbeddingCreator
from logger_config import logger


# Streamlit Chat Application
if __name__ == '__main__':
    vec_creator = VectorEmbeddingCreator()
    vec_creator.store_embeddings_from_json()
    vec_creator.close()
