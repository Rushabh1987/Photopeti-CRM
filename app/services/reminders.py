"""Reminder engine — rule evaluator (Phase 4).

evaluate(db): for each open entity x rule, if the condition holds and the last
reminder for (entity, rule_key) is older than the rule's cooldown, send via
Telegram and log a Reminder row. When the owner resolves the condition the rule
stops matching, so reminders stop automatically — no cancellation needed.

Rules: lead_unreplied_2h, editing_not_started_24h, editing_pending_3d,
payment_pending_5d, video_waiting_24h.
"""
# TODO(Phase 4): RULES table + evaluate(db)
