import asyncio
import logging
import sys
import os
from unittest.mock import MagicMock, AsyncMock, patch

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Set Env Vars for Test (Simulate Prod)
os.environ["GCP_PROJECT_ID"] = "mock-project"
os.environ["SPANNER_INSTANCE_ID"] = "mock-instance"
os.environ["SPANNER_DATABASE_ID"] = "mock-db"
os.environ["FIREBASE_CREDENTIALS"] = "{}" # Mock JSON

from app.repositories.spanner_graph import SpannerSoulRepository
from app.services.auth import FirebaseAuth

async def test_spanner_mock():
    print("🕸️  Testing Spanner Repository Logic (with Mocks)...")

    # 1. Mock Spanner Client
    with patch("google.cloud.spanner.Client") as MockClient:
        # Setup Mock Hierarchy
        mock_client_instance = MockClient.return_value
        mock_spanner_instance = mock_client_instance.instance.return_value
        mock_database = mock_spanner_instance.database.return_value

        # Initialize Repo
        repo = SpannerSoulRepository()
        await repo.initialize()
        print("✅ Spanner Client Initialized (Mocked).")

        # Test: get_or_create_user
        # Mock Snapshot Context Manager
        mock_snapshot = MagicMock()
        mock_database.snapshot.return_value.__enter__.return_value = mock_snapshot

        # Case A: User Exists
        # Mock result row: [id, name, created_at]
        mock_snapshot.execute_sql.return_value = [['user-123', 'Test User', '2025-01-01']]

        user = await repo.get_or_create_user("user-123")
        print(f"✅ User Retrieved: {user.name}")
        assert user.id == "user-123"

        # Case B: User Does Not Exist (Simulate empty result then transaction)
        mock_snapshot.execute_sql.return_value = [] # Empty result

        # Mock Transaction
        def run_tx_side_effect(func):
            tx = MagicMock()
            return func(tx)

        mock_database.run_in_transaction.side_effect = run_tx_side_effect

        new_user = await repo.get_or_create_user("new-user-456", "New Guy")
        print(f"✅ User Created via Transaction: {new_user.name}")

        # Verify transaction.execute_update was called
        # We need to capture the transaction object passed to the function
        # But run_in_transaction calls the function.
        # Check if run_in_transaction was called
        mock_database.run_in_transaction.assert_called()

async def test_firebase_mock():
    print("\n🔥 Testing Firebase Auth (with Mocks)...")

    # Mock verify_id_token
    with patch("firebase_admin.auth.verify_id_token") as mock_verify:
        # Mock credentials loading to avoid parsing error
        with patch("firebase_admin.credentials.Certificate") as MockCert:
            # Mock initialize_app to do nothing
            with patch("firebase_admin.initialize_app"):
                # Force re-initialization for test
                FirebaseAuth._initialized = False
                FirebaseAuth.initialize()

                # Case A: Valid Token
                mock_verify.return_value = {"uid": "firebase-user-777"}
                uid = FirebaseAuth.verify_token("valid-token")
                print(f"✅ Verified Token -> UID: {uid}")
                assert uid == "firebase-user-777"

        # Case B: Invalid Token
        mock_verify.side_effect = ValueError("Expired")
        try:
            FirebaseAuth.verify_token("bad-token")
            print("❌ Failed: Should have raised ValueError")
        except ValueError:
             print("✅ Correctly rejected invalid token.")

    print("\n🏁 Phase 3.2 Verification Complete.")

if __name__ == "__main__":
    asyncio.run(test_spanner_mock())
    asyncio.run(test_firebase_mock())
