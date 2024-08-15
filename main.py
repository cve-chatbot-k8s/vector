from embedding2 import VectorEmbeddingCreator2
import streamlit as st
from logger_config import logger
from streamlit_chat import message



# Press the green button in the gutter to run the script.
# if __name__ == '__main__':
#     logger.info("Starting CVE Search Engine application")
#     vec_creator = VectorEmbeddingCreator2()
#     st.title("CVE Search Engine")
#     st.write("Enter your query to search for CVE information:")
#     user_query = st.text_input("Query:")
#
#     if st.button("Search"):
#         if user_query:
#             logger.info(f"User query received: {user_query}")
#             # Call the search_embeddings function
#             result = vec_creator.search_embeddings(user_query)
#             # Display the result
#             st.write("Result:", result)
#         else:
#             st.write("Please enter a query.")
#
#     # vec_creator.store_embeddings_from_json()
#     # print("Below is the result of the query:")
#     # print(vec_creator.search_embeddings("What CVE id is associated with the Apache Struts vulnerability?"))
#     vec_creator.close()


if __name__ == '__main__':
    vec_creator = VectorEmbeddingCreator2()
    st.title("CVE Search Engine Chat")
    logger.info("Starting CVE Search Engine application")
    # Initialize chat history
    if 'responses' not in st.session_state:
        st.session_state['responses'] = ["How can I assist you with CVE information?"]

    if 'requests' not in st.session_state:
        st.session_state['requests'] = []

    # User input section
    user_input = st.text_input("Query:")

    # Handle user query
    if st.button("Send") and user_input:
        logger.info(f"User query received: {user_input}")
        # Store user query in session
        st.session_state.requests.append(user_input)

        # Call the search_embeddings function
        result = vec_creator.search_embeddings(user_input)

        # Generate a response
        if result:
            st.session_state.responses.append(f"Result found: {result}")
        else:
            st.session_state.responses.append("Sorry, I couldn't find any relevant CVE information.")

    # Display chat history
    for i in range(len(st.session_state['responses'])):
        message(st.session_state['responses'][i], key=str(i))
        if i < len(st.session_state['requests']):
            message(st.session_state["requests"][i], is_user=True, key=str(i) + '_user')