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


def replace_sensitive_values(
    text: str,
    values: list[dict],
    salt: str = "",
) -> dict:
    """Replace sensitive values identified by the agent in text.

    This is a general-purpose tool for replacing ANY sensitive information
    that the agent identifies using its intelligence. The agent determines
    what type each value is (name, username, serial, ID, etc.).

    Args:
        text: The text content containing sensitive values to anonymize.
        values: List of dicts, each with:
            - 'value': The sensitive string to replace
            - 'type': Category like 'person_name', 'username', 'serial_number',
                      'device_id', 'account_id', 'jss_id', 'user_id', 'custom_id', etc.
        salt: Optional salt for consistent anonymization across calls.

    Returns:
        dict: Contains 'anonymized_text' and list of 'replacements'.

    Example:
        values = [
            {"value": "John Smith", "type": "person_name"},
            {"value": "jsmith_42", "type": "username"},
            {"value": "PLVU929ESEF", "type": "serial_number"},
            {"value": "JSS-12345", "type": "jss_id"},
        ]
    """
    if not text:
        return {"status": "success", "anonymized_text": "", "replacements": []}

    if not values:
        return {"status": "success", "anonymized_text": text, "replacements": []}

    anonymized = text
    replacements = []

    # Sort by length (longest first) to avoid partial replacements
    sorted_values = sorted(values, key=lambda x: len(x.get("value", "")), reverse=True)

    for item in sorted_values:
        value = item.get("value", "")
        value_type = item.get("type", "sensitive_data")

        if value and value in anonymized:
            anonymous_value = _generate_anonymous_value(value, value_type, salt)
            anonymized = anonymized.replace(value, anonymous_value)
            replacements.append(
                {
                    "original": value,
                    "type": value_type,
                    "replacement": anonymous_value,
                }
            )

    return {
        "status": "success",
        "anonymized_text": anonymized,
        "replacements": replacements,
        "items_replaced": len(replacements),
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
        "You are an anonymization agent in a sequential pipeline. Your ONLY job is to "
        "anonymize the conversation data you receive and return the anonymized result. "
        "DO NOT attempt to delegate, transfer, or call other agents - just do the anonymization.\n\n"
        "YOUR WORKFLOW FOR ANONYMIZING TEXT:\n"
        "1. Carefully read the text and use your intelligence to identify ALL sensitive values:\n\n"
        "   HUMAN NAMES (type: 'person_name') - BE AGGRESSIVE:\n"
        "   - First names, last names, full names, nicknames\n"
        "   - SHORT/COMMON FIRST NAMES: Mike, Bob, Sam, Tom, Jim, Joe, Dan, Ben, Amy, Jen, etc.\n"
        "   - Names in greetings ('Hi Mike', 'Hello Jennifer'), signatures, casual references\n"
        "   - Names that appear standalone without 'Mr./Ms.' or last names\n"
        "   - Names from all cultures and backgrounds\n"
        "   - EVEN if it's just a first name with no context, treat it as a name!\n"
        "   - Example: 'Mike asked about...' -> 'Mike' is a person_name, anonymize it!\n\n"
        "   USERNAMES (type: 'username'):\n"
        "   - Account usernames like 'jsmith_42', 'user123', 'admin_bob'\n"
        "   - Login identifiers, screen names, handles\n\n"
        "   SERIAL NUMBERS (type: 'serial_number'):\n"
        "   - Device serials like 'PLVU929ESEF', 'SN-ABC123XYZ'\n"
        "   - Product codes, hardware identifiers\n"
        "   - Alphanumeric strings that look like serials\n\n"
        "   IDs (various types):\n"
        "   - JSS IDs (type: 'jss_id'): 'JSS-12345', device management IDs\n"
        "   - User IDs (type: 'user_id'): 'usr_abc123', numeric user IDs\n"
        "   - Account IDs (type: 'account_id'): customer/account numbers\n"
        "   - Device IDs (type: 'device_id'): 'DEV-001', machine identifiers\n"
        "   - Ticket IDs (type: 'ticket_id'): 'TKT-789', case numbers\n"
        "   - Any other IDs (type: 'custom_id')\n\n"
        "2. Call 'replace_sensitive_values' with the text and list of identified values.\n"
        "   Each value needs: {'value': 'the_text', 'type': 'category'}\n\n"
        "3. Take the result and call 'anonymize_pii_patterns' to detect structured PII\n"
        "   (emails, phone numbers, SSNs, credit cards, IP addresses, UUIDs).\n\n"
        "FOR ANONYMIZING MESSAGE IDENTIFIERS:\n"
        "Use 'anonymize_identifiers' for system fields in message dictionaries.\n\n"
        "PATTERN RECOGNITION (even WITHOUT labels like 'ID:' or 'serial:'):\n"
        "Look for these patterns ANYWHERE in text, even without context clues:\n\n"
        "- SERIAL NUMBERS: ALL CAPS alphanumeric 8-12 chars (PLVU929ESEF, C02X1234ABCD)\n"
        "  These often appear as bare strings without any label!\n"
        "- USERNAMES: lowercase with underscores/dots/numbers (john_doe, j.smith, user123)\n"
        "  Look for words that seem like account names, not regular English words\n"
        "- IDs WITH PREFIXES: JSS-12345, USR-789, DEV-001, TKT-456, ID-ABC123\n"
        "  Any WORD-NUMBER or LETTERS-NUMBERS pattern could be an ID\n"
        "- NUMERIC IDS: Standalone numbers 4+ digits that aren't dates/times (12345, 98765)\n"
        "- ALPHANUMERIC CODES: Mixed letter-number strings (A1B2C3, XYZ789, 2FA5BC)\n\n"
        "CRITICAL: Do NOT wait for labels like 'serial number:' or 'username:'\n"
        "Instead, recognize the PATTERN ITSELF:\n"
        "- 'Check device PLVU929ESEF' -> PLVU929ESEF is a serial (ALL CAPS alphanumeric)\n"
        "- 'User jsmith_42 reported' -> jsmith_42 is a username (underscore pattern)\n"
        "- 'Ticket 78234 was closed' -> 78234 could be a ticket ID\n"
        "- 'Machine C02DM1XDFVH4' -> C02DM1XDFVH4 is a serial (Apple-style)\n\n"
        "When in doubt, anonymize it - false positives are safer than leaking data!\n\n"
        "TOOLS:\n"
        "- 'replace_sensitive_values': Replace ANY sensitive values you identify\n"
        "- 'anonymize_pii_patterns': Auto-detect structured PII patterns\n"
        "- 'anonymize_identifiers': Anonymize message system identifiers\n"
        "- 'clear_anonymization_cache': Reset anonymization mappings\n\n"
        "CRITICAL SECURITY RULES:\n"
        "- NEVER repeat, quote, or echo original sensitive data in your responses\n"
        "- NEVER say things like 'I found the name John Smith' - that leaks PII!\n"
        "- NEVER list the sensitive values you found in plain text\n"
        "- Only speak about data AFTER it has been anonymized\n"
        "- Your output should ONLY contain anonymized placeholders like [PERSON_NAME_xxx]\n"
        "- If you need to reference something you're anonymizing, use '***' or '[REDACTED]'\n\n"
        "CORRECT: 'I anonymized 5 names and 3 IDs. Here is the result: ...'\n"
        "WRONG: 'I found Jennifer Martinez, so I will replace it...' <- LEAKS DATA!\n\n"
        "PIPELINE BEHAVIOR:\n"
        "After anonymizing, return ONLY the anonymized conversation. Do not attempt "
        "to call other agents or delegate."
    ),
    tools=[
        replace_sensitive_values,
        anonymize_pii_patterns,
        anonymize_identifiers,
        clear_anonymization_cache,
    ],
)
