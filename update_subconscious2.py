import re

with open("backend/app/services/subconscious.py", "r") as f:
    content = f.read()

# Update logging to clarify why flashback happened
search_pattern = """
                            whisper = (
                                f"🧠 [Flashback]: The user's current topic relates to a past memory: "
                                f"{episode.summary}. Use this context naturally."
                            )
                            logger.info(f"🧠 Memory Retrieved: {episode.summary}")
"""

replace_pattern = """
                            whisper = (
                                f"🧠 [Flashback]: The user's current topic relates to a past memory: "
                                f"{episode.summary}. Use this context naturally."
                            )
                            logger.info(f"🧠 Flashback triggered by temporal reference: '{full_text[:50]}...'")
                            logger.info(f"🧠 Memory Retrieved: {episode.summary}")
"""

content = content.replace(search_pattern, replace_pattern)

with open("backend/app/services/subconscious.py", "w") as f:
    f.write(content)
