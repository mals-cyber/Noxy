from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

class ChromaEmbedWrapper:
    def __init__(self):
        self.model = DefaultEmbeddingFunction()

    def embed_documents(self, texts):
        return self.model(texts)

    def embed_query(self, text):
        return self.model([text])[0]


embedding_model = ChromaEmbedWrapper()
