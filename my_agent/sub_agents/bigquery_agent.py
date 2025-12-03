from google.adk.agents import Agent
from google.cloud import bigquery

def query_public_dataset() -> dict:
    """Queries a public BigQuery dataset to get the top 10 most popular names.

    Returns:
        dict: A dictionary containing the query results.
    """
    try:
        client = bigquery.Client()
        query = """
            SELECT name, SUM(number) as total_count
            FROM `bigquery-public-data.usa_names.usa_1910_2013`
            GROUP BY name
            ORDER BY total_count DESC
            LIMIT 10
        """
        query_job = client.query(query)
        results = []
        for row in query_job:
            results.append({"name": row.name, "total_count": row.total_count})
        
        return {"status": "success", "data": results}
    except Exception as e:
        return {"status": "error", "error_message": str(e)}

bq_agent = Agent(
    name="bigquery_agent",
    model="gemini-2.0-flash",
    description="Agent that can query public BigQuery datasets.",
    instruction="You are an agent that queries BigQuery for public data.",
    tools=[query_public_dataset],
)
