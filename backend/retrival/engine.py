import sys 
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from dto.decomposed_queries import DecomposedQueries
from helpers.utils import get_datetime_local
from retrival.retriever import retrieve_rag_contexts, retrieve_initial_context, rerank_documents
from common.llm_service import generation_llm
from helpers.retrieval_util import get_decomposition_prompt, format_context, get_rag_prompt
from helpers.constants import (
    RAG_FALLBACK_RESPONSE,
    COHERE_TOP_N, 
    RETRIEVER_TOP_K, 
    MAX_RAG_RESPONSE_GENERATION_RETRIES

)

def get_decomposed_queries(llm, query) -> list[str]:
    context = retrieve_initial_context(query)
    prompt_value = get_decomposition_prompt(query, context)
    try:
        result = llm.with_structured_output(DecomposedQueries).invoke(prompt_value)
        return [q for q in result.queries if q.strip()] or [query]
    except Exception as e:
        print(f"Decomposition failed, using original query: {e}")
        return [query]



def generate_rag_answer(query, 
                        reranking_top_n=COHERE_TOP_N,
                        should_print_subqueries=False, 
                        should_print_ranking_score=False):
    sub_queries = get_decomposed_queries(generation_llm, query)
    
    if should_print_subqueries:
        print(sub_queries)

    docs = retrieve_rag_contexts(sub_queries, reranking_top_n, should_print_ranking_score)
    context = format_context(docs)

    prompt_value = get_rag_prompt(query, context, get_datetime_local(), RAG_FALLBACK_RESPONSE)
    response = generation_llm.invoke(prompt_value)

    return response.content


def get_rag_response(query, 
                     should_print_subqueries=False, 
                     should_print_ranking_score=False, 
                     reranking_top_n=COHERE_TOP_N):
    for attempt in range(MAX_RAG_RESPONSE_GENERATION_RETRIES + 1):

        response = generate_rag_answer(
            query,
            reranking_top_n=reranking_top_n,
            should_print_subqueries=should_print_subqueries,
            should_print_ranking_score=should_print_ranking_score
        )

        if response.strip() != RAG_FALLBACK_RESPONSE:
            return response

        if attempt < MAX_RAG_RESPONSE_GENERATION_RETRIES:
            reranking_top_n = RETRIEVER_TOP_K

    return response