_default_embedding = None


def get_default_embedding():
    global _default_embedding

    if _default_embedding is not None:
        return _default_embedding

    try:
        from openai import OpenAI

        from .openai import OpenAIEmbedding

        _default_embedding = OpenAIEmbedding(client=OpenAI(), model="text-embedding-ada-002")

        return _default_embedding
    except ImportError:
        pass

    # Try fastembed too

    raise ValueError("Please setup openai or fastembed library to use embeddings")
