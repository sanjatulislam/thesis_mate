
import sys 
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from agents.agent_prompts import SUPERVISOR_PROMPT, DIRECT_REPLY_PROMPT
from agents.state import ProgramCode

from pydantic import BaseModel, Field
from typing import Optional
from agents.state import AgentState, PlanStep
from common.llm_service import generation_llm
from langchain_core.messages import SystemMessage, AIMessage



class Route(BaseModel):
    steps: list[PlanStep] = Field(
        default_factory=list,
        description="Ordered steps for the agents (one step per need, at most 3). Empty when you reply yourself.",
    )
    answer: Optional[str] = Field(
        None, description="When steps is empty: your own full reply to the student in friendly, complete sentences (for example a question asking which subject area interests them). Write new text in your own words."
    )
    program: Optional[ProgramCode] = Field(
        None, description="Programme code when the student states their own programme."
    )


def supervisor_node(state: AgentState) -> dict:
    prompt = SUPERVISOR_PROMPT.format(program=state.get("program") or "unknown")
    route = generation_llm.with_structured_output(Route).invoke(
        [SystemMessage(content=prompt), *state["messages"][-20:]]
    )

    steps = route.steps[:3]
    print("[plan]", [(s.agent, s.task) for s in steps] or "reply directly")

    update = {
        "plan": steps,
        "steps": steps,
        "results": [],
        "program": route.program or state.get("program"),
    }
    if not steps:
        answer = (route.answer or "").strip()
        is_echo = answer.lower() == state["messages"][-1].content.strip().lower()

        if not answer or is_echo:
            answer = reply_directly(state, update["program"]).strip()

        update["messages"] = [AIMessage(content=answer)]
    return update


def reply_directly(state: AgentState) -> str:
    """Plain LLM reply for small talk, used if the Supervisor left 'answer' empty."""
    return generation_llm.invoke([SystemMessage(content=DIRECT_REPLY_PROMPT), *state["messages"][-4:]]).content



