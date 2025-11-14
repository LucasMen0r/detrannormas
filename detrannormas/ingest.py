# ingest.py
import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain.text_splitters import RecursiveCharacterTextSplitter

# 1. Configurações
# O nome do arquivo PDF do seu manual.
PDF_FILE_NAME = "MANUAL - Norma de padronização da nomenclatura de objetos do banco de dados (v 0.29).docx.pdf"
# Nome do modelo Ollama que você está usando (ex: nomic-embed-text ou all-minilm)
OLLAMA_MODEL = "nomic-embed-text" 
# Diretório para armazenar o banco de vetores Chroma localmente (opcional se usar PostgreSQL)
CHROMA_DB_PATH = "./chroma_db"

def ingest_data():
    """
    Carrega o PDF, divide o texto, cria embeddings e armazena os vetores.
    """
    if not os.path.exists(PDF_FILE_NAME):
        print(f"ERRO: Arquivo PDF não encontrado: {PDF_FILE_NAME}")
        print("Certifique-se de que o PDF está na pasta atual.")
        return

    print(f"Carregando o documento: {PDF_FILE_NAME}...")
    loader = PyPDFLoader(PDF_FILE_NAME)
    documents = loader.load()

    # 2. Divisão de Texto (Chunking)
    print("Dividindo o texto em pedaços (chunks)...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    texts = text_splitter.split_documents(documents)

    # 3. Criação de Embeddings (Vetores)
    print(f"Criando embeddings usando o Ollama ({OLLAMA_MODEL})...")
    # Certifique-se de que o Ollama está rodando e o modelo está baixado!
    embeddings = OllamaEmbeddings(model=OLLAMA_MODEL)

    # 4. Armazenamento dos Vetores
    # Usaremos o ChromaDB como banco de vetores local por simplicidade inicial.
    print(f"Armazenando vetores no ChromaDB em: {CHROMA_DB_PATH}...")
    Chroma.from_documents(
        documents=texts,
        embedding=embeddings,
        persist_directory=CHROMA_DB_PATH,
    )
    print("Ingestão concluída. Os vetores estão prontos para consulta.")

if __name__ == "__main__":
    ingest_data()
