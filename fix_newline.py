with open('backend/app/services/session_manager.py', 'r') as f:
    content = f.read()

content = content.replace('full_transcript = "\n".join(session_transcript_buffer)', 'full_transcript = "\\n".join(session_transcript_buffer)')

with open('backend/app/services/session_manager.py', 'w') as f:
    f.write(content)
