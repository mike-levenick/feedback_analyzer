from google.adk.agents import Agent
import requests

def fetch_public_api() -> dict:
    """Fetches data from a public API.

    Returns:
        dict: The JSON response from the API.
    """
    try:
        response = requests.get("https://jsonplaceholder.typicode.com/todos/1")
        response.raise_for_status()
        return {"status": "success", "data": response.json()}
    except Exception as e:
        return {"status": "error", "error_message": str(e)}

api_agent = Agent(
    name="api_agent",
    model="gemini-2.0-flash",
    description="Agent that can make API calls.",
    instruction="You are an agent that makes API calls to fetch data.",
    tools=[fetch_public_api],
)
