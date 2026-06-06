"""Instagram Messaging API integration (Phase 2).

verify_token(...)         -> Meta GET handshake
parse_webhook(payload)    -> normalized (sender, text, raw)
send_reply(recipient, text) -> POST to Graph API (24h window applies)
Requires a Professional account + Facebook Page + approved Meta app.
"""
# TODO(Phase 2)
