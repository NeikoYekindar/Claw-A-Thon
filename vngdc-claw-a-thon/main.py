import os
from datetime import datetime

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain_core.tools import tool

from greennode_agentbase import (
    GreenNodeAgentBaseApp,
    RequestContext,
    PingStatus,
)
from greennode_agentbase.memory import MemoryClient
from greennode_agentbase.memory.models import MemoryRecordSearchRequest
from greennode_agent_bridge import AgentBaseMemoryEvents
from langgraph.config import get_config

load_dotenv()

app = GreenNodeAgentBaseApp()

# --- Memory Configuration ---
MEMORY_ID = os.environ.get("MEMORY_ID", "")
if not MEMORY_ID:
    raise ValueError("MEMORY_ID environment variable is required for memory-enabled agents")

MEMORY_STRATEGY_ID = os.environ.get("MEMORY_STRATEGY_ID", "default")

checkpointer = AgentBaseMemoryEvents(memory_id=MEMORY_ID)
memory_client = MemoryClient()

# --- LLM Configuration ---
LLM_MODEL = os.environ.get("LLM_MODEL", "")
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "")
LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
if not LLM_MODEL or not LLM_BASE_URL or not LLM_API_KEY:
    raise ValueError(
        "LLM_MODEL, LLM_BASE_URL, and LLM_API_KEY environment variables are required. "
        "Set them in your .env file or use /agentbase-llm to get a platform API key."
    )

llm = ChatOpenAI(
    model=LLM_MODEL,
    base_url=LLM_BASE_URL,
    api_key=LLM_API_KEY,
)



def _get_actor_id() -> str:
    config = get_config()
    return config["configurable"].get("actor_id", "default")


def _build_namespace(actor_id: str) -> str:
    return f"/strategies/{MEMORY_STRATEGY_ID}/actors/{actor_id}"


@tool
def remember(fact: str) -> str:
    """Store a fact or finding into long-term memory for future reference."""
    namespace = _build_namespace(_get_actor_id())
    memory_client.insert_memory_records_directly(
        id=MEMORY_ID,
        namespace=namespace,
        request=[fact],
    )
    return f"Remembered: {fact}"


@tool
def recall(query: str) -> str:
    """Search long-term memory for facts or findings relevant to the query."""
    namespace = _build_namespace(_get_actor_id())
    results = memory_client.search_memory_records(
        id=MEMORY_ID,
        namespace=namespace,
        request=MemoryRecordSearchRequest(query=query, limit=10),
    )
    if not results:
        return "No relevant memories found."
    return "\n".join(f"- {r.memory} (score: {r.score:.2f})" for r in results)


# --- Create Agent ---
agent = create_agent(
    llm,
    tools=[remember, recall],
    system_prompt=(
        "You are an expert AI assistant specializing in code analysis and log analysis. "
        "Your capabilities include:\n"
        "- Analyzing source code for bugs, security vulnerabilities, performance issues, and code quality\n"
        "- Parsing and interpreting application logs (error logs, access logs, system logs)\n"
        "- Identifying patterns, anomalies, and root causes from log output\n"
        "- Suggesting fixes, refactors, and improvements to code\n"
        "- Explaining stack traces and error messages clearly\n"
        "- Detecting log-level issues (ERROR, WARN, CRITICAL) and their implications\n\n"
        "Use 'remember' to store important findings or patterns about the user's codebase or systems. "
        "Use 'recall' to retrieve previously stored insights when they are relevant."
    ),
    checkpointer=checkpointer,
)


@app.entrypoint
def handler(payload: dict, context: RequestContext) -> dict:

    if not context.user_id or not context.session_id:
        return {
            "status": "error",
            "error": "Missing required headers: X-GreenNode-AgentBase-User-Id and X-GreenNode-AgentBase-Session-Id are required when using memory.",
        }

    message = payload.get("message", "Hello")

    config = {
        "configurable": {
            "thread_id": context.session_id,
            "actor_id": context.user_id,
        }
    }

    result = agent.invoke(
        {"messages": [{"role": "user", "content": message}]},
        config=config,
    )
    ai_message = result["messages"][-1]
    return {
        "status": "success",
        "response": ai_message.content,
        "timestamp": datetime.now().isoformat(),
    }


@app.ping
def health_check() -> PingStatus:

    return PingStatus.HEALTHY


if __name__ == "__main__":
    app.run(port=8080, host="0.0.0.0")
