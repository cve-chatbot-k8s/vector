# This is a sample Python script.
from embedding import VectorEmbeddingCreator
from transformers import AutoTokenizer
from embedding2 import VectorEmbeddingCreator2


def query_llm(model, query):
    tokenizer = AutoTokenizer.from_pretrained("gpt2")
    inputs = tokenizer.encode(query, return_tensors="pt")
    outputs = model.generate(inputs, max_length=50, num_return_sequences=1)
    return tokenizer.decode(outputs[0], skip_special_tokens=True)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    vec_creator = VectorEmbeddingCreator2()
    # vec_creator.store_embeddings_from_json()
    print("Below is the result of the query:")
    print(vec_creator.search_embeddings("What CVE id is associated with the Apache Struts vulnerability?"))
    vec_creator.close()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
