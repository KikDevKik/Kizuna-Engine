import pytest
import asyncio
from app.services.auction_service import AuctionService

async def _reset_auction():
    auction = AuctionService()
    if auction._current_winner:
        await auction.release(auction._current_winner)
    # Force reset just in case
    auction._current_winner = None
    auction._current_score = 0.0
    # Check lock
    if auction._lock.locked():
        try:
            auction._lock.release()
        except RuntimeError:
            pass

@pytest.mark.asyncio
async def test_auction_singleton():
    await _reset_auction()
    s1 = AuctionService()
    s2 = AuctionService()
    assert s1 is s2
    assert s1._lock is s2._lock

@pytest.mark.asyncio
async def test_auction_bid_flow():
    await _reset_auction()
    auction = AuctionService()

    # Initial state
    assert auction._current_winner is None

    # Agent A wins
    success = await auction.bid("agent_A", 1.0)
    assert success is True
    assert auction._current_winner == "agent_A"

    # Agent A re-bids (should keep it)
    success = await auction.bid("agent_A", 1.5)
    assert success is True

    # Agent B tries to bid (should fail)
    success = await auction.bid("agent_B", 2.0)
    assert success is False
    assert auction._current_winner == "agent_A"

    # Agent A releases
    await auction.release("agent_A")
    assert auction._current_winner is None

    # Agent B can now win
    success = await auction.bid("agent_B", 0.5)
    assert success is True
    assert auction._current_winner == "agent_B"

@pytest.mark.asyncio
async def test_auction_interrupt():
    await _reset_auction()
    auction = AuctionService()

    await auction.bid("agent_C", 1.0)
    assert auction._current_winner == "agent_C"

    await auction.interrupt()
    assert auction._current_winner is None

    # Someone else can take it
    success = await auction.bid("agent_D", 1.0)
    assert success is True
