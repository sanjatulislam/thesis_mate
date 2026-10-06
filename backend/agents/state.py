from typing import Annotated, Optional, TypedDict, Literal
from langgraph.graph.message import add_messages

NextStep = Literal["advisor", "answer"]

class AgentState(TypedDict):
    messages: Annotated[list, add_messages] 
    program: Optional[str]
    task: Optional[str] 
    next: Optional[str]