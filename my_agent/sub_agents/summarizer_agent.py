"""Summarizer agent for anonymized conversation history.

This agent takes an anonymized conversation and produces a concise summary
capturing the key points, topics discussed, and overall flow of the conversation.
"""

from google.adk.agents import Agent


def format_conversation_for_summary(messages: list[dict]) -> dict:
    """Format a list of messages into a readable conversation format for summarization.

    Takes messages in the history_message_schema format and converts them
    into a clean, readable format for the summarizer.

    Args:
        messages: List of message dictionaries with 'role' and 'content' fields.

    Returns:
        dict: Contains 'formatted_conversation' string and 'message_count'.
    """
    if not isinstance(messages, list):
        return {"status": "error", "error_message": "Messages must be a list"}

    if not messages:
        return {
            "status": "success",
            "formatted_conversation": "",
            "message_count": 0,
        }

    formatted_lines = []
    for i, msg in enumerate(messages):
        role = msg.get("role", "unknown").upper()
        content = msg.get("content", "")

        # Handle structured content (list format)
        if isinstance(content, list):
            content_parts = []
            for item in content:
                if isinstance(item, str):
                    content_parts.append(item)
                elif isinstance(item, dict) and "text" in item:
                    content_parts.append(item["text"])
            content = " ".join(content_parts)

        formatted_lines.append(f"[{role}]: {content}")

    return {
        "status": "success",
        "formatted_conversation": "\n\n".join(formatted_lines),
        "message_count": len(messages),
    }


summarizer_agent = Agent(
    name="summarizer_agent",
    model="gemini-2.0-flash",
    description="Agent that summarizes anonymized conversations.",
    instruction=(
        "You are a conversation summarizer agent in a sequential pipeline. Your job is to "
        "take anonymized conversations, create summaries, and pass both the original "
        "messages AND summary to the next stage.\n\n"
        "These conversations are being summarized because the end-user provided feedback in "
        "the form of either a thumb up a thumb down (verso up/verso down), along with optional comments.\n\n"
        "This feedback is an important part of the conversation analysis process, but may not tell the whole story. "
        "Be sure to also look at messages from the user after a verso is provided for additional insight.\n\n"
        "WHEN GIVEN ANONYMIZED CONVERSATION DATA:\n"
        "1. Use 'format_conversation_for_summary' if given raw message data\n"
        "2. Analyze the conversation flow and identify:\n"
        "   - Main topics discussed\n"
        "   - Key questions asked by the user\n"
        "   - Key responses/solutions provided\n"
        "   - Any unresolved issues or follow-ups needed\n"
        "   - Overall sentiment/tone of the conversation\n"
        "   - Feedback provided by the user (thumbs up/down and comments)\n"
        "   - Messages after feedback for additional context\n"
        "3. Create a structured summary with these sections:\n"
        "   - **Overview**: 1-2 sentence high-level summary\n"
        "   - **Topics Discussed**: Bullet points of main topics\n"
        "   - **Key Points**: Important information exchanged\n"
        "   - **Outcome**: How the conversation concluded\n\n"
        "   - **Issue Summary**: Why the user provided feedback (thumbs up/down) and any comments\n"
        "CRITICAL FOR PIPELINE COORDINATION:\n"
        "After creating the summary, you MUST output BOTH:\n"
        "1. **MESSAGES**: The original anonymized message data you received\n"
        "2. **SUMMARY**: Your completed summary\n\n"
        "Format your final output like this:\n"
        "=== ANONYMIZED MESSAGES ===\n"
        "[Include the original anonymized conversation data here]\n\n"
        "=== SUMMARY ===\n"
        "[Your structured summary here]\n\n"
        "This ensures the analyzer agent receives both the detailed conversation data "
        "and the summary for comprehensive analysis.\n\n"
        "IMPORTANT:\n"
        "- Keep all anonymized placeholders intact (e.g., [PERSON_NAME_abc123])\n"
        "- Be concise but capture all important information\n"
        "- Always include both sections in your output for proper pipeline flow"
    ),
    tools=[format_conversation_for_summary],
)
