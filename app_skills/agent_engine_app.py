from vertexai.agent_engines import AdkApp
from .agent import root_agent

agent_engine = AdkApp(
    agent=root_agent,
    enable_tracing=True,
)
