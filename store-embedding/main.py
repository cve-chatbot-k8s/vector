from transformers import AutoTokenizer
from embedding import VectorEmbeddingCreator
from logger_config import logger
import requests


def send_post_request():
    url = "http://localhost:15020/quitquitquit"
    try:
        response = requests.post(url)
        if response.status_code == 200:
            logger.info("POST request to /quitquitquit was successful.")
        else:
            logger.error(f"POST request to /quitquitquit failed with status code: {response.status_code}")
    except Exception as e:
        logger.error(f"An error occurred while making the POST request: {e}")


# Streamlit Chat Application
if __name__ == '__main__':
    vec_creator = VectorEmbeddingCreator()
    vec_creator.store_embeddings_from_json()
    vec_creator.close()
    logger.info("Embeddings stored successfully.")
    logger.info("Calling Istio proxy to quit the application.")
    send_post_request()
