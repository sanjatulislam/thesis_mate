import os 
from dotenv import load_dotenv

from langchain_groq import ChatGroq

import sys 
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from helpers.constants import (
    GENERATION_LLM, 
    GENERATION_TEMPERATURE, 
    GENERATION_LLM_MAX_TOKENS,
    MAX_LLM_RETRIES,
    GENERATION_LLM_THINKING_MODE
)


load_dotenv()

def get_groq(model=GENERATION_LLM,
             max_tokens=GENERATION_LLM_MAX_TOKENS,
             temperature=GENERATION_TEMPERATURE,
             max_retries=MAX_LLM_RETRIES,
             reasoning_effort=GENERATION_LLM_THINKING_MODE):
    return ChatGroq(
        model=model,
        api_key=os.environ['GROQ_API_KEY'],
        max_tokens=max_tokens,
        temperature=temperature,
        max_retries=max_retries,
        reasoning_effort=reasoning_effort
    )

generation_llm = get_groq()