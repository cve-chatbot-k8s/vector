import os
import json
import numpy as np
# import torch
# from psycopg import sql
# from transformers import AutoTokenizer, AutoModel
import logging
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
from logger_config import logger
# import openai

warnings.filterwarnings("ignore")


class VectorEmbeddingCreator2:
    def __init__(self):
        # Connect to the PostgreSQL database
        self.db_connector = PostgresConnector()
        self.db_connector.connect()
        connection_string = f"postgresql+psycopg://{self.db_connector.user}:{self.db_connector.password}@{self.db_connector.host}:5432/{self.db_connector.database}"
        logger.info(f"Connection string: {connection_string}")
        # connection_string = "postgresql+psycopg://cve_user:password1234@localhost:5432/cve"
        print(connection_string)
        # Initialize LangChain's HuggingFaceEmbeddings wrapper
        self.embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        try:
            logger.info("Connecting to PostgreSQL DB")
            self.vectorstore = PGVector(
                connection=connection_string,
                embeddings=self.embedding_model,
                collection_name="cve.vector",
                use_jsonb=True,
            )
        except Exception as e:
            logger.error(f"Error initializing PGVector: {e}")
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
                WHERE embedding IS NULL 
                AND date_published >= current_date - interval '1 month' LIMIT 10
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
            # update_query = sql.SQL("""
            #     UPDATE cve.CVE_RECORDS
            #     SET embedding = %s
            #     WHERE id = %s
            # """)
            # cursor.execute(update_query, (embedding.tolist(), record_id))
            self.vectorstore.add_embeddings([record_id], [embedding])
            # self.db_connector.connection.commit()
        except Exception as e:
            print(f"Error updating embedding: {e}")
            # self.db_connector.connection.rollback()
        finally:
            cursor.close()

    def search_embeddings(self, user_input, top_k=5):
        """Search the database for embeddings similar to the user's input."""
        # user_embedding = self.create_user_embedding(user_input).tolist()
        # retriever = self.vectorstore.as_retriever()
        retriever = self.vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 1})
        result = retriever.invoke(user_input)
        print(result)
        # Fetch the CVE JSON data for each document_id
        cve_json_list = []
        cursor = self.db_connector.connection.cursor()
        try:
            for r in result:
                document_id = r.page_content  # The document ID stored in page_content
                cursor.execute("SELECT cve_json FROM cve.CVE_RECORDS WHERE id = %s", (document_id,))
                row = cursor.fetchone()
                if row:
                    cve_json_list.append(row[0])
        except Exception as e:
            print(f"Error fetching CVE records: {e}")
        finally:
            cursor.close()
        logger.info(f"Found the following CVE JSON data: {cve_json_list}")

        # system_prompt = (
        #     "You are an assistant for question-answering tasks. "
        #     "You will be provided with a context which will be a list of CVE JSON data"
        #     "And a User Input which will be a question. You have to answer "
        #     "the question solely based on the context provided. You have to go through the CVE JSON list and"
        #     "find a suitable answer to the question."
        #     "If you don't know the answer, say that you "
        #     "don't know. Use maximum of 5 sentences Keep the "
        #     "answer concise. Don't reply to any questions that are not related to the context."
        #     "\n\n"
        #     "{context}"
        # )

        system_prompt = (
            "You are an assistant for question-answering tasks. "
            "Provide concise answers based on given CVE JSON data. For each question, you will be provided with a "
            "list of CVE JSON data and a user-input question. Please answer the question by searching the CVE JSON "
            "list and use a maximum of 5 sentences. "
            "Additionally, you will only respond to questions directly related to the provided context. Keep "
            "your answers accurate and clear. Your answers should be based only on the provided knowledge base "
            "\n\n"
            "There can be several types of questions a user can ask and the expected answers are:"
            "What is the CVE ID of a specific vulnerability related to a product?"
            "Answer: CVE-2024-6896 which is present in the json data in the cveMetadata.cveId field"
            "What is the severity of a specific vulnerability related to a product? "
            "Answer: MEDIUM"
            "What is the description of a specific vulnerability related to a product? "
            "Answer: The AMP for WP – Accelerated Mobile Pages plugin for WordPress is vulnerable to Stored "
            "Cross-Site Scripting via SVG File uploads in all versions up to, and including,"
            "What is the solution of a specific vulnerability related to a product? "
            "Answer: Update to version"
            "What is the provider metadata of a specific vulnerability related to a product? "
            "Answer: Wordfence"
            "What is the date updated of a specific vulnerability related to a product? "
            "Answer: 2024-07-24T11:00:09.141Z"
            "What is the reference of a specific vulnerability related to a product? "
            "Answer: https://www.wordfence.com/threat-intel/vulnerabilities/id/b0a5fdb9-4e36-43ce-88ce-cd75bb1d1e25"
            "?source=cve"
            "What is the affected product of a specific vulnerability related to a product? "
            "Answer: AMP for WP – Accelerated Mobile Pages"
            "What is the affected version of a specific vulnerability related to a product? "
            "Answer: *"
            "What is the CWE ID of a specific vulnerability related to a product? "
            "Answer: CWE-79"
            "What is the CWE description of a specific vulnerability related to a product? "
            "Answer: CWE-79 Improper Neutralization of Input During Web Page Generation ('Cross-site Scripting')"
            "What is the credit of a specific vulnerability related to a product? "
            "Answer: wesley"
            "What is the credit type of a specific vulnerability related to a product? "
            "Answer: finder"
            "What is the credit value of a specific vulnerability related to a product? "
            "Answer: wesley"
            "What is the timeline of a specific vulnerability related to a product? "
            "Answer: 2024-07-23T21:41:54.000+00:00"
            "\n\n"
            "{context}"
        )

        llm = ChatOpenAI(model="gpt-3.5-turbo")
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                ("human", "{input}"),
            ]
        )
        question_answer_chain = create_stuff_documents_chain(llm, prompt)
        rag_chain = create_retrieval_chain(retriever, question_answer_chain)
        response = rag_chain.invoke({"input": user_input, "context": cve_json_list})
        print(response["answer"])
        # # Generate a response for the user based on the fetched CVE JSON data
        # doc_chain = self.generate_doc_chain(cve_json_list, user_input)
        # chain = create_retrieval_chain(results, doc_chain)
        # response = chain.invoke(user_input)
        # print(response)
        return response["answer"]

    def sample_json(self):
        """Sample JSON data for testing."""
        cve_json = {
            "dataType": "CVE_RECORD",
            "containers": {
                "cna": {
                    "title": "AMP for WP – Accelerated Mobile Pages <= 1.0.96.1 - Authenticated (Author+) Stored "
                             "Cross-Site Scripting via SVG File Upload",
                    "credits": [
                        {
                            "lang": "en",
                            "type": "finder",
                            "value": "wesley"
                        }
                    ],
                    "metrics": [
                        {
                            "cvssV3_1": {
                                "version": "3.1",
                                "baseScore": 6.4,
                                "baseSeverity": "MEDIUM",
                                "vectorString": "CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:C/C:L/I:L/A:N"
                            }
                        }
                    ],
                    "affected": [
                        {
                            "vendor": "mohammed_kaludi",
                            "product": "AMP for WP – Accelerated Mobile Pages",
                            "versions": [
                                {
                                    "status": "affected",
                                    "version": "*",
                                    "versionType": "semver",
                                    "lessThanOrEqual": "1.0.96.1"
                                }
                            ],
                            "defaultStatus": "unaffected"
                        }
                    ],
                    "timeline": [
                        {
                            "lang": "en",
                            "time": "2024-07-23T21:41:54.000+00:00",
                            "value": "Disclosed"
                        }
                    ],
                    "references": [
                        {
                            "url": "https://www.wordfence.com/threat-intel/vulnerabilities/id/b0a5fdb9-4e36-43ce-88ce-cd75bb1d1e25?source=cve"
                        },
                        {
                            "url": "https://plugins.trac.wordpress.org/browser/accelerated-mobile-pages/tags/1.0.96.1/templates/features.php#L7159"
                        },
                        {
                            "url": "https://wordpress.org/plugins/accelerated-mobile-pages/#developers"
                        },
                        {
                            "url": "https://plugins.trac.wordpress.org/changeset/3123278/"
                        }
                    ],
                    "descriptions": [
                        {
                            "lang": "en",
                            "value": "The AMP for WP – Accelerated Mobile Pages plugin for WordPress is vulnerable to Stored Cross-Site Scripting via SVG File uploads in all versions up to, and including, 1.0.96.1 due to insufficient input sanitization and output escaping. This makes it possible for authenticated attackers, with Author-level access and above, to inject arbitrary web scripts in pages that will execute whenever a user accesses the SVG file."
                        }
                    ],
                    "problemTypes": [
                        {
                            "descriptions": [
                                {
                                    "lang": "en",
                                    "type": "CWE",
                                    "cweId": "CWE-79",
                                    "description": "CWE-79 Improper Neutralization of Input During Web Page Generation ('Cross-site Scripting')"
                                }
                            ]
                        }
                    ],
                    "providerMetadata": {
                        "orgId": "b15e7b5b-3da4-40ae-a43c-f7aa60e62599",
                        "shortName": "Wordfence",
                        "dateUpdated": "2024-07-24T11:00:09.141Z"
                    }
                }
            },
            "cveMetadata": {
                "cveId": "CVE-2024-6896",
                "state": "PUBLISHED",
                "dateUpdated": "2024-07-24T11:00:09.141Z",
                "dateReserved": "2024-07-18T20:45:33.149Z",
                "assignerOrgId": "b15e7b5b-3da4-40ae-a43c-f7aa60e62599",
                "datePublished": "2024-07-24T11:00:09.141Z",
                "assignerShortName": "Wordfence"
            },
            "dataVersion": "5.1"
        }
        return cve_json

    def create_user_embedding(self, user_data):
        embedding = self.embedding_model.embed_query(user_data)
        return np.array(embedding)

    def close(self):
        """Close the database connection."""
        self.db_connector.close()
