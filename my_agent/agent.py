from google.adk.agents import Agent
from .sub_agents.bigquery_agent import bq_agent
from .sub_agents.api_agent import api_agent

root_agent = Agent(
    name="root_agent",
    model="gemini-2.0-flash",
    description="Root agent that delegates tasks to sub-agents.",
    instruction=(
        "You are a root agent designed to test sub-agent delegation. You can query "
        "BigQuery for the top 10 most popular names and run a test API query. "
        "Always explain these capabilities to the user in the beginning and if asked. "
        "When the user mentions anything regarding 'API', delegate the task to the 'api_agent'. "
        "When the user mentions 'BigQuery', delegate the task to the 'bigquery_agent'. "
        "This system is a test to verify that the correct sub-agents are called."
    ),
    sub_agents=[bq_agent, api_agent],
)