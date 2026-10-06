
import sys 
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from agents.agent_prompts import SUPERVISOR_PROMPT, DIRECT_REPLY_PROMPT

from pydantic import BaseModel
from typing import Optional
from agents.state import AgentState, NextStep
from common.llm_service import generation_llm
from langchain_core.messages import SystemMessage, AIMessage


class Route(BaseModel):
    next: NextStep     
    task: Optional[str] = None
    answer: Optional[str] = None
    program: Optional[str] = None



def reply_directly(state: AgentState) -> str:
    """Plain LLM reply for small talk, used if the Supervisor left 'answer' empty."""
    return generation_llm.invoke([SystemMessage(content=DIRECT_REPLY_PROMPT), *state["messages"][-4:]]).content



def supervisor_node(state: AgentState) -> dict:
    prompt = SUPERVISOR_PROMPT.format(program=state.get("program") or "unknown")
    
    route = generation_llm.with_structured_output(Route).invoke(
        [SystemMessage(content=prompt), *state["messages"][-15:]]
    )

    print(f"[supervisor -> {route.next}] {route.task or ''}")

    update = {
        "next": route.next,
        "task": route.task,
        "program": route.program or state.get("program"),
    }

    if route.next == "answer":
        answer = route.answer or reply_directly(state)
        update["messages"] = [AIMessage(content=answer)]

    return update