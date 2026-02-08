import os
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# Load the index
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={'device': 'cpu'},
    encode_kwargs={'normalize_embeddings': True}
)

vectorstore = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)

print("")
query = "Who is Xeen Cloudrunner?"
print(query)
docs = vectorstore.similarity_search(query, k=3)
print(f"Found {len(docs)} relevant documents")
for i, doc in enumerate(docs):
    print(f"\nDocument {i + 1}:")
    print(f"Source: {doc.metadata.get('source', 'unknown')}")
    print(f"Content: {doc.page_content[:200]}...")
