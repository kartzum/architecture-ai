import os
import argparse
import logging
from pathlib import Path
from typing import List

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import TextLoader
from langchain_core.documents import Document

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_text_files(directory: str) -> List[Document]:
    documents = []
    txt_files = list(Path(directory).glob("**/*.txt"))

    if not txt_files:
        logger.warning(f"No .txt files found in {directory}")
        return documents

    logger.info(f"Found {len(txt_files)} .txt files")

    for txt_file in txt_files:
        try:
            loader = TextLoader(str(txt_file), encoding='utf-8')
            file_docs = loader.load()
            for doc in file_docs:
                doc.metadata["source"] = str(txt_file.relative_to(directory))
            documents.extend(file_docs)
            logger.info(f"Loaded {txt_file}")
        except Exception as e:
            logger.error(f"Error loading {txt_file}: {e}")

    return documents


def create_faiss_index(
        input_dir: str,
        output_dir: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
):
    logger.info(f"Loading text files from {input_dir}")
    documents = load_text_files(input_dir)

    if not documents:
        logger.error("No documents to process. Exiting.")
        return

    logger.info(f"Splitting {len(documents)} documents into chunks")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", " ", ""]
    )

    chunks = text_splitter.split_documents(documents)
    logger.info(f"Created {len(chunks)} chunks from documents")

    logger.info("Creating embeddings using 'all-MiniLM-L6-v2'")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )

    logger.info("Creating FAISS vector store")
    vectorstore = FAISS.from_documents(chunks, embeddings)

    logger.info(f"Saving FAISS index to {output_dir}")
    vectorstore.save_local(output_dir)

    metadata = {
        "num_documents": len(documents),
        "num_chunks": len(chunks),
        "chunk_size": chunk_size,
        "chunk_overlap": chunk_overlap,
        "embedding_model": "all-MiniLM-L6-v2",
        "files_indexed": [doc.metadata.get("source", "unknown") for doc in documents]
    }

    import json
    metadata_path = os.path.join(output_dir, "index_metadata.json")
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"Index saved successfully to {output_dir}")
    logger.info(f"Index contains {len(chunks)} chunks from {len(documents)} documents")


def main():
    parser = argparse.ArgumentParser(description="Create FAISS index from text files")
    parser.add_argument("--input-dir", type=str, required=True,
                        help="Directory containing .txt files")
    parser.add_argument("--output-dir", type=str, required=True,
                        help="Directory to save the FAISS index")
    parser.add_argument("--chunk-size", type=int, default=1000,
                        help="Size of text chunks (default: 1000)")
    parser.add_argument("--chunk-overlap", type=int, default=200,
                        help="Overlap between chunks (default: 200)")

    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    create_faiss_index(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap
    )


if __name__ == "__main__":
    main()
