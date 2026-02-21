import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import sys
import os
from datetime import datetime

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Set Env Vars for Test
os.environ["GCP_PROJECT_ID"] = "mock-project"
os.environ["SPANNER_INSTANCE_ID"] = "mock-instance"
os.environ["SPANNER_DATABASE_ID"] = "mock-db"

from app.repositories.spanner_graph import SpannerSoulRepository
from app.models.graph import DreamNode, MemoryEpisodeNode

@pytest.mark.asyncio
async def test_consolidate_memories_flow():
    """
    Test the full flow of Spanner memory consolidation:
    1. Fetch Episodes
    2. Fetch Resonance
    3. Generate Dream
    4. Calculate EMA
    5. Execute Transaction
    """
    print("\n🧪 Testing Spanner Consolidation Flow...")

    with patch("google.cloud.spanner.Client") as MockClient:
        # --- 1. Setup Mocks ---
        mock_client_instance = MockClient.return_value
        mock_spanner_instance = mock_client_instance.instance.return_value
        mock_database = mock_spanner_instance.database.return_value

        repo = SpannerSoulRepository()
        await repo.initialize()

        # Mock Snapshot (for Reads)
        mock_snapshot = MagicMock()
        mock_database.snapshot.return_value.__enter__.return_value = mock_snapshot

        # Mock Data: 2 Episodes
        # Query 1: Fetch Episodes
        # Row: [id, summary, valence]
        episodes_data = [
            ['ep-1', 'User was happy', 0.8],
            ['ep-2', 'User was neutral', 0.0]
        ]

        # Mock Data: 1 Resonance
        # Query 2: Fetch Resonance
        # Row: [agent_id, affinity_level, shared_memories]
        # Agent shares BOTH episodes
        resonance_data = [
            ['agent-kizuna', 50.0, ['ep-1', 'ep-2']]
        ]

        # Configure execute_sql side effects based on query content
        def execute_sql_side_effect(query, params=None, param_types=None):
            if "MATCH (u:User {id: @uid})-[:EXPERIENCED]->(e:Episode)" in query:
                return episodes_data
            if "MATCH (u:User {id: @uid})-[r:HAS_RESONANCE]->(a:Agent)" in query:
                return resonance_data
            return []

        mock_snapshot.execute_sql.side_effect = execute_sql_side_effect

        # Mock Dream Generator
        mock_dream_gen = AsyncMock()
        mock_dream_gen.return_value = DreamNode(
            id="dream-123", theme="Joy", intensity=0.9, surrealism_level=0.4
        )

        # Mock Transaction (for Writes)
        # We need to capture the transaction function passed to run_in_transaction
        # and execute it with a mock transaction object.
        mock_tx = MagicMock()

        def run_in_transaction_side_effect(func):
            return func(mock_tx)

        mock_database.run_in_transaction.side_effect = run_in_transaction_side_effect

        # --- 2. Execute ---
        await repo.consolidate_memories("user-123", dream_generator=mock_dream_gen)

        # --- 3. Verify Reads ---
        print("✅ Verifying Reads...")
        assert mock_snapshot.execute_sql.call_count == 2

        # --- 4. Verify Logic (EMA) ---
        # Episodes: 0.8, 0.0 -> Avg: 0.4
        # Target: 50 + (0.4 * 50) = 50 + 20 = 70.0
        # Old Affinity: 50.0
        # Alpha: 0.15
        # New Affinity = (70.0 * 0.15) + (50.0 * 0.85)
        #              = 10.5 + 42.5 = 53.0
        expected_affinity = 53.0

        print(f"✅ Expected Affinity Calculation: {expected_affinity}")

        # --- 5. Verify Writes ---
        print("✅ Verifying Transaction Writes...")
        assert mock_database.run_in_transaction.called

        # Check execute_update calls in the transaction
        # We expect:
        # 1. Create Dream
        # 2. Link Shadow
        # 3. Update Affinity (for agent-kizuna)
        # 4. Archive ep-1
        # 5. Archive ep-2

        calls = mock_tx.execute_update.call_args_list
        assert len(calls) >= 5

        # Verify Dream Creation
        dream_call = [c for c in calls if "CREATE (:Dream" in c[0][0]]
        assert dream_call, "Dream creation query missing"
        assert dream_call[0][1]['params']['theme'] == "Joy"

        # Verify Shadow Link
        shadow_call = [c for c in calls if "CREATE (u)-[:SHADOW" in c[0][0]]
        assert shadow_call, "Shadow edge creation missing"

        # Verify Affinity Update
        affinity_call = [c for c in calls if "SET r.affinity_level = @new_aff" in c[0][0]]
        assert affinity_call, "Affinity update query missing"

        actual_new_aff = affinity_call[0][1]['params']['new_aff']
        print(f"✅ Actual Updated Affinity sent to DB: {actual_new_aff}")
        assert abs(actual_new_aff - expected_affinity) < 0.001

        # Verify Archival
        archive_calls = [c for c in calls if "SET e.valence = 999.0" in c[0][0]]
        assert len(archive_calls) == 2, "Should archive 2 episodes"
        archived_ids = [c[1]['params']['eid'] for c in archive_calls]
        assert "ep-1" in archived_ids
        assert "ep-2" in archived_ids

    print("🎉 Test Complete: Spanner Consolidation Logic Verified.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_consolidate_memories_flow())
