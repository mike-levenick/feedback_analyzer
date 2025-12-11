"""Deployment script for feedback_analyzer to Vertex AI Agent Engine.

Run this script to deploy your agent to Google Cloud.
Usage: python deploy.py
"""

import vertexai
from vertexai import agent_engines

# Import your root agent
from feedback_analyzer.agent import root_agent

# Configuration from your .env
PROJECT_ID = "red-formula-472219-g8"
LOCATION = "us-central1"
STAGING_BUCKET = "gs://red-formula-472219-g8-adk-staging"  # Will be created if needed
DISPLAY_NAME = "feedback-analyzer"


def main():
    print("Initializing Vertex AI...")
    print(f"  Project: {PROJECT_ID}")
    print(f"  Location: {LOCATION}")
    print(f"  Staging Bucket: {STAGING_BUCKET}")

    # Initialize the Vertex AI SDK
    vertexai.init(
        project=PROJECT_ID,
        location=LOCATION,
        staging_bucket=STAGING_BUCKET,
    )

    print("\nWrapping agent in AdkApp...")
    # Wrap the agent in an AdkApp object
    app = agent_engines.AdkApp(
        agent=root_agent,
        enable_tracing=True,
    )

    print("\nDeploying to Agent Engine (this may take several minutes)...")
    # Deploy to Agent Engine
    remote_app = agent_engines.create(
        agent_engine=app,
        display_name=DISPLAY_NAME,
        requirements=[
            "google-adk>=0.3.0",
        ],
    )

    print("\n" + "=" * 60)
    print("DEPLOYMENT SUCCESSFUL!")
    print("=" * 60)
    print(f"\nResource Name: {remote_app.resource_name}")
    print("\nView in Cloud Console:")
    print(
        f"  https://console.cloud.google.com/vertex-ai/agents/agent-engines?project={PROJECT_ID}"
    )
    print("\nTo interact with your deployed agent, use:")
    print(f'  remote_app = agent_engines.get("{remote_app.resource_name}")')

    return remote_app


if __name__ == "__main__":
    main()
