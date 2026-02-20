import sys
import unittest
from unittest.mock import patch, MagicMock

# Define a context manager to simulate missing modules
class MissingModule:
    def __init__(self, modules):
        self.modules = modules
        self.original_modules = {}

    def __enter__(self):
        for module in self.modules:
            if module in sys.modules:
                self.original_modules[module] = sys.modules[module]
                del sys.modules[module]
            sys.modules[module] = None # Force ImportError

    def __exit__(self, exc_type, exc_val, exc_tb):
        for module in self.modules:
            del sys.modules[module] # Clean up None
            if module in self.original_modules:
                sys.modules[module] = self.original_modules[module]

class TestLazyLoading(unittest.TestCase):
    def test_import_main_without_google_cloud(self):
        """Test that app.main can be imported even if google.cloud.spanner is missing."""
        print("🛡️ Testing Lazy Import Protection...")

        # Simulate missing google.cloud
        with MissingModule(['google.cloud', 'google.cloud.spanner']):
            try:
                # We need to make sure we are not using cached modules from previous tests
                if 'app.main' in sys.modules:
                    del sys.modules['app.main']
                if 'app.repositories.spanner_graph' in sys.modules:
                    del sys.modules['app.repositories.spanner_graph']

                # Attempt import
                from app.main import app, get_soul_repository

                # Verify we got LocalRepo by default (since no env vars set for this test process)
                repo = get_soul_repository()
                print(f"✅ Repository Instantiated: {type(repo).__name__}")

                self.assertTrue("LocalSoulRepository" in type(repo).__name__)

            except ImportError as e:
                self.fail(f"Import failed with error: {e}")
            except Exception as e:
                self.fail(f"Unexpected error: {e}")

if __name__ == '__main__':
    unittest.main()
