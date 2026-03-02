with open('./backend/app/services/audio_session.py', 'r') as f:
    content = f.read()

old_block = """                if len(audio_buffer) >= AUDIO_BUFFER_THRESHOLD:
                    try:
                        await session.send(input={"data": bytes(audio_buffer), "mime_type": "audio/pcm;rate=16000"})
                        audio_buffer.clear()"""

new_block = """                if len(audio_buffer) >= AUDIO_BUFFER_THRESHOLD:
                    try:
                        logger.info(f"📤 Sending audio packet: {len(audio_buffer)} bytes")
                        await session.send(input={"data": bytes(audio_buffer), "mime_type": "audio/pcm;rate=16000"})
                        audio_buffer.clear()"""

if old_block in content:
    content = content.replace(old_block, new_block)
    with open('./backend/app/services/audio_session.py', 'w') as f:
        f.write(content)
    print("Replaced successfully")
else:
    print("Block not found")
