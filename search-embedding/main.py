from embedding import VectorEmbeddingCreator
import streamlit as st
from streamlit_chat import message 
from logger_config import logger

# Streamlit Chat Application
if __name__ == '__main__':
    vec_creator = VectorEmbeddingCreator()
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
            st.session_state.responses.append(f"{result}")
        else:
            st.session_state.responses.append("Sorry, I couldn't find any relevant CVE information.")


    # Display the last 3 messages in the chat history
    start_index = max(0, len(st.session_state['responses']) - 3)

    for i in range(start_index, len(st.session_state['responses'])):
        message(st.session_state['responses'][i], key=str(i))
        if i < len(st.session_state['requests']):
            message(st.session_state["requests"][i], is_user=True, key=str(i) + '_user')
