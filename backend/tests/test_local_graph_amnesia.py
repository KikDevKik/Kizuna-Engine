import pytest
import asyncio
from pathlib import Path
from app.repositories.local_graph import LocalSoulRepository
from app.models.graph import MemoryEpisodeNode

@pytest.mark.asyncio
async def test_verbatim_priority_amnesia_fix():
    """
    Test that 'Verbatim Priority' works:
    Summaries should not displace raw transcripts in get_recent_episodes.
    """
    # Setup
    temp_graph_path = Path("backend/data/test_amnesia_graph.json")
    if temp_graph_path.exists():
        temp_graph_path.unlink()

    repo = LocalSoulRepository(data_path=temp_graph_path)
    await repo.initialize()

    user_id = "test_user"
    await repo.get_or_create_user(user_id)

    # 1. Create Raw Episode 1
    await repo.save_episode(
        user_id=user_id,
        agent_id="ai",
        summary="Summary 1",
        valence=0.1,
        raw_transcript="Raw 1"
    )

    # 2. Create Raw Episode 2
    raw2 = await repo.save_episode(
        user_id=user_id,
        agent_id="ai",
        summary="Summary 2",
        valence=0.1,
        raw_transcript="Raw 2"
    )

    # 3. Create Summary Episode (No raw transcript)
    summary_node = MemoryEpisodeNode(
        summary="Consolidated Summary",
        emotional_valence=1.0
    )
    repo.episodes[summary_node.id] = summary_node
    repo.experienced[user_id].append(summary_node.id)
    await repo._save()

    # 4. Fetch Limit=2
    # Expect: Raw 1, Raw 2 (Summary skipped)
    recent = await repo.get_recent_episodes(user_id, limit=2)

    assert len(recent) == 2
    assert recent[0].raw_transcript == "Raw 1"
    assert recent[1].raw_transcript == "Raw 2"

    # 5. Fetch Limit=3
    # Expect: Raw 1, Raw 2, Summary (Backfill)
    # Wait, in my backfill logic:
    # Collected Raw: [Raw 2, Raw 1] (reversed scan) -> [Raw 1, Raw 2] (sorted)
    # Need 1 more.
    # Collected Summary: [Summary]
    # Result: [Raw 1, Raw 2, Summary] -> Sorted by timestamp

    recent_3 = await repo.get_recent_episodes(user_id, limit=3)
    assert len(recent_3) == 3

    # Verify content
    has_raw1 = any(e.raw_transcript == "Raw 1" for e in recent_3)
    has_raw2 = any(e.raw_transcript == "Raw 2" for e in recent_3)
    has_summary = any(e.summary == "Consolidated Summary" for e in recent_3)

    assert has_raw1
    assert has_raw2
    assert has_summary

    # Cleanup
    if temp_graph_path.exists():
        temp_graph_path.unlink()

@pytest.mark.asyncio
async def test_backfill_logic():
    """
    Test that backfill works when raw transcripts are scarce.
    """
    temp_graph_path = Path("backend/data/test_backfill_graph.json")
    if temp_graph_path.exists():
        temp_graph_path.unlink()

    repo = LocalSoulRepository(data_path=temp_graph_path)
    await repo.initialize()
    user_id = "test_user_2"

    # 1. Summary 1
    sum1 = MemoryEpisodeNode(summary="Old 1", emotional_valence=0.0)
    repo.episodes[sum1.id] = sum1
    repo.experienced.setdefault(user_id, []).append(sum1.id)
    await asyncio.sleep(0.01)

    # 2. Summary 2
    sum2 = MemoryEpisodeNode(summary="Old 2", emotional_valence=0.0)
    repo.episodes[sum2.id] = sum2
    repo.experienced[user_id].append(sum2.id)
    await asyncio.sleep(0.01)

    # 3. Raw 1
    raw1 = await repo.save_episode(
        user_id=user_id,
        agent_id="ai",
        summary="Raw 1",
        valence=0.1,
        raw_transcript="Raw content"
    )

    # Fetch Limit=2
    # Expect: Raw 1 + Summary 2 (Most recent summary)
    recent = await repo.get_recent_episodes(user_id, limit=2)

    assert len(recent) == 2
    assert any(e.id == raw1.id for e in recent)
    assert any(e.id == sum2.id for e in recent)
    assert not any(e.id == sum1.id for e in recent)

    # Cleanup
    if temp_graph_path.exists():
        temp_graph_path.unlink()
