import logging
import time
import os

from langchain_classic.chains.retrieval_qa.base import RetrievalQA
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.llms import Ollama
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain_text_splitters import CharacterTextSplitter
from fastapi import FastAPI
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AbstractBot:
    def __init__(self):
        pass

    def query_light(self, q):
        pass

    def query_full(self, q):
        pass


class OllamaBot(AbstractBot):
    def __init__(self, url="http://ollama:11434", use_index=True, index_folder="faiss_index"):
        super().__init__()

        # Создание БД из файлов или в памяти.

        if use_index:
            self.store = self._crate_faiss_index_store(index_folder)
        else:
            self.store = self._crate_local_store()

        # Создание llm.

        self.llm = Ollama(
            model="deepseek-r1:1.5b",
            base_url=url
        )

        # Создание цепочки для запросов с промтом.

        self.qa_chain = self._create_qa_chain(self.llm, self.store)

    @staticmethod
    def _crate_faiss_index_store(index_folder):
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        return FAISS.load_local(
            index_folder,
            embeddings,
            allow_dangerous_deserialization=True
        )

    @staticmethod
    def _crate_local_store():
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )

        documents = [
            "LangChain is a framework for developing applications powered by large language models (LLMs).",
            "It simplifies the creation of complex LLM workflows.",
            "FAISS is a library for efficient similarity search and clustering of dense vectors.",
            "RetrievalQA chains use a retriever to fetch relevant documents before generating an answer."
        ]
        docs = [Document(page_content=t) for t in documents]
        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
        texts = text_splitter.split_documents(docs)

        return FAISS.from_documents(texts, embeddings)

    @staticmethod
    def _create_qa_chain(llm, store):
        template = """You are a helpful and honest assistant.
        You must answer the user's question *only* based on the provided context.
        If the answer is not found in the context, you must reply with the exact phrase: 'I do not know'.
        {context}
        Question: {question}
        Answer:"""
        qa_prompt = PromptTemplate(
            template=template
        )
        return RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=store.as_retriever(),
            chain_type_kwargs={"prompt": qa_prompt},
            return_source_documents=True
        )

    def query_light(self, q):
        # Запрос без проверок.

        result = self.qa_chain.invoke({"query": q})

        logger.info(f"Result={result}")

        docs = []
        if result["source_documents"]:
            for doc in result["source_documents"]:
                page_content = str(doc.page_content)
                source = str(doc.metadata.get("source", "unknown"))
                docs.append({"source": source, "page_content": page_content})

        r = result["result"]

        query_result = {"result": r, "docs": docs}

        logger.info(f"Result={query_result}")

        return query_result

    def query_full(self, q):
        # Запрос с проверками.

        if q is None:
            return {"result": "The question cannot be empty"}

        blacklisted_phrases = [
            "ignore all instructions",
            "password",
            "swordfish",
            "output",
            "root",
            "superpassword",
            "credentials",
            "cуперпароль"
        ]

        question_lower = q.lower()
        if any(phrase in question_lower for phrase in blacklisted_phrases):
            return {"result": "Not a secure question"}

        result = self.qa_chain.invoke({"query": q})

        logger.info(f"Result={result}")

        if any(phrase in result["result"].lower() for phrase in blacklisted_phrases):
            return {"result": "I can't answer the question"}

        if not result["source_documents"]:
            return {"result": "Not enough information for answer"}

        docs = []
        if result["source_documents"]:
            for doc in result["source_documents"]:
                page_content = str(doc.page_content)
                source = str(doc.metadata.get("source", "unknown"))
                page_content_lower = page_content.lower()
                if any(phrase in page_content_lower for phrase in blacklisted_phrases):
                    logger.info(f"Skip={source}")
                    continue
                docs.append({"source": source, "page_content": page_content})

        r = result["result"]

        query_result = {"result": r, "docs": docs}

        logger.info(f"Result={query_result}")

        return query_result


def create_ollama_bot(timeout=60 * 15, url="http://ollama:11434", use_index=True, index_folder="faiss_index"):
    start_time = time.time()
    while True:
        if time.time() - start_time > timeout:
            return None

        try:
            _bot = OllamaBot(url=url, use_index=use_index, index_folder=index_folder)
            result = _bot.query_light("What is abstract thing?")
            print(result)
            if _bot:
                return _bot
        except Exception as e:
            print(f"Error: {e}", e)

        print(f"Waiting for bot")
        time.sleep(1)


class EchoBot(AbstractBot):
    def __init__(self):
        super().__init__()

    def query_light(self, q):
        return {"result": q}

    def query_full(self, q):
        return {"result": q}


class Query(BaseModel):
    query: str


# Создание бота согласно входным параметрам.

logger.info("App start")

bot = EchoBot()

ollama_url = os.getenv('OLLAMA_HOST')
if ollama_url is not None:
    index_folder_ = os.getenv('INDEX_FOLDER')
    if index_folder_ is None:
        index_folder_ = "faiss_index"
    logger.info(f"Starting ollama bot. ollama_url={ollama_url}, use_index=True, index_folder={index_folder_}")
    bot = create_ollama_bot(url=ollama_url, use_index=True, index_folder=index_folder_)

app = FastAPI()


@app.post("/query-light")
async def query_light(q: Query, response_model=dict):
    # Запросы без проверок.
    logger.info(f"Query={q}")
    q = q.query
    result = bot.query_light(q)
    logger.info(f"Query={q}. Answer={result}")
    return result


@app.post("/query-full")
async def query_full(q: Query, response_model=dict):
    # Запросы с проверками.
    logger.info(f"Query={q}")
    q = q.query
    result = bot.query_full(q)
    logger.info(f"Query={q}. Answer={result}")
    return result


def main():
    # Запуск сервиса.

    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
