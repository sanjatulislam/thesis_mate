import sys 
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from pydantic import BaseModel
from typing import Annotated, Optional, TypedDict, Literal
from langgraph.graph.message import add_messages
from langchain_core.messages import AIMessage

from helpers.constants import ADVISOR_STEP, JOB_SCOUT_STEP, ANSWER_STEP

ProgramCode = Literal["TBA2M", "TDV2M", "TBV2M", "TIS2M", "TDA2M", "TIT2Y"]
NextStep = Literal[ADVISOR_STEP, JOB_SCOUT_STEP, ANSWER_STEP]


AgentName = Literal[ADVISOR_STEP, JOB_SCOUT_STEP]


class PlanStep(BaseModel):
    agent: AgentName
    task: str


class AgentState(TypedDict):
    messages: Annotated[list, add_messages] 
    program: Optional[str]
    plan: list[PlanStep]
    steps: list[PlanStep]
    results: list[str]


def task_with_context(step: PlanStep, results: list[str]) -> str:
    if not results:
        return step.task
    earlier = "\n\n".join(results)
    return f"{step.task}\n\nResults from earlier steps:\n{earlier}"

def final_text(result: dict) -> str:
    for m in reversed(result["messages"]):
        if isinstance(m, AIMessage) and isinstance(m.content, str) and m.content.strip() and not m.tool_calls:
            return m.content
    return "Sorry, I couldn't put together an answer this time. Could you try asking again?"