with open('backend/app/services/session_manager.py', 'r') as f:
    content = f.read()

# Add auction_service param
content = content.replace("websocket, session, session_transcript_buffer, transcript_queue", "websocket, session, auction_service, session_transcript_buffer, transcript_queue")
content = content.replace("websocket,\n                                session,\n                                transcript_queue,", "websocket,\n                                session,\n                                auction_service,\n                                transcript_queue,")

# Also add the subconscious cleanup
content = content.replace("            logger.info(\"WebSocket session closed.\")", "            logger.info(\"WebSocket session closed.\")\n            subconscious_mind.cleanup(user_id)")

with open('backend/app/services/session_manager.py', 'w') as f:
    f.write(content)
