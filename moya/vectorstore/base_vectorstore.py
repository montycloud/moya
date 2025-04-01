import abc
from typing import List, Dict


class BaseVectorStore(abc.ABC):
    """
    Abstract interface for storing and retrieving vectors.
    Implements the Singleton pattern to ensure only one instance exists.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(BaseVectorStore, cls).__new__(cls)
        return cls._instance

    @abc.abstractmethod
    def create_vectorstore(self, directory: str) -> None:
        """
        Create a new vectorstore in the specified directory.
        """
        pass

    @abc.abstractmethod
    def add_vector(self, chunks: List[Dict]) -> None:
        """
        Add a new vector to the vectorstore.
        """
        pass

    @abc.abstractmethod
    def load_vectorstore(self, path: str) -> None:
        """
        Load a vectorstore from the specified path.
        """
        pass

    @abc.abstractmethod
    def search_vectorstore(self, query: str, top_k: int = 2) -> List[Dict]:
        """
        Search the vectorstore for the most relevant vectors.
        """
        pass

    @abc.abstractmethod
    def delete_vectorstore(self, path: str) -> None:
        """
        Delete the vectorstore at the specified path.
        """
        pass
