DATA_DIR="./../data"

WEAVIATE_COLLECTION="thesis_guideline"
WEAVIATE_TEXT_KEY="content"

SPLITTER_CHUNK_SIZE=1500
SPLITTER_CHUNK_OVERLAP=300

EMBEDDING_MODEL="BAAI/bge-base-en-v1.5"
EMBEDDING_MODEL_QUERY_INSTRUCTION="Represent this sentence for searching relevant passages:"

RETRIEVER_TOP_K=10

COHERE_RERANK_MODEL = "rerank-v3.5"
COHERE_TOP_N=6

GENERATION_LLM="Qwen/Qwen3.8-27B"
GENERATION_TEMPERATURE=0.1
GENERATION_LLM_MAX_TOKENS=900

RAG_FALLBACK_RESPONSE = (
    "I could not find this in the IT Departments thesis guidelines. "
    "Please ask the thesis coordinator at exjobb@it.uu.se or post in the thesis Slack workspace."
)

MAX_RAG_RESPONSE_GENERATION_RETRIES=2