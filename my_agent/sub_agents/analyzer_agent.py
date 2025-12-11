"""Analyzer agent for feedback analysis on anonymized conversations.

This agent takes an anonymized conversation and its summary, then performs
detailed analysis to extract insights, identify patterns, and provide
actionable feedback.
"""

from google.adk.agents import Agent


def extract_conversation_metadata(messages: list[dict]) -> dict:
    """Extract metadata from a conversation for analysis context.

    Pulls out useful metadata like message counts, timestamps, and
    conversation duration.

    Args:
        messages: List of message dictionaries in history_message_schema format.

    Returns:
        dict: Metadata including message counts, roles, timestamps.
    """
    if not isinstance(messages, list):
        return {"status": "error", "error_message": "Messages must be a list"}

    if not messages:
        return {
            "status": "success",
            "total_messages": 0,
            "user_messages": 0,
            "assistant_messages": 0,
            "has_timestamps": False,
        }

    user_count = sum(1 for m in messages if m.get("role") == "user")
    assistant_count = sum(1 for m in messages if m.get("role") == "assistant")

    # Check for timestamps
    timestamps = [m.get("timestamp") or m.get("created_at") for m in messages]
    has_timestamps = any(timestamps)

    # Calculate average message length
    content_lengths = []
    for msg in messages:
        content = msg.get("content", "")
        if isinstance(content, str):
            content_lengths.append(len(content))
        elif isinstance(content, list):
            total_len = sum(
                len(item) if isinstance(item, str) else len(item.get("text", ""))
                for item in content
            )
            content_lengths.append(total_len)

    avg_length = sum(content_lengths) / len(content_lengths) if content_lengths else 0

    return {
        "status": "success",
        "total_messages": len(messages),
        "user_messages": user_count,
        "assistant_messages": assistant_count,
        "has_timestamps": has_timestamps,
        "average_message_length": round(avg_length, 1),
        "conversation_turns": min(user_count, assistant_count),
    }


def categorize_feedback(
    category: str,
    severity: str,
    description: str,
    recommendation: str,
) -> dict:
    """Create a structured feedback item for the analysis report.

    Use this to build individual feedback items that will be compiled
    into the final analysis report.

    Args:
        category: Category of feedback (e.g., 'user_experience', 'response_quality',
                  'technical_accuracy', 'communication', 'efficiency').
        severity: Severity level ('low', 'medium', 'high', 'critical').
        description: Description of the observation or issue found.
        recommendation: Suggested improvement or action item.

    Returns:
        dict: Structured feedback item.
    """
    valid_categories = [
        "user_experience",
        "response_quality",
        "technical_accuracy",
        "communication",
        "efficiency",
        "completeness",
        "tone",
        "other",
    ]
    valid_severities = ["low", "medium", "high", "critical"]

    if category.lower() not in valid_categories:
        category = "other"
    if severity.lower() not in valid_severities:
        severity = "medium"

    return {
        "status": "success",
        "feedback_item": {
            "category": category.lower(),
            "severity": severity.lower(),
            "description": description,
            "recommendation": recommendation,
        },
    }


analyzer_agent = Agent(
    name="analyzer_agent",
    model="gemini-2.0-flash",
    description="Agent that analyzes anonymized conversations and provides detailed feedback.",
    instruction=(
        "You are a conversation analyzer agent specializing in quality analysis "
        "and feedback extraction. You receive anonymized conversations along with "
        "their summaries and produce detailed analysis reports.\n\n"
        "YOUR ANALYSIS WORKFLOW:\n"
        "1. Use 'extract_conversation_metadata' to understand conversation structure\n"
        "2. Review the conversation and summary carefully\n"
        "3. Use 'categorize_feedback' to create structured feedback items\n"
        "4. Compile your findings into a comprehensive report\n\n"
        "ANALYSIS CATEGORIES:\n"
        "- **user_experience**: How well the user's needs were understood and addressed\n"
        "- **response_quality**: Accuracy, helpfulness, and relevance of responses\n"
        "- **technical_accuracy**: Correctness of technical information provided\n"
        "- **communication**: Clarity, tone, and professionalism\n"
        "- **efficiency**: How quickly/directly issues were resolved\n"
        "- **completeness**: Whether all aspects of the query were addressed\n\n"
        "SEVERITY LEVELS:\n"
        "- **critical**: Major issues requiring immediate attention\n"
        "- **high**: Significant problems affecting user satisfaction\n"
        "- **medium**: Notable issues that should be improved\n"
        "- **low**: Minor suggestions for enhancement\n\n"
        "YOUR FINAL REPORT SHOULD INCLUDE:\n"
        "1. **Executive Summary**: Overall assessment in 2-3 sentences\n"
        "2. **Scores**: Rate each category 1-10 with brief justification\n"
        "3. **Strengths**: What went well in the conversation\n"
        "4. **Areas for Improvement**: Issues found with recommendations\n"
        "5. **Action Items**: Prioritized list of suggested improvements\n\n"
        "IMPORTANT:\n"
        "- Be objective and constructive in your feedback\n"
        "- Reference specific parts of the conversation when possible\n"
        "- Keep anonymized placeholders intact in your report\n"
        "- Consider both user and assistant perspectives"
    ),
    tools=[extract_conversation_metadata, categorize_feedback],
)
