import sys 
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from typing import Annotated, Optional, TypedDict, Literal
from langgraph.graph.message import add_messages

from helpers.constants import ADVISOR_STEP, JOB_SCOUT_STEP, ANSWER_STEP

ProgramCode = Literal["TBA2M", "TDV2M", "TBV2M", "TIS2M", "TDA2M", "TIT2Y"]
NextStep = Literal[ADVISOR_STEP, JOB_SCOUT_STEP, ANSWER_STEP]


class AgentState(TypedDict):
    messages: Annotated[list, add_messages] 
    program: Optional[str]
    task: Optional[str] 
    next: Optional[str]