from pathlib import Path
from uuid import uuid4
from langchain_chroma import Chroma
from langchain_aws import BedrockEmbeddings
from langchain_core.documents import Document
from langchain_community.document_loaders import WebBaseLoader

embeddings = BedrockEmbeddings()

vector_store = Chroma(
    collection_name="moya_docs",
    embedding_function=embeddings,
    persist_directory="/workspaces/moya/examples/hackathon_assistant/tools/chroma_langchain_db",  # Where the data is stored locally
)


# From the folder path /workspaces/moya/examples/hackathon_assistant/data/documentation, read all the markdown files
# and index them into the vector store
# DOCS_PATH = Path("/workspaces/moya/examples/hackathon_assistant/data/documentation")
# def read_docs():
#     for file in DOCS_PATH.glob("*.md"):
#         with open(file, "r") as f:
#             yield f.read()

# documents = []
# for content in read_docs():
#     documents.append(Document(content))

# uuids = [str(uuid4()) for _ in range(len(documents))]
# vector_store.add_documents(documents=documents, ids=uuids)



loader = WebBaseLoader(["https://staging.d29qp8i10iguz1.amplifyapp.com/explanations",
                        "https://staging.d29qp8i10iguz1.amplifyapp.com/guides",
                        "https://staging.d29qp8i10iguz1.amplifyapp.com/index",
                        "https://staging.d29qp8i10iguz1.amplifyapp.com/quickstart",
                        "https://staging.d29qp8i10iguz1.amplifyapp.com/reference",
                        "https://staging.d29qp8i10iguz1.amplifyapp.com/tutorials"])
loader.requests_per_second = 1
docs = loader.load()
vector_store.add_documents(documents=docs)

