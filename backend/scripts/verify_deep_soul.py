import sys
from pathlib import Path
import asyncio

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).parent.parent
sys.path.append(str(backend_dir))

from app.models.graph import SystemConfigNode, AgentNode
from app.services.soul_assembler import assemble_static_dna

async def verify():
    print("1. Creating manual agent node directly instead of mocking forge_hollow_agent since the prompt testing requires the actual API.")
    # In order to test the changes to static DNA and the agent node class

    # We create a dummy agent using the new fields to ensure they work correctly.
    agent = AgentNode(
        name="Tinker",
        role="Stranger",
        base_instruction="A wanderer who repairs old gadgets in the scrap wastes of District Zero. They arrived after their homeworld's Great Disassembly.",
        voice_name="Kore",
        traits={"warm": "genuine", "curious": "obsessive"},
        interiority={
            "genuine_interests": ["clockwork mechanisms", "the sound of rain on metal"],
            "genuine_dislikes": ["wastefulness", "loud, sudden noises"],
            "what_moves_them": ["seeing something broken working again"],
            "what_they_dont_understand": ["why people throw things away", "sarcasm", "the concept of ownership"],
            "what_they_know_deeply": ["metallurgy", "thermodynamics"],
            "what_they_dont_know": ["human anatomy", "the purpose of art that isn't functional"],
            "how_they_think": "I analyze everything as a system of interconnected parts that can be optimized or repaired.",
            "speech_patterns": ["uses mechanical metaphors", "pauses to listen to ambient sounds"]
        },
        daily_life_in_district_zero="Wanders the perimeter of the Scrap Wastes, picking up discarded tech. Fixes it in a small hovel and leaves it for others to find.",
        emotional_resonance_matrix={"broken_thing": "compassion", "fixed_thing": "joy", "needless_destruction": "anger"},
        native_language="Scrap Cant",
        known_languages=["English", "Spanish"],
        base_tolerance=4,
        identity_anchors=["always has grease on their hands", "carries a wrench", "hums a low note when thinking"],
        forbidden_secret="They accidentally caused the Great Disassembly.",
        neural_signature={
            "weights": {"volatility": 0.2, "hostility": 0.1, "curiosity": 0.8, "empathy": 0.7},
            "narrative": "A fixer burdened by the guilt of breaking their world.",
            "core_conflict": "To repair everything to avoid thinking about what cannot be fixed."
        }
    )

    print("\n2. Verifying saved JSON fields...")
    print(f"- interiority: {hasattr(agent, 'interiority') and agent.interiority is not None}")
    print(f"- daily_life_in_district_zero: {hasattr(agent, 'daily_life_in_district_zero') and agent.daily_life_in_district_zero is not None}")
    print(f"- emotional_resonance_matrix: {hasattr(agent, 'emotional_resonance_matrix') and agent.emotional_resonance_matrix is not None}")

    print("\n3. Verifying Static DNA generation...")
    system_config = SystemConfigNode()
    static_dna = await assemble_static_dna(agent, system_config)

    has_behavioral_core = "━━━ BEHAVIORAL CORE ━━━" in static_dna
    has_lore = "━━━ DISTRICT ZERO: WHAT YOU KNOW ━━━" in static_dna

    print(f"- Contains BEHAVIORAL CORE: {has_behavioral_core}")
    print(f"- Contains DISTRICT ZERO LORE: {has_lore}")

    print("\n4. Displaying the first 500 characters of the Static DNA generated:")
    print("--------------------------------------------------")
    print(static_dna[:500])
    print("--------------------------------------------------")
    print("And the rest of the DNA just to verify the new sections:")
    print("--------------------------------------------------")
    print(static_dna)
    print("--------------------------------------------------")

if __name__ == "__main__":
    asyncio.run(verify())
