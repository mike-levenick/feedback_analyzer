from google.adk.agents import Agent, SequentialAgent
from .sub_agents.anonymization_agent import anonymization_agent
from .sub_agents.summarizer_agent import summarizer_agent
from .sub_agents.analyzer_agent import analyzer_agent


# Sequential pipeline that automatically chains: anonymize -> summarize -> analyze
feedback_pipeline = SequentialAgent(
    name="feedback_pipeline",
    description="Sequential pipeline that anonymizes, summarizes, and analyzes conversations.",
    sub_agents=[anonymization_agent, summarizer_agent, analyzer_agent],
)

root_agent = Agent(
    name="feedback_analyzer",
    model="gemini-2.0-flash",
    description="Analyzes conversation feedback through anonymization, summarization, and analysis.",
    instruction=(
        "You are a conversation feedback analyzer. Your job is to process conversations "
        "and provide detailed analysis and feedback.\n\n"
        "EXPECTED INPUT FORMAT:\n"
        "Users will provide conversations in the DynamoDB history message schema format, "
        "which includes messages with these key fields:\n"
        "- 'content': The message text (string or list)\n"
        "- 'role': Either 'user' or 'assistant'\n"
        "- 'message_id', 'thread_id': Identifiers\n"
        "- 'PK', 'SK': DynamoDB keys\n"
        "- Optional: 'timestamp', 'created_at', 'updated_at'\n\n"
        "WHEN A USER PROVIDES A CONVERSATION:\n"
        "Delegate to 'feedback_pipeline' which will automatically:\n"
        "1. Anonymize the conversation (replace names, PII, identifiers)\n"
        "2. Summarize the anonymized conversation\n"
        "3. Analyze and provide detailed feedback\n\n"
        "The pipeline will return the complete analysis. Present the results to the user "
        "in a clear, organized format including:\n"
        "- The conversation summary\n"
        "- The detailed analysis with scores and recommendations\n\n"
        "IMPORTANT:\n"
        "- Always use the pipeline for processing conversations\n"
        "- Never expose original PII - only show anonymized data\n"
        "- If any step fails, report the error clearly"
    ),
    sub_agents=[feedback_pipeline],
)
