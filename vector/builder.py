import os, shutil
from langchain_chroma import Chroma
from .embeddings import embedding_model
from .loaders import load_json_kb, load_md_kb, load_pdf_kb
from .chunker import chunk_documents


def build_chromadb(kb_path="KnowledgeBaseFiles"):
    all_docs = []

    # load JSON + MD KB
    for file in os.listdir(kb_path):
        path = os.path.join(kb_path, file)

        if file.endswith(".json"):
            all_docs.extend(load_json_kb(path))
        elif file.endswith(".md"):
            all_docs.extend(load_md_kb(path))

    # load PDFs
    all_docs.extend(load_pdf_kb())

    # chunking
    chunks = chunk_documents(all_docs)

    # remove old DB
    if os.path.exists("ChromaDB"):
        shutil.rmtree("ChromaDB")

    # build new DB
    Chroma.from_documents(
        documents=chunks,
        embedding=embedding_model,
        persist_directory="ChromaDB"
    )

    print("ChromaDB was successfully built.")
