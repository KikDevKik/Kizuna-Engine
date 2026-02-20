
import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Set environment variables GLOBALLY for the process before imports
# We use mock-api-key to prevent startup crash
os.environ["GEMINI_API_KEY"] = "mock-api-key"
os.environ["GCP_PROJECT_ID"] = "prod-project"
os.environ["FIREBASE_CREDENTIALS"] = ""

# Patch gemini_service to avoid real connection attempts
with patch("app.services.gemini_live.gemini_service") as mock_gemini:
    from app import main

class TestSecurityAuth(unittest.TestCase):

    def test_verify_user_prod_enforcement(self):
        """
        SECURITY TEST: Ensure that Production environment STRICTLY enforces authentication.
        If GCP_PROJECT_ID is set but FIREBASE_CREDENTIALS are missing,
        providing a token must result in a rejection (ValueError), NOT guest access.
        """

        # Mock settings in main to reflect the vulnerable configuration
        with patch.object(main.settings, 'GCP_PROJECT_ID', "prod-project"), \
             patch.object(main.settings, 'FIREBASE_CREDENTIALS', ""), \
             patch("app.services.auth.FirebaseAuth", create=True):

            print("\n--- Testing Security: Auth Enforcement in Production ---")
            token = "some-random-token"

            # This should RAISE ValueError due to misconfiguration
            # It should NOT return "guest_user"
            with self.assertRaises(ValueError) as cm:
                main.verify_user(token)

            self.assertIn("Server Misconfiguration", str(cm.exception))
            print("✅ CORRECT BEHAVIOR: Server rejected insecure configuration.")

    def test_verify_user_dev_fallback(self):
        """
        Verify that Development environment (No GCP_PROJECT_ID) allows guest access.
        """
        with patch.object(main.settings, 'GCP_PROJECT_ID', ""), \
             patch.object(main.settings, 'FIREBASE_CREDENTIALS', ""):

            print("\n--- Testing Security: Dev Mode Fallback ---")
            user = main.verify_user(None)
            self.assertEqual(user, "guest_user")
            print("✅ CORRECT BEHAVIOR: Dev mode allowed guest access.")

if __name__ == '__main__':
    unittest.main()
