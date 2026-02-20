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

class TestTotalShielding(unittest.TestCase):
    def test_import_main_minimal_boot(self):
        """Test that app.main can be imported without GCP, Firebase, or Redis libs."""
        print("🛡️ Testing Minimal Boot (Total Shielding)...")

        missing_libs = [
            'google.cloud', 'google.cloud.spanner',
            'firebase_admin', 'firebase_admin.auth',
            'redis', 'redis.asyncio'
        ]

        with MissingModule(missing_libs):
            try:
                # Force reload of main and deps
                modules_to_unload = [
                    'app.main', 'app.services.auth', 'app.services.cache',
                    'app.repositories.spanner_graph', 'app.routers.warmup'
                ]
                for m in modules_to_unload:
                    if m in sys.modules:
                        del sys.modules[m]

                from app.main import app, get_soul_repository

                # Check Repo
                repo = get_soul_repository()
                print(f"✅ Boot Success. Repo: {type(repo).__name__}")
                self.assertTrue("LocalSoulRepository" in type(repo).__name__)

                # Check Auth Service Import safety
                from app.services.auth import FirebaseAuth
                # Should not crash even if libs missing
                FirebaseAuth.initialize() # Should log error but not crash
                print("✅ Auth Service loaded safely.")

                # Check Cache Service Import safety
                from app.services.cache import RedisCache
                cache = RedisCache()
                # await cache.initialize() # async, skip for unit test or mock loop
                print("✅ Cache Service loaded safely.")

            except ImportError as e:
                self.fail(f"Import failed with error: {e}")
            except Exception as e:
                self.fail(f"Unexpected error: {e}")

if __name__ == '__main__':
    unittest.main()
