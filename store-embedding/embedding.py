import os
import json
import numpy as np
import torch
from psycopg import sql
from transformers import AutoTokenizer, AutoModel

from db import PostgresConnector
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_postgres.vectorstores import PGVector
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.chat_models import ChatOpenAI
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
import warnings
from langchain.docstore.document import Document
from openai import OpenAI
import openai

warnings.filterwarnings("ignore")


class VectorEmbeddingCreator:
    def __init__(self):
        # Connect to the PostgreSQL database
        self.db_connector = PostgresConnector()
        self.db_connector.connect()
        connection_string = f"postgresql+psycopg://{self.db_connector.user}:{self.db_connector.password}@{self.db_connector.host}:5432/{self.db_connector.database}"
        print(connection_string)
        # Initialize LangChain's HuggingFaceEmbeddings wrapper
        self.embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

        try:
            self.vectorstore = PGVector(
                connection=connection_string,
                embeddings=self.embedding_model,
                collection_name="cve.vector",
                use_jsonb=True,
            )
        except Exception as e:
            print(f"Error initializing PGVector: {e}")
        print("Connection to PostgreSQL DB successful")

    def extract_meaningful_data(self, cve_json):
        """Extract meaningful data from JSON using OpenAI model."""
        # Create a prompt for the GPT-3.5 model
        prompt = (
            f"From the given CVE JSON Data extract meaningful data and Write the Data in NATURAL SENTENCES. The Output data should include a summary of the CVE ID, Severity metric which will be "
            f"present in the metrics object, the affected product, the solution, the description, Provider metadata, date Updated and the Reference. Common "
            f"Vulnerabilities and Exposures Records are structured data that describes a cybersecurity "
            f"vulnerability and is associated with a CVE ID. The Output Should Only contain the extracted data and it"
            f"should not contain any sentence similar to Here is the extracted meaningful data from the "
            f"provided CVE JSON data. Write the data in natural sentences and not in JSON format"
            f"Here is the JSON data:\n{json.dumps(cve_json)}")
        client = OpenAI(
            # This is the default and can be omitted
            api_key=os.environ.get("OPENAI_API_KEY"),
        )
        # Make a request to the OpenAI API using the gpt-3.5-turbo model
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system",
                 "content": "You are an assistant who can help extract and summarize data from JSON."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.7,
        )

        message_content = response.choices[0].message.content.strip()
        print(f"Extracted data: {message_content}")
        return message_content

    def create_embedding(self, cve_json):
        data = self.extract_meaningful_data(cve_json)
        embedding = self.embedding_model.embed_query(data)
        return np.array(embedding)

    def store_embeddings_from_json(self):
        """Process records that do not yet have embeddings and update them in the database."""
        cursor = self.db_connector.connection.cursor()
        try:
            select_query = """
                SELECT id, cve_json 
                FROM cve.CVE_RECORDS 
                WHERE date_published >= current_date - interval '1 month' LIMIT 30;
            """
            cursor.execute(select_query)
            records = cursor.fetchall()
            for record in records:
                record_id, cve_json = record
                text_data = json.dumps(cve_json)
                embedding = self.create_embedding(text_data)
                self.update_embedding(record_id, embedding)
        except Exception as e:
            print(f"Error processing records: {e}")
        finally:
            cursor.close()

    def update_embedding(self, record_id, embedding):
        """Update the database with the generated embedding for a given record."""
        cursor = self.db_connector.connection.cursor()
        try:            
            self.vectorstore.add_embeddings([record_id], [embedding])
        except Exception as e:
            print(f"Error updating embedding: {e}")
        finally:
            cursor.close()

    def close(self):
        """Close the database connection."""
        self.db_connector.close()
