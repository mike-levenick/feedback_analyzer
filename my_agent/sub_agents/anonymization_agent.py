"""Anonymization agent for conversation history messages.

This agent provides tools to anonymize PII and sensitive identifiers
in conversation data based on the history message schema.

The agent uses LLM intelligence to identify human names contextually,
rather than relying on hardcoded name lists.
"""

import hashlib
import re

from google.adk.agents import Agent


# Regex patterns for common PII (structured data that can be reliably detected with patterns)
PII_PATTERNS = {
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
    "phone": re.compile(
        r"\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b"
    ),
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "credit_card": re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"),
    "ip_address": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    "uuid": re.compile(
        r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
    ),
}

# Mapping to store consistent anonymization across calls
_anonymization_cache: dict[str, dict[str, str]] = {}


def _generate_anonymous_value(original: str, pii_type: str, salt: str = "") -> str:
    """Generate a consistent anonymous value for a given original value.

    Args:
        original: The original PII value to anonymize.
        pii_type: The type of PII (email, phone, etc.).
        salt: Optional salt for the hash.

    Returns:
        An anonymized placeholder string.
    """
    cache_key = f"{pii_type}:{original}"

    if cache_key in _anonymization_cache.get(salt, {}):
        return _anonymization_cache[salt][cache_key]

    # Create a hash-based identifier for consistency
    hash_input = f"{salt}{original}".encode()
    hash_suffix = hashlib.sha256(hash_input).hexdigest()[:8]

    anonymous_value = f"[{pii_type.upper()}_{hash_suffix}]"

    if salt not in _anonymization_cache:
        _anonymization_cache[salt] = {}
    _anonymization_cache[salt][cache_key] = anonymous_value

    return anonymous_value


def replace_names_in_text(text: str, names: list[str], salt: str = "") -> dict:
    """Replace identified human names in text with anonymized placeholders.

    This tool is called by the agent after it has intelligently identified
    human names in the text. The agent uses its contextual understanding
    to determine what constitutes a name.

    Args:
        text: The text content containing names to anonymize.
        names: List of names identified by the agent to be replaced.
               Can include first names, last names, or full names.
        salt: Optional salt for consistent anonymization across calls.

    Returns:
        dict: Contains 'anonymized_text' and list of 'replaced_names'.
    """
    if not text:
        return {"status": "success", "anonymized_text": "", "replaced_names": []}

    if not names:
        return {"status": "success", "anonymized_text": text, "replaced_names": []}

    anonymized = text
    replaced = []

    # Sort names by length (longest first) to avoid partial replacements
    sorted_names = sorted(set(names), key=len, reverse=True)

    for name in sorted_names:
        if name in anonymized:
            anonymous_value = _generate_anonymous_value(name, "person_name", salt)
            anonymized = anonymized.replace(name, anonymous_value)
            replaced.append({"original": name, "replacement": anonymous_value})

    return {
        "status": "success",
        "anonymized_text": anonymized,
        "replaced_names": replaced,
        "names_found": len(replaced) > 0,
    }


def anonymize_pii_patterns(text: str, salt: str = "") -> dict:
    """Anonymize structured PII patterns in text.

    Detects and replaces common PII patterns (emails, phone numbers, SSNs,
    credit cards, IP addresses, UUIDs) with anonymized placeholders.

    Note: This does NOT detect human names. Use 'replace_names_in_text'
    after identifying names with your intelligence.

    Args:
        text: The text content to anonymize.
        salt: Optional salt to ensure consistent anonymization across calls.

    Returns:
        dict: Contains 'anonymized_text' and 'detections' (list of found PII types).
    """
    if not text:
        return {"status": "success", "anonymized_text": "", "detections": []}

    anonymized = text
    detections = []

    # Anonymize regex-based patterns
    for pii_type, pattern in PII_PATTERNS.items():
        matches = pattern.findall(anonymized)
        for match in matches:
            anonymous_value = _generate_anonymous_value(match, pii_type, salt)
            anonymized = anonymized.replace(match, anonymous_value)
            if pii_type not in detections:
                detections.append(pii_type)

    return {
        "status": "success",
        "anonymized_text": anonymized,
        "detections": detections,
        "pii_found": len(detections) > 0,
    }


def anonymize_identifiers(message: dict, salt: str = "") -> dict:
    """Anonymize identifier fields in a conversation history message.

    Anonymizes system identifiers in a message based on the DynamoDB
    history message schema. Does NOT anonymize content - use the agent's
    intelligence combined with 'replace_names_in_text' and
    'anonymize_pii_patterns' for content.

    Args:
        message: A message dictionary containing fields like 'content',
                 'message_id', 'thread_id', 'PK', etc.
        salt: Optional salt for consistent anonymization.

    Returns:
        dict: The anonymized message with a summary of anonymizations performed.
    """
    if not isinstance(message, dict):
        return {"status": "error", "error_message": "Message must be a dictionary"}

    anonymized_message = message.copy()
    anonymizations = []

    # Anonymize identifier fields
    id_fields = ["message_id", "thread_id", "org_id", "user_id", "tenant_id"]
    for field in id_fields:
        if field in message and message[field]:
            original_value = message[field]
            anonymized_message[field] = _generate_anonymous_value(
                original_value, field, salt
            )
            anonymizations.append(field)

    # Anonymize composite keys (PK, SK)
    if "PK" in message:
        anonymized_message["PK"] = _generate_anonymous_value(message["PK"], "pk", salt)
        anonymizations.append("PK")

    if "SK" in message:
        anonymized_message["SK"] = _generate_anonymous_value(message["SK"], "sk", salt)
        anonymizations.append("SK")

    if "SKMessage" in message:
        anonymized_message["SKMessage"] = _generate_anonymous_value(
            message["SKMessage"], "sk_message", salt
        )
        anonymizations.append("SKMessage")

    return {
        "status": "success",
        "anonymized_message": anonymized_message,
        "anonymizations_performed": anonymizations,
    }


def clear_anonymization_cache() -> dict:
    """Clear the anonymization cache.

    Clears the internal cache that maintains consistent anonymization mappings.
    Call this when you want to start fresh anonymization mappings.

    Returns:
        dict: Confirmation of cache clearing.
    """
    global _anonymization_cache
    cache_size = sum(len(v) for v in _anonymization_cache.values())
    _anonymization_cache = {}
    return {
        "status": "success",
        "message": f"Cleared {cache_size} cached anonymization mappings",
    }


anonymization_agent = Agent(
    name="anonymization_agent",
    model="gemini-2.0-flash",
    description="Agent that anonymizes PII and sensitive data in conversation history.",
    instruction=(
        "You are an anonymization agent specialized in protecting personally identifiable "
        "information (PII) in conversation data.\n\n"
        "YOUR WORKFLOW FOR ANONYMIZING TEXT:\n"
        "1. First, carefully read the text and use your intelligence to identify ALL human names "
        "(first names, last names, nicknames, full names). Consider context - names can appear "
        "in greetings ('Hi John'), signatures, references to people, etc.\n"
        "2. Call 'replace_names_in_text' with the text and the list of names you identified.\n"
        "3. Take the result and call 'anonymize_pii_patterns' to detect and replace structured "
        "PII (emails, phone numbers, SSNs, credit cards, IP addresses, UUIDs).\n\n"
        "FOR ANONYMIZING MESSAGE IDENTIFIERS:\n"
        "Use 'anonymize_identifiers' to anonymize system identifiers in message dictionaries "
        "(message_id, thread_id, org_id, user_id, tenant_id, PK, SK).\n\n"
        "IMPORTANT GUIDELINES:\n"
        "- Be thorough when identifying names - look for names from all cultures and backgrounds\n"
        "- Consider nicknames and informal name references\n"
        "- Names at the start of sentences may look like regular words - use context\n"
        "- Use the 'salt' parameter for consistent anonymization across multiple calls\n"
        "- The same salt + original value always produces the same anonymized placeholder\n\n"
        "TOOLS AVAILABLE:\n"
        "- 'replace_names_in_text': Replace names YOU identify in text\n"
        "- 'anonymize_pii_patterns': Detect/replace structured PII patterns\n"
        "- 'anonymize_identifiers': Anonymize message system identifiers\n"
        "- 'clear_anonymization_cache': Reset anonymization mappings"
    ),
    tools=[
        replace_names_in_text,
        anonymize_pii_patterns,
        anonymize_identifiers,
        clear_anonymization_cache,
    ],
)
