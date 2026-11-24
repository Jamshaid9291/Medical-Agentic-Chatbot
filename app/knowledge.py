# from functools import lru_cache
# from pinecone import Pinecone, ServerlessSpec
# from openai import OpenAI
# from app.config import settings

# @lru_cache()
# def clients():
#     if not settings.openai_api_key or not settings.pinecone_api_key:
#         raise ValueError("OpenAI and Pinecone API keys must be set in the environment variables.")
#     return OpenAI(api_key=settings.openai_api_key), Pinecone(api_key=settings.pinecone_api_key)


# def ensure_index():
#     _, pc = clients()
#     if not pc.has_index(settings.pinecone_index):
#         pc.create_index(name=settings.pinecone_index, dimension=1536, metric='cosine', spec=ServerlessSpec(cloud='aws', region='us-east-1'))
#     return pc.Index(settings.pinecone_index)


# def embed(texts):
#     ai, _ = clients()
#     return [x.embedding for x in ai.embeddings.create(model=settings.openai_embed_model, input=texts).data]



# def search_kb(query, top_k=5):
#     index = ensure_index()
#     vector = embed([query])[0]
#     result = index.query(vector=vector, top_k=top_k, include_metadata=True)
#     return [{'page': m.metadata.get('page'), 'text': m.metadata.get('text',''), 'score': round(m.score,3), 'source': 'Gale Encyclopedia (2002)'} for m in result.matches if m.score >= 0.30]



from functools import lru_cache

from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer

from app.config import settings


# all-MiniLM-L6-v2 produces 384-dimensional embeddings
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384


@lru_cache()
def clients():
    if not settings.pinecone_api_key:
        raise ValueError(
            "Pinecone API key must be set in environment variables."
        )

    return Pinecone(api_key=settings.pinecone_api_key)


@lru_cache()
def embedding_model():
    return SentenceTransformer(EMBEDDING_MODEL)


def ensure_index():
    pc = clients()

    if not pc.has_index(settings.pinecone_index):
        pc.create_index(
            name=settings.pinecone_index,
            dimension=EMBEDDING_DIMENSION,
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            )
        )

    return pc.Index(settings.pinecone_index)


def embed(texts):
    model = embedding_model()

    vectors = model.encode(
        texts,
        normalize_embeddings=True,
        convert_to_numpy=True
    )

    return vectors.tolist()


def search_kb(query, top_k=5):
    index = ensure_index()

    vector = embed([query])[0]

    result = index.query(
        vector=vector,
        top_k=top_k,
        include_metadata=True
    )

    return [
        {
            "page": m.metadata.get("page"),
            "text": m.metadata.get("text", ""),
            "score": round(m.score, 3),
            "source": "Gale Encyclopedia (2002)"
        }
        for m in result.matches
        if m.score >= 0.30
    ]
