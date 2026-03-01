with open('backend/app/services/auction_service.py', 'r') as f:
    content = f.read()

import re

# Remove the Singleton __new__ method entirely
pattern_new = r"    def __new__\(cls\):.*?        return cls\._instance\n"
content = re.sub(pattern_new, "", content, flags=re.DOTALL)

# Add __init__ instead
init_code = """
    def __init__(self):
        self._lock = asyncio.Lock()
        self._current_winner: Optional[str] = None
        self._current_score: float = 0.0
        self._last_user_activity: float = 0.0
        self._user_priority_window: float = 0.5  # 500ms grace period
"""
content = content.replace("    _instance = None\n", init_code)

# Remove Singleton Instance at the bottom
content = content.replace("# Singleton Instance\nauction_service = AuctionService()\n", "")

with open('backend/app/services/auction_service.py', 'w') as f:
    f.write(content)
