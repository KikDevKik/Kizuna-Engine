with open('backend/app/services/session_manager.py', 'r') as f:
    content = f.read()

content = content.replace("from app.services.cache import cache", "from app.services.cache import cache\nfrom app.services.auction_service import AuctionService")

with open('backend/app/services/session_manager.py', 'w') as f:
    f.write(content)
