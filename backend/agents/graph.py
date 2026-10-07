import sys 
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from langchain_core.messages import HumanMessage, AIMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from agents.advisor_agent import advisor_node
from agents.supervisor_agent import supervisor_node
from agents.job_scout_agent import job_scout_node
from agents.state import AgentState


def next_step(state: AgentState) -> str:
    plan = state.get("plan") or []
    if plan:
        return plan[0].agent
    return "finish" if state.get("results") else END


def finish_node(state: AgentState) -> dict:
    results = state.get("results") or []
    if not results:
        return {}   
    return {"messages": [AIMessage(content="\n\n".join(results))], "results": []}


ROUTES = {"advisor": "advisor", "job_scout": "job_scout", "finish": "finish", END: END}


graph = StateGraph(AgentState)
graph.add_node("supervisor", supervisor_node)
graph.add_node("advisor", advisor_node)
graph.add_node("job_scout", job_scout_node)
graph.add_node("finish", finish_node)

graph.add_edge(START, "supervisor")
graph.add_conditional_edges("supervisor", next_step, ROUTES)
graph.add_conditional_edges("advisor", next_step, ROUTES)
graph.add_conditional_edges("job_scout", next_step, ROUTES)
graph.add_edge("finish", END)

app = graph.compile(checkpointer=MemorySaver())


def chat(message: str, thread_id: str) -> dict:
    config = {"configurable": {"thread_id": thread_id}}
    result = app.invoke({"messages": [HumanMessage(content=message)]}, config=config)

    return {
        "reply": result["messages"][-1].content,
        "program": result.get("program"),
        "steps": result.get("steps") or [],
    }
