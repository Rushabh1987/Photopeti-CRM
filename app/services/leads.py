"""Lead service — the single funnel every channel flows through.

upsert_from_channel(): match a client by instagram/phone (else create),
append the message to conversation history, reuse an open lead or create a
new one, and refresh last_activity_at. Implemented in Phase 1/2.
"""
# TODO(Phase 1): create/list/update leads + clients
# TODO(Phase 2): upsert_from_channel(db, source, channel, sender, body, raw)
