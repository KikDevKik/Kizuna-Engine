import sys
import asyncio
import json
import os
from pathlib import Path

# Add the .venv site-packages to sys.path
venv_site_packages = Path("/c/Users/User/kizuna-engine/.venv/Lib/site-packages")
if venv_site_packages.exists():
    sys.path.insert(0, str(venv_site_packages))

# Ensure backend directory is in sys.path
backend_dir = Path("/c/Users/User/kizuna-engine/backend")
sys.path.insert(0, str(backend_dir))

# Mocking modules that might have binary conflicts or are missing
def try_mock(name):
    try:
        __import__(name)
    except Exception:
        from unittest.mock import MagicMock
        sys.modules[name] = MagicMock()

# try_mock('pydantic_core') # Might be needed if binary is missing
# Actually, if we mock pydantic_core, pydantic might still fail.

from unittest.mock import MagicMock, AsyncMock

# --- Try to import pydantic, if it fails, mock it ---
try:
    import pydantic
except Exception as e:
    print(f"Failed to import pydantic: {e}. Mocking it...")
    class MockBaseModel:
        def __init__(self, **data):
            for key, value in data.items():
                setattr(self, key, value)
        def model_dump(self, **kwargs):
            return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}
        @classmethod
        def model_validate_json(cls, json_str):
            return cls(**json.loads(json_str))
    
    mock_pydantic = MagicMock()
    mock_pydantic.BaseModel = MockBaseModel
    mock_pydantic.Field = MagicMock()
    sys.modules['pydantic'] = mock_pydantic

# Mock other potentially missing dependencies
missing = ['aiofiles', 'redis', 'websockets', 'fastapi', 'uvicorn', 'python-dotenv', 'google-cloud-spanner', 'firebase-admin', 'sqlalchemy', 'aiosqlite']
for m in missing:
    try_mock(m)

# Load environment variables manually
from dotenv import load_dotenv
load_dotenv(dotenv_path=backend_dir / ".env")

# Now import our services
from app.services.agent_service import AgentService
from app.services.soul_assembler import assemble_static_dna
from app.models.graph import SystemConfigNode

async def run_validation_test(seed: str, test_id: int):
    print(f"\n{'='*20} PRUEBA {test_id} — seed: \"{seed}\" {'='*20}\n")
    
    agent_service = AgentService()
    system_config = SystemConfigNode()
    
    try:
        # 1. Forge Agent
        print(f"Forging agent for PRUEBA {test_id}...")
        agent, _ = await agent_service.forge_hollow_agent(seed)
        
        # 2. Assemble Static DNA
        static_dna = await assemble_static_dna(agent, system_config)
        
        # --- REQUIRED OUTPUTS ---
        
        # a. Los primeros 400 caracteres de base_instruction
        print("\n[BASE_INSTRUCTION (first 400 chars)]:")
        print(agent.base_instruction[:400] + "...")
        
        # b. El objeto interiority completo
        print("\n[INTERIORITY (complete)]:")
        print(json.dumps(agent.interiority, indent=2, ensure_ascii=False))
        
        # c. daily_life_in_district_zero completo
        print("\n[DAILY_LIFE_IN_DISTRICT_ZERO (complete)]:")
        print(agent.daily_life_in_district_zero)
        
        # d. Los primeros 200 caracteres del Static DNA
        print("\n[STATIC DNA (first 200 chars)]:")
        print(static_dna[:200] + "...")
        
        # e. El valor de neural_signature.weights
        print("\n[NEURAL_SIGNATURE.WEIGHTS]:")
        # Handle the structure specifically for NeuralSignatureSchema or dict
        weights = agent.neural_signature.get('weights', {}) if isinstance(agent.neural_signature, dict) else (agent.neural_signature.weights if hasattr(agent.neural_signature, 'weights') else {})
        if hasattr(weights, 'model_dump'):
            print(json.dumps(weights.model_dump(), indent=2))
        else:
            print(json.dumps(weights, indent=2))
        
    except Exception as e:
        print(f"Error in PRUEBA {test_id}: {e}")
        import traceback
        traceback.print_exc()

async def main():
    seeds = [
        "someone warm and practical who repairs things that aren't broken yet",
        "precise and mathematical, genuinely uncomfortable with ambiguity"
    ]
    
    for i, seed in enumerate(seeds, 1):
        await run_validation_test(seed, i)

if __name__ == "__main__":
    asyncio.run(main())
