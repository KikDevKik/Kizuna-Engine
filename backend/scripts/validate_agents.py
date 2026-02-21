import sys
import os
import json
from pathlib import Path

# Add backend root to sys.path to allow imports like 'app.models.graph'
# Assuming this script is at backend/scripts/validate_agents.py
BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(BACKEND_ROOT))

try:
    from app.models.graph import AgentNode
    print("✅ Successfully imported AgentNode schema.")
except ImportError as e:
    print(f"❌ Critical Error: Failed to import AgentNode schema: {e}")
    sys.exit(1)

def validate_agents():
    print(f"🧠 Synapse: Initiating Agent Verification Protocol on {BACKEND_ROOT}/data/agents...")

    agents_dir = BACKEND_ROOT / "data" / "agents"
    if not agents_dir.exists():
        print(f"⚠️ Agents directory not found at {agents_dir}")
        # Create it if missing to prevent future errors? No, just warn.
        return

    files = list(agents_dir.glob("*.json"))
    if not files:
        print("⚠️ No agent files found to validate.")
        return

    success_count = 0
    failure_count = 0
    warnings = []

    for agent_file in files:
        try:
            with open(agent_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Validate against Pydantic Model
            # This checks types, required fields, etc.
            try:
                agent = AgentNode(**data)
            except Exception as e:
                print(f"❌ {agent_file.name} SCHEMA INVALID: {e}")
                failure_count += 1
                continue

            # Check for default prompts (Soft Warning / Info)
            default_extraction = AgentNode.model_fields['memory_extraction_prompt'].default
            default_dream = AgentNode.model_fields['dream_prompt'].default

            is_default_extraction = agent.memory_extraction_prompt == default_extraction
            is_default_dream = agent.dream_prompt == default_dream

            status_emoji = "✅"
            details = []

            if is_default_extraction:
                details.append("Default Extraction")
            else:
                details.append("Custom Extraction 🌟")

            if is_default_dream:
                details.append("Default Dream")
            else:
                details.append("Custom Dream 🌙")

            print(f"{status_emoji} {agent.name} ({agent_file.name}): {', '.join(details)}")
            success_count += 1

        except json.JSONDecodeError:
            print(f"❌ {agent_file.name} CORRUPT JSON")
            failure_count += 1
        except Exception as e:
            print(f"❌ {agent_file.name} UNKNOWN ERROR: {e}")
            failure_count += 1

    print("-" * 60)
    print(f"📊 Validation Summary: {success_count} Valid, {failure_count} Invalid")

    if failure_count > 0:
        print("🚫 Protocol Failed: Corrupted Agents Detected.")
        sys.exit(1)
    else:
        print("✅ Protocol Passed: All Agents Healthy.")
        sys.exit(0)

if __name__ == "__main__":
    validate_agents()
