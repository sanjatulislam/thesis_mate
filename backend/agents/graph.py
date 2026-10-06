import sys 
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from agents.advisor_agent import advisor_node
from agents.supervisor_agent import supervisor_node
from agents.job_scout_agent import job_scout_node
from agents.state import AgentState
from helpers.constants import ADVISOR_STEP, JOB_SCOUT_STEP, ANSWER_STEP


graph = StateGraph(AgentState)
graph.add_node("supervisor", supervisor_node)
graph.add_node("advisor", advisor_node)
graph.add_node("job_scout", job_scout_node)

graph.add_edge(START, "supervisor")
graph.add_conditional_edges("supervisor", 
                            lambda s: s["next"], 
                            {ADVISOR_STEP: ADVISOR_STEP, JOB_SCOUT_STEP: JOB_SCOUT_STEP, ANSWER_STEP: END},)
graph.add_edge("advisor", END)
graph.add_edge("job_scout", END)

app = graph.compile(checkpointer=MemorySaver())


def chat(message: str, thread_id: str) -> dict:

    messages = [HumanMessage(content=message)]
    config = {"configurable": {"thread_id": thread_id}}

    result = app.invoke({"messages": messages}, config=config)

    return {
        "reply": result["messages"][-1].content,
        "route": result.get("next"),
        "program": result.get("program"),
    }