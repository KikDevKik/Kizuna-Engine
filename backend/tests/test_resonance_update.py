
import unittest
from unittest.mock import MagicMock, AsyncMock, patch
import asyncio
import sys
import os
from datetime import datetime

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.repositories.spanner_graph import SpannerSoulRepository
from app.models.graph import ResonanceEdge

class TestResonanceUpdate(unittest.TestCase):
    def setUp(self):
        # Patch spanner import before it's used
        self.mock_spanner_module = MagicMock()
        self.mock_client_cls = MagicMock()
        self.mock_spanner_module.Client = self.mock_client_cls
        self.mock_spanner_module.param_types = MagicMock()

        # Patching at module level where it is imported in spanner_graph.py
        self.patcher = patch("app.repositories.spanner_graph.spanner", self.mock_spanner_module)
        self.patcher.start()

        self.repo = SpannerSoulRepository()
        self.repo.database = MagicMock() # Mock database directly

    def tearDown(self):
        self.patcher.stop()

    def test_update_resonance_merge_structure(self):
        """Test that update_resonance attempts a MERGE query."""
        async def run_test():
            # Mock transaction
            mock_tx = MagicMock()

            # Mock run_in_transaction to execute the callback with mock_tx
            def side_effect(func):
                func(mock_tx)
                return "success"

            self.repo.database.run_in_transaction.side_effect = side_effect

            # Mock get_resonance to return something valid
            with patch.object(self.repo, 'get_resonance', new_callable=AsyncMock) as mock_get:
                mock_get.return_value = ResonanceEdge(source_id="u1", target_id="a1", affinity_level=55.0)

                await self.repo.update_resonance("u1", "a1", 5.0)

                # Check that run_in_transaction was called once (success path)
                self.assertEqual(self.repo.database.run_in_transaction.call_count, 1)

                # Check that execute_update was called with MERGE
                mock_tx.execute_update.assert_called()
                args, _ = mock_tx.execute_update.call_args
                query = args[0]

                if "MERGE" in query:
                    print("✅ MERGE query found.")
                    # Check for CASE statement for clamping
                    assert "CASE" in query, "Query must include CASE for clamping"
                else:
                    self.fail("MERGE query NOT found.")

        asyncio.run(run_test())

    def test_update_resonance_fallback(self):
        """Test fallback to Check-Then-Act (New Transaction) when MERGE fails."""
        async def run_test():
            mock_tx = MagicMock()

            # We need run_in_transaction to behave differently on consecutive calls
            # Call 1: Execute MERGE callback -> Raises Exception
            # Call 2: Execute Fallback callback -> Succeeds

            def side_effect(func):
                return func(mock_tx)

            self.repo.database.run_in_transaction.side_effect = side_effect

            # Mock transaction operations
            # 1. MERGE (execute_update) -> Fails
            # 2. Check (execute_sql) -> Returns []
            # 3. Create (execute_update) -> Succeeds

            mock_tx.execute_update.side_effect = [
                Exception("Syntax Error: MERGE not supported"), # 1. MERGE fails
                None # 2. CREATE succeeds
            ]

            mock_tx.execute_sql.return_value = [] # Fallback check returns empty

            with patch.object(self.repo, 'get_resonance', new_callable=AsyncMock) as mock_get:
                mock_get.return_value = ResonanceEdge(source_id="u1", target_id="a1", affinity_level=50.0)

                await self.repo.update_resonance("u1", "a1", 10.0)

                # Verify 2 calls to run_in_transaction (Attempt 1 + Attempt 2)
                self.assertEqual(self.repo.database.run_in_transaction.call_count, 2)

                # Verify queries in order
                # We can't easily check order across different calls to execute_update if we don't inspect call_args_list carefully
                calls = mock_tx.execute_update.call_args_list
                self.assertEqual(len(calls), 2)

                first_query = calls[0][0][0]
                second_query = calls[1][0][0]

                self.assertIn("MERGE", first_query)
                self.assertIn("CREATE", second_query) # It should fallback to CREATE

                print("✅ Fallback (New Transaction) verified.")

        asyncio.run(run_test())

if __name__ == "__main__":
    unittest.main()
