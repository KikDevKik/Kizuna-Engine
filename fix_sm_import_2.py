with open('backend/app/services/session_manager.py', 'r') as f:
    content = f.read()

content = content.replace("from .sleep_manager import sleep_manager", "from .sleep_manager import sleep_manager\nfrom .auction_service import AuctionService")

with open('backend/app/services/session_manager.py', 'w') as f:
    f.write(content)
