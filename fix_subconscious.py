with open('backend/app/services/subconscious.py', 'r') as f:
    content = f.read()

# Add cleanup method
cleanup_method = """
    def cleanup(self, user_id: str):
        \"\"\"Removes the user session and clears the buffer.\"\"\"
        if user_id in self.active_sessions:
            del self.active_sessions[user_id]
        self.buffer.clear()
        logger.info(f"Subconscious cleaned for {user_id}")
"""

# Find where to insert it, maybe after start method
# Actually, just put it before generate_dream
content = content.replace('    async def generate_dream(', cleanup_method + '\n    async def generate_dream(')

with open('backend/app/services/subconscious.py', 'w') as f:
    f.write(content)
