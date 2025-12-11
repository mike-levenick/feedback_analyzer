"""Test script for the anonymization agent tools."""

from my_agent.sub_agents.anonymization_agent import (
    replace_names_in_text,
    anonymize_pii_patterns,
    anonymize_identifiers,
    clear_anonymization_cache,
)


def test_replace_names():
    """Test the replace_names_in_text function."""
    print("=" * 60)
    print("Testing replace_names_in_text")
    print("=" * 60)

    text = "Hello, my name is John Smith and I work with Sarah Johnson."
    names = ["John Smith", "Sarah Johnson"]

    result = replace_names_in_text(text, names, salt="test")
    print(f"Input: {text}")
    print(f"Names to replace: {names}")
    print(f"Output: {result['anonymized_text']}")
    print(f"Replaced: {result['replaced_names']}")
    print()


def test_anonymize_pii_patterns():
    """Test the anonymize_pii_patterns function."""
    print("=" * 60)
    print("Testing anonymize_pii_patterns")
    print("=" * 60)

    text = """
    Contact me at john.doe@example.com or call 555-123-4567.
    My SSN is 123-45-6789 and credit card is 4111-1111-1111-1111.
    Server IP: 192.168.1.1, Request ID: 550e8400-e29b-41d4-a716-446655440000
    """

    result = anonymize_pii_patterns(text, salt="test")
    print(f"Input: {text}")
    print(f"Output: {result['anonymized_text']}")
    print(f"Detected PII types: {result['detections']}")
    print()


def test_anonymize_identifiers():
    """Test the anonymize_identifiers function."""
    print("=" * 60)
    print("Testing anonymize_identifiers")
    print("=" * 60)

    message = {
        "PK": "org123#tenantA#user456#thread789",
        "SK": "MSG#0000000123456789012#msg_abc123",
        "SKMessage": "MSG#msg_abc123",
        "thread_id": "thread789",
        "message_id": "msg_abc123",
        "org_id": "org123",
        "user_id": "user456",
        "tenant_id": "tenantA",
        "content": "Hello, this is a test message.",
        "role": "user",
    }

    result = anonymize_identifiers(message, salt="test")
    print(f"Input message keys: {list(message.keys())}")
    print(f"Anonymized message:")
    for key, value in result["anonymized_message"].items():
        original = message.get(key, "N/A")
        if value != original:
            print(f"  {key}: {original} -> {value}")
        else:
            print(f"  {key}: {value} (unchanged)")
    print(f"Anonymizations performed: {result['anonymizations_performed']}")
    print()


def test_full_workflow():
    """Test the complete anonymization workflow as the agent would use it."""
    print("=" * 60)
    print("Testing Full Workflow (as agent would use it)")
    print("=" * 60)

    # Simulating what the agent would do:
    # 1. Agent reads text and identifies names
    # 2. Agent calls replace_names_in_text
    # 3. Agent calls anonymize_pii_patterns

    original_text = """
    Hi Dr. Martinez,

    I'm reaching out about the issue reported by Kevin O'Brien.
    You can contact him at kevin.obrien@company.com or 408-555-1234.
    
    His user ID in the system is usr_12345 and the incident was
    logged from IP 10.0.0.50.

    Best regards,
    Aisha Patel
    """

    print(f"Original text:{original_text}")

    # Step 1: Agent identifies names (simulating LLM intelligence)
    identified_names = ["Dr. Martinez", "Kevin O'Brien", "Aisha Patel"]
    print(f"Agent identified names: {identified_names}")

    # Step 2: Replace names
    result1 = replace_names_in_text(original_text, identified_names, salt="workflow")
    print(f"\nAfter name replacement:{result1['anonymized_text']}")

    # Step 3: Anonymize PII patterns
    result2 = anonymize_pii_patterns(result1["anonymized_text"], salt="workflow")
    print(f"After PII anonymization:{result2['anonymized_text']}")
    print(f"PII types detected: {result2['detections']}")
    print()


def test_consistency():
    """Test that the same input produces the same output with the same salt."""
    print("=" * 60)
    print("Testing Consistency (same salt = same output)")
    print("=" * 60)

    clear_anonymization_cache()

    text = "Contact John at john@example.com"
    names = ["John"]
    salt = "consistent"

    result1 = replace_names_in_text(text, names, salt=salt)
    result2 = replace_names_in_text(text, names, salt=salt)

    print(f"First call result: {result1['anonymized_text']}")
    print(f"Second call result: {result2['anonymized_text']}")
    print(f"Results match: {result1['anonymized_text'] == result2['anonymized_text']}")

    # Different salt should produce different output
    clear_anonymization_cache()
    result3 = replace_names_in_text(text, names, salt="different")
    print(f"Different salt result: {result3['anonymized_text']}")
    print(
        f"Different from original salt: {result1['anonymized_text'] != result3['anonymized_text']}"
    )
    print()


if __name__ == "__main__":
    test_replace_names()
    test_anonymize_pii_patterns()
    test_anonymize_identifiers()
    test_full_workflow()
    test_consistency()
    print("All tests completed!")
