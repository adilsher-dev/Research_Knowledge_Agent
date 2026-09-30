from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

model = SentenceTransformer("all-MiniLM-L6-v2")

text1 = "Generative AI can create new content."
text2 = "Artificial intelligence can generate new content."
text3 = "The weather is very hot today."

embedding1 = model.encode([text1])
embedding2 = model.encode([text2])
embedding3 = model.encode([text3])

similarity_1_2 = cosine_similarity(
    embedding1,
    embedding2
)[0][0]

similarity_1_3 = cosine_similarity(
    embedding1,
    embedding3
)[0][0]

print("Similarity between text 1 and text 2:", similarity_1_2)
print("Similarity between text 1 and text 3:", similarity_1_3)