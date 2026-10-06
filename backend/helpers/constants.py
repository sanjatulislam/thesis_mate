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

RAG_ERROR_RESPONSE = "The guideline search is temporarily unavailable. Please try again in a moment."

MAX_LLM_RETRIES=2

JOBTECH_SEARCH_URL = "https://jobsearch.api.jobtechdev.se/search"
JOBTECH_SEARCH_AD = "https://jobsearch.api.jobtechdev.se/ad/31491359"
THESIS_TERMS = ["master thesis", "exjobb", "degree project", "thesis"]
JOBTECH_SENDER_LIMIT=10
JOBTECH_REQUEST_LIMIT=20
JOBTECH_REQUEST_TIMEOUT=20
JOBTECH_REQUEST_HEADER = { "accept": "application/json" }
JOBTECH_REQUEST_SORTING = "relevance"