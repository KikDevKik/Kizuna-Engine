with open('backend/app/services/audio_session.py', 'r') as f:
    content = f.read()

content = content.replace("AUDIO_BUFFER_THRESHOLD = 3200", "AUDIO_BUFFER_THRESHOLD = 2048")

with open('backend/app/services/audio_session.py', 'w') as f:
    f.write(content)
