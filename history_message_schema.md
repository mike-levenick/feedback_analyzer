# DynamoDB History Message Schema

This document describes the DynamoDB schema used for conversation history messages.

## Location
- Model definitions: [assistant/database/schema.py](assistant/database/schema.py#L1-L200)

## PK / SK Patterns
- PK: `{org_id}[#{tenant_id}]#{user_id}#{thread_id}` (tenant segment optional)
- SK (message items): `MSG#{timestamp:019d}#{message_id}` or `LLM#{timestamp:019d}#{message_id}`
- SKMessage: `MSG#{message_id}` or `LLM#{message_id}` (GSI attribute)
- Thread SK (metadata): `THREAD#{thread_id}` and `SKTimestampThread = THREAD#{timestamp}#{thread_id}`

## Indexes
- `PK-SKMessage-index-v1` — GSI for `PK` + `SKMessage` (named `MESSAGE_ID_INDEX_NAME` in code)
- `PK-SKTimestampThread-index-v1` — GSI for thread timestamp sorting (named `TIMESTAMP_THREAD_INDEX_NAME`)

## Core Attributes (message items)
- `PK`: string — partition key
- `SK`: string — sort key (message or thread)
- `SKMessage`: string — `MSG#id` or `LLM#id`
- `ExpiryTime`: int — TTL epoch seconds
- `thread_id`: string
- `timestamp`: int
- `message_id`: string
- `content`: string | list[string | dict | Any]
- `stop_reason`: Optional[string]
- `role`: `"user"` or `"assistant"`
- `response_metadata`: Optional[dict] (assistant messages)
- `verso`: Optional[`Verso`] — `"up"` or `"down"` feedback direction (set via `set_feedback_verso()`)
- `feedback`: Optional[string] — optional freeform feedback/comment set via `set_feedback_comment()`
- `sources`: Optional[list[Source]]
- `created_at`, `updated_at`: string timestamps

## Thread metadata (`ThreadMetadata`)
- `PK`, `SK` (`THREAD#{thread_id}`), `SKTimestampThread`, `ExpiryTime`
- `org_id`, `user_id`, `origin`, `is_temporary`, `title`, `created_at`, `updated_at`, `user_message_count`
- `SKTimestampThread`: string — `THREAD#{timestamp}#{thread_id}` used by the `PK-SKTimestampThread-index-v1` GSI to sort threads by time

## Notes
- Message SK uses zero-padded timestamps (`:019d`) so lexicographic order equals chronological order.
- `ExpiryTime` is used as a DynamoDB TTL attribute; temporary threads use a shorter expiry.
- `content` may be a plain string or a structured list/object — frontends should handle both.

## Example (simplified) message item
```json
{
  "PK": "org123#tenantA#user456#thread789",
  "SK": "MSG#0000000123456789012#msg_abc123",
  "SKMessage": "MSG#msg_abc123",
  "ExpiryTime": 1740000000,
  "thread_id": "thread789",
  "message_id": "msg_abc123",
  "timestamp": 1234567890123,
  "content": "Here's an example with an apostrophe",
  "verso": "up",
  "feedback": "Helpful answer",
  "role": "user",
  "created_at": "2025-12-10T12:34:56",
  "updated_at": "2025-12-10T12:34:56"
}
```
