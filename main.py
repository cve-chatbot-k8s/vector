from embedding import VectorEmbeddingCreator
from transformers import AutoTokenizer
from embedding2 import VectorEmbeddingCreator2
import streamlit as st


def query_llm(model, query):
    tokenizer = AutoTokenizer.from_pretrained("gpt2")
    inputs = tokenizer.encode(query, return_tensors="pt")
    outputs = model.generate(inputs, max_length=50, num_return_sequences=1)
    return tokenizer.decode(outputs[0], skip_special_tokens=True)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    vec_creator = VectorEmbeddingCreator2()
    st.title("CVE Search Engine")
    st.write("Enter your query to search for CVE information:")
    user_query = st.text_input("Query:")

    if st.button("Search"):
        if user_query:
            # Call the search_embeddings function
            result = vec_creator.search_embeddings(user_query)
            # Display the result
            st.write("Result:", result)
        else:
            st.write("Please enter a query.")

    # vec_creator.store_embeddings_from_json()
    # print("Below is the result of the query:")
    # print(vec_creator.search_embeddings("What CVE id is associated with the Apache Struts vulnerability?"))
    vec_creator.close()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
