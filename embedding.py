import os
import psycopg2
import json
import numpy as np
from psycopg2 import sql
from db import PostgresConnector
import torch
from transformers import AutoTokenizer, AutoModel
import warnings

warnings.filterwarnings("ignore")
class VectorEmbeddingCreator:
    def __init__(self):
        self.db_connector = PostgresConnector()
        self.db_connector.connect()

    def create_embedding(self, cve_json):
        # Example: Convert JSON to a vector (this is a placeholder, replace with actual embedding logic)
        tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
        model = AutoModel.from_pretrained("bert-base-uncased")
        data = json.dumps(cve_json)
        inputs = tokenizer(data, return_tensors='pt', max_length=512, truncation=True)
        with torch.no_grad():
            outputs = model(**inputs)
            # Use the last hidden state as the embedding (average across tokens for simplicity)
            embedding = torch.mean(outputs.last_hidden_state, dim=1).squeeze()
        print(embedding)
        return embedding.detach().numpy()

    def update_embedding(self, record_id, embedding):
        cursor = self.db_connector.connection.cursor()
        try:
            update_query = sql.SQL("""
                UPDATE cve.CVE_RECORDS
                SET embedding = %s
                WHERE id = %s
            """)
            cursor.execute(update_query, (embedding.tolist(), record_id))
            self.db_connector.connection.commit()
        except Exception as e:
            print(f"Error updating embedding: {e}")
            self.db_connector.connection.rollback()
        finally:
            cursor.close()

    def process_records(self):
        cursor = self.db_connector.connection.cursor()
        try:
            select_query = """
                SELECT id, cve_json 
                FROM cve.CVE_RECORDS 
                WHERE embedding IS NULL 
                AND date_updated <= CURRENT_DATE - INTERVAL '2 weeks' LIMIT 1
            """
            cursor.execute(select_query)
            records = cursor.fetchall()
            for record in records:
                record_id, cve_json = record
                embedding = self.create_embedding(cve_json)
                self.update_embedding(record_id, embedding)
        except Exception as e:
            print(f"Error processing records: {e}")
        finally:
            cursor.close()

    def close(self):
        self.db_connector.close()