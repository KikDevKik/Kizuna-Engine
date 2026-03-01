with open('backend/app/services/session_manager.py', 'r') as f:
    content = f.read()

import re

# Add AuctionService instantiation and usage
# 1. Update imports if needed
if "AuctionService" not in content:
    content = content.replace("from .auction_service import auction_service", "from .auction_service import AuctionService")

# 2. Before the session loop starts
auction_init = """
        # Phase 2.1: Isolate Session Auction
        auction_service = AuctionService()
"""
# Insert before Master Session Logger
content = content.replace("        # Master Session Logger: Global Transcript Accumulation", auction_init + "\n        # Master Session Logger: Global Transcript Accumulation")

# 3. Pass auction_service to audio_session methods in session_manager
# Actually, audio_session.py functions send_to_gemini and receive_from_gemini import auction_service globally
# I need to modify audio_session.py to accept auction_service as a parameter too!
