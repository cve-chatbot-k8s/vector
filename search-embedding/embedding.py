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
        # connection_string = "postgresql+psycopg://cve_user:password1234@localhost:5432/cve"
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
    # def generate_doc_chain(self, cve_json_list, user_input):
    #         """Generate a response for the user based on the list of CVE JSON data."""
    #         # Load the LLM
    #         llm = ChatOpenAI(model_name="gpt-3.5-turbo")

    #         # Convert JSON objects to Document objects
    #         documents = [Document(page_content=json.dumps(cve_json), metadata={}) for cve_json in cve_json_list]

    #         # Define the template with placeholders
    #         template = """
    #         You are an assistant for question-answering tasks.
    #         Use the provided context only to answer the following question:

    #         <context>
    #         {context}
    #         </context>

    #         Question: {user_input}
    #         """

    #         # Create the prompt template
    #         prompt = ChatPromptTemplate.from_template(template)

    #         # Generate the doc_chain
    #         doc_chain = create_stuff_documents_chain(llm, prompt)

    #         # Invoke the chain with the list of Document objects and user input
    #         response = doc_chain.invoke({"context": documents, "user_input": user_input})

    #         return response

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

        print(cve_json_list[0])

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

        temp = json.dumps(self.sample_json())

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

    def create_user_embedding(self, user_data):
        embedding = self.embedding_model.embed_query(user_data)
        return np.array(embedding)

    def close(self):
        """Close the database connection."""
        self.db_connector.close()
