with open('backend/app/services/session_manager.py', 'r') as f:
    content = f.read()

# I need to add `auction_service = AuctionService()` where I planned it.
content = content.replace("        # Master Session Logger: Global Transcript Accumulation", "        # Phase 2.1: Isolate Session Auction\\n        auction_service = AuctionService()\\n\\n        # Master Session Logger: Global Transcript Accumulation")

# I also need to ensure AuctionService is imported!
if "from .auction_service import AuctionService" not in content:
    content = content.replace("from .sleep_manager import sleep_manager", "from .sleep_manager import sleep_manager\nfrom .auction_service import AuctionService")

with open('backend/app/services/session_manager.py', 'w') as f:
    f.write(content.replace("\\n", "\n"))
