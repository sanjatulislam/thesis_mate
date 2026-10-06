from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from agents.advisor_agent import advisor_node
from agents.supervisor_agent import supervisor_node
from agents.state import AgentState

graph = StateGraph(AgentState)
graph.add_node("supervisor", supervisor_node)
graph.add_node("advisor", advisor_node)

graph.add_edge(START, "supervisor")
graph.add_conditional_edges("supervisor", lambda s: s["next"], {"advisor": "advisor", "answer": END})
graph.add_edge("advisor", END)

app = graph.compile(checkpointer=MemorySaver())


def chat(message: str, thread_id: str) -> str:
    result = app.invoke(
        {"messages": [HumanMessage(content=message)]},
        config={"configurable": {"thread_id": thread_id}},
    )
    return result["messages"][-1].content