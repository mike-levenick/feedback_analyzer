# Test Agent System

This project is a **proof-of-concept** designed to test multi-agent delegation using the Google Agent Development Kit (ADK). It features a root agent that delegates tasks to specialized sub-agents based on user input.

## ⚠️ Disclaimer: Not for Production Use

**This project is strictly for testing and demonstration purposes.**

*   It is **not** intended for production environments.
*   The code is designed to verify that sub-agents are correctly called and that the delegation logic works as expected.
*   Security, error handling, and scalability features required for a production system may be minimal or missing.

## Architecture

The system consists of a hierarchical agent structure:

1.  **Root Agent**: The main entry point. It understands user intent and routes requests to the appropriate sub-agent.
2.  **BigQuery Sub-Agent**: Handles requests related to BigQuery. It is currently configured to query a public dataset for popular names.
3.  **API Sub-Agent**: Handles requests related to external APIs. It is currently configured to fetch data from a placeholder test API.

## Capabilities

*   **BigQuery**: Can query the `bigquery-public-data.usa_names.usa_1910_2013` dataset to retrieve the top 10 most popular names.
*   **API**: Can make a test GET request to `https://jsonplaceholder.typicode.com/todos/1`.

## Setup

1.  **Initialize Virtual Environment**:
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the Agent**:
    From the parent folder, run:
    ```bash
    adk web
    ```
