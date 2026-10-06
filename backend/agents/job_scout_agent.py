import sys 
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))


from langchain.agents import create_agent
from langchain_core.messages import HumanMessage

from agents.state import AgentState
from agents.tools import check_deadlines, get_job_details, search_jobtech
from common.llm_service import generation_llm
from agents.agent_prompts import JOB_SCOUT_PROMPT

job_scout_agent = create_agent(
    generation_llm,
    tools=[search_jobtech, get_job_details, check_deadlines],
    system_prompt=JOB_SCOUT_PROMPT,
)


def job_scout_node(state: AgentState) -> dict:
    result = job_scout_agent.invoke({"messages": [HumanMessage(content=state["task"])]})
    return {"messages": [result["messages"][-1]]}