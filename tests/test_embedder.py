import numpy as np

from backend.rag.embedder import embed_texts


def _cosine_sim(a, b):
    a, b = np.array(a), np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def test_embed_texts_returns_correct_shape():
    vectors = embed_texts(["Hello world", "Another sentence"])
    assert len(vectors) == 2
    assert len(vectors[0]) == 384
    assert len(vectors[1]) == 384


def test_embed_texts_captures_semantic_similarity():
    vectors = embed_texts(
        [
            "The pharmacy owner was arrested.",
            "Police arrested the pharmacy owner.",
            "The weather is sunny today.",
        ]
    )
    similar_score = _cosine_sim(vectors[0], vectors[1])
    unrelated_score = _cosine_sim(vectors[0], vectors[2])

    assert similar_score > unrelated_score
    assert similar_score > 0.7
