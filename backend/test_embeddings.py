from fastembed import TextEmbedding
import numpy as np


model = TextEmbedding(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)


def cosine_similarity(a, b):
    a = np.asarray(a)
    b = np.asarray(b)

    return np.dot(a, b) / (
        np.linalg.norm(a) * np.linalg.norm(b)
    )


texts = [
    "RAG combines retrieval with language models.",
    "Retrieval augmented generation uses external knowledge.",
    "The weather is sunny today."
]

embeddings = list(model.embed(texts))

similarity_1 = cosine_similarity(
    embeddings[0],
    embeddings[1]
)

similarity_2 = cosine_similarity(
    embeddings[0],
    embeddings[2]
)

print("Embedding dimension:", len(embeddings[0]))
print("Related similarity:", similarity_1)
print("Unrelated similarity:", similarity_2)