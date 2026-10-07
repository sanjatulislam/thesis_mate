import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))


from typing import Optional
import re
from dotenv import load_dotenv
import os
from langchain_core.documents import Document
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


import weaviate
from weaviate.classes.init import Auth
from langchain_weaviate import WeaviateVectorStore
from langchain_huggingface import HuggingFaceEmbeddings

from langchain_text_splitters import RecursiveCharacterTextSplitter


from helpers.constants import (
    DATA_DIR,
    WEAVIATE_TEXT_KEY, 
    EMBEDDING_MODEL, 
    SPLITTER_CHUNK_SIZE, 
    SPLITTER_CHUNK_OVERLAP,
    WEAVIATE_COLLECTION
)

load_dotenv()

def merge_pages_to_single_document(doc_name, pages) -> Optional[Document]:
    if not pages:
        return None
    
    text = "\n".join(
        re.sub(r"\n\s*\d+\s*$", "", p.page_content)
        for p in pages
    )
    text = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", text).replace("\u202f", " ")
    text = re.sub(r"[ \t]+\n", "\n", text)

    return Document(
        page_content=text,
        metadata={"source": doc_name}
    )
       

def load_documents() -> list[Document]:
    all_docs = []
    data_dir = Path(DATA_DIR)

    for pdf in data_dir.glob("*.pdf"):
        loader = PyMuPDFLoader(file_path=pdf)
        docs = loader.load()

        document = merge_pages_to_single_document(pdf.name, docs)

        if document:
            all_docs.append(document)
            print(f"Loaded {pdf.name}: {len(docs)} pages")

    return all_docs


def chunk_documents(documents, chunk_size=SPLITTER_CHUNK_SIZE, chunk_overlap=SPLITTER_CHUNK_OVERLAP):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", ". ", "\n", " ", ""],
        keep_separator="end",
        add_start_index=True
    )
    chunks = splitter.split_documents(documents)

    print(f"Total chunks: {len(chunks)}")

    return chunks


def update_chunk_metadata(chunks):
    all_chunks = []

    if chunks:
        for i, chunk in enumerate(chunks):
            source = chunk.metadata.get("source")

            doc_name = source.split("\\")[-1]
            doc_name_pref = doc_name.split(".")[0]
            doc_name_ext = doc_name.split(".")[-1]

            doc = Document(page_content=chunk.page_content, metadata={"source": doc_name, "chunk_id": f"{doc_name_pref}_{i+1}.{doc_name_ext}"})

            all_chunks.append(doc)

    print(f"Total chunks: {len(all_chunks)}")

    return all_chunks

def collection_count(client, name: str) -> int:
    if not client.collections.exists(name):
        return 0
    result = client.collections.get(name).aggregate.over_all(total_count=True)
    return result.total_count or 0


def store_documents(chunks, rebuild=False):
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        encode_kwargs={"normalize_embeddings": True}
    )

    client = weaviate.connect_to_weaviate_cloud(
        cluster_url = os.environ['WEAVIATE_URL'],
        auth_credentials=Auth.api_key(os.environ['WEAVIATE_ADMIN_API_KEY'])
    )

    existing = collection_count(client, WEAVIATE_COLLECTION)

    if existing and not rebuild:
        print(f"'{WEAVIATE_COLLECTION}' already has {existing} chunks, skipping. Use rebuild=True to re-ingest.")
        return

    if existing and rebuild:
        client.collections.delete(WEAVIATE_COLLECTION)
        print(f"Deleted '{WEAVIATE_COLLECTION}' for a clean rebuild.")

    store = WeaviateVectorStore(
        client=client,
        index_name=WEAVIATE_COLLECTION,
        text_key=WEAVIATE_TEXT_KEY,
        embedding=embeddings
    )

    store.add_documents(chunks)

    print(f"Stored {len(chunks)} vector database")

    client.close()


def run_ingestion_pipeline(rebuild=False):
    documents = load_documents()
    chunks = chunk_documents(documents)
    chunks = update_chunk_metadata(chunks)
    store_documents(chunks, rebuild=rebuild)


if __name__ == "__main__":
    run_ingestion_pipeline()   