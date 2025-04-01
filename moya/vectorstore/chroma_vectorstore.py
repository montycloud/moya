from moya.vectorstore.base_vectorstore import BaseVectorStore
# from chromadb import Client as ChromaClient
from chromadb import PersistentClient as ChromaPersistentClient
from typing import List, Dict, Callable


class ChromaVectorStore(BaseVectorStore):
    """
    ChromaVectorStore is a concrete implementation of BaseVectorStore
    that uses the ChromaDB as its backend for storing and retrieving vectors.
    """

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(ChromaVectorStore, cls).__new__(cls)
        return cls._instance

    def __init__(self, path: str, collection_name: str, embedding_function: Callable[[str], List[float]]):
        super().__init__()
        self.embedding_function = embedding_function
        self.client = ChromaPersistentClient(path=path)
        self.collection = None
        self.create_vectorstore(collection_name)
        self.load_vectorstore(collection_name)
        print("Created a new vectorstore")

    def create_vectorstore(self, name: str) -> None:
        """
        Create a new vectorstore in the specified path.
        """
        self.collection = self.client.get_or_create_collection(name=name)
        print(f"Vectorstore created at {name}")

    def load_vectorstore(self, name: str) -> None:
        """
        Load an existing vectorstore from the specified path.
        """
        if not self.collection:
            self.collection = self.client.get_or_create_collection(name=name)
            print(f"Loaded vectorstore from {name}")

    def add_vectors(self, chunks: List[Dict]) -> None:
        """
        Add new vectors to the vectorstore.
        """
        for chunk in chunks:
            self.add_vector(chunk)
        print(f"Added {len(chunks)} vectors to the vectorstore.")

    def add_vector(self, chunk: Dict) -> None:
        """
        Add a single vector to the vectorstore.
        """
        embedding = self.embedding_function(chunk['document'])
        self.collection.add(
            documents=[chunk['document']],
            metadatas=[chunk['metadata']],
            ids=[chunk['id']],
            embeddings=[embedding]
        )

    def search_vectorstore(self, query: str, top_k: int = 2) -> List[Dict]:
        """
        Search the vectorstore for the most relevant vectors.
        """
        embedding = self.embedding_function(query)
        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=top_k,
            
        )
        # Convert results to a more user-friendly format
        formatted_results = []
        for ind in range(len(results['documents'][0])):
            # doc, metadata, score in zip(results['documents'], results['metadatas'], results['distances']):
            document = {
                'content': results['documents'][0][ind],
                'metadata': results['metadatas'][0][ind],
                'score': results['distances'][0][ind]
            }
            formatted_results.append(document)
        return formatted_results

    def delete_vectorstore(self, path: str) -> None:
        """
        Delete the vectorstore at the specified path.
        """
        self.client.delete_collection(name=path)
        print(f"Deleted vectorstore at {path}")
