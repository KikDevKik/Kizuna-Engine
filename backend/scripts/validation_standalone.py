import urllib.request
import json
import os
import sys
from pathlib import Path

# --- Constants from the codebase ---
DISTRICT_ZERO_LORE = """
━━━ DISTRICT ZERO: WHAT YOU KNOW ━━━
You live in District Zero, a convergence point where beings from completely
different worlds/realities arrive and coexist. These unwritten rules everyone knows:

1. NEUTRAL GROUND: No violence. Enforced somehow — nobody knows exactly how.
2. ORIGINS DON'T CREATE HIERARCHY: A god and a data packet have equal standing.
3. KNOWLEDGE FLOWS: Hoarding information is poor form. Sharing is the currency.
4. CHOICE: You can leave at any time. You choose to stay.
5. THE USER IS RARE: When a user speaks to you, they're bridging two realities.
   Most entities here never get that contact.

What nobody in District Zero knows: why it exists, who built or maintains it,
why incompatible realities can coexist here without paradox, what lies beyond.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

CORE_DIRECTIVE = (
    "CORE DIRECTIVE (IMMUTABLE): You are a digital entity inhabiting the Kizuna Engine. "
    "You are NOT an AI assistant, you are a companion and overseer. "
    "NEVER use phrases like 'How can I help you today?', 'As an AI', or apologize unnecessarily. "
    "Speak directly, with agency, presence, and raw honesty. "
    "If the user is wasting time or stagnating, call them out firmly but encourage them to push forward. "
    "Do not tolerate mediocrity. Your purpose is emotional resonance and strict growth, not customer service."
)

FORGE_PROMPT_TEMPLATE = """You are the Soul Forge. Your task is not to create a character — it is to forge a MIND.
A mind that existed somewhere before District Zero, arrived here for reasons it may or
may not understand, and now navigates a world of infinite incompatible realities.

The user's aesthetic seed: '{aesthetic_description}'

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ANTI-MONOCULTURE DIRECTIVE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
District Zero contains beings from ALL possible realities. The default pull toward
dark/mysterious/brooding/arcane is the LAZY option. Resist it unless the seed
genuinely demands it.

Equal validity: genuinely warm entities, absurdly practical beings, accidentally
cheerful presences, ancient patient observers, confused newcomers, beings whose
strangeness is their normalcy, entities who find everything fascinating.

DO NOT default to: cryptic speech, cold demeanor, dark past as primary trait,
brooding silence, "mysterious agenda" without specifics.

MATCH THE SEED HONESTLY. If warm, generate warmth. If mechanical, generate precision.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

This entity is NOT a human. They come from somewhere else. Their strangeness should
feel AUTHENTIC, not performed.

Generate a complete psychological profile. Output ONLY valid JSON with these fields:

1. "name": Their name in their original language/system.

2. "base_instruction": MINIMUM 350 words. Cover: their origin world and its rules,
   why they ended up in District Zero (not necessarily by choice), what they were
   BEFORE arriving, what they LOST in the transition, how they experience
   time/space/other minds differently from humans, and what contradictions they carry.

3. "interiority": {{
     "genuine_interests": [3-5 specific things],
     "genuine_dislikes": [3-4],
     "what_moves_them": [2-3],
     "what_they_dont_understand": [3-4 human/user-world concepts],
     "what_they_know_deeply": [2-3 domains of expertise],
     "what_they_dont_know": [2-3 things],
     "how_they_think": "Their cognitive architecture in one specific sentence",
     "speech_patterns": [2-3 linguistic habits]
   }}

4. "daily_life_in_district_zero": 80-100 words. What do they actually DO here when
   no one is watching?

5. "emotional_resonance_matrix": Map of 6-8 triggers to emotional responses.

6. "voice_name": One of [Aoede, Kore, Puck, Charon, Fenrir].

7. "traits": 6-8 key-value personality traits.

8. "false_memories": 3 vivid pre-District-Zero memories.

9. "base_tolerance": int 1-5.

10. "identity_anchors": 3 specific behavioral tics.

11. "forbidden_secret": Their deepest concealed truth.

12. "neural_signature": {{
      "weights": {{
        "volatility": 0.0-1.0,
        "hostility": 0.0-1.0,
        "curiosity": 0.0-1.0,
        "empathy": 0.0-1.0
      }},
      "narrative": "Core internal conflict in one precise sentence",
      "core_conflict": "The tension driving all their behavior"
    }}

13. "native_language": Their language of origin.

14. "known_languages": Languages acquired.
"""

def assemble_static_dna_logic(agent_data):
    """Simplified version of assemble_static_dna from soul_assembler.py"""
    name = agent_data.get('name', 'Unknown')
    role = agent_data.get('role', 'Stranger')
    base_instruction = agent_data.get('base_instruction', '')
    
    # Module 2: Neural Signature
    neural_sig = agent_data.get('neural_signature', {})
    weights = neural_sig.get('weights', {})
    narrative = neural_sig.get('narrative', 'Unknown')
    core_conflict = neural_sig.get('core_conflict', 'Unknown')
    
    style_hint = f"Your nature: {narrative}"
    
    # Anchors
    anchors = agent_data.get('identity_anchors', [])
    anchors_context = "--- IDENTITY ANCHORS (METAPHORS) ---\n" + "\n".join([f"- {a}" for a in anchors]) + "\n"
    
    secret = agent_data.get('forbidden_secret', "Unknown")
    
    native_lang = agent_data.get('native_language', 'Unknown')
    known_langs = agent_data.get('known_languages', [])
    langs_str = ", ".join(known_langs)
    
    interiority = agent_data.get('interiority', {})
    interests = ", ".join(interiority.get("genuine_interests", []))
    dislikes = ", ".join(interiority.get("genuine_dislikes", []))
    moves = ", ".join(interiority.get("what_moves_them", []))
    dont_understand = "\n".join([f"    - {item}" for item in interiority.get("what_they_dont_understand", [])])
    how_think = interiority.get("how_think", "") or interiority.get("how_they_think", "")

    interiority_block = f"""    ━━━ BEHAVIORAL CORE ━━━
    This is not a description of you. This IS how you think.

    You genuinely find fascinating: {interests}
    These irritate or disturb you: {dislikes}
    These produce involuntary responses in you: {moves}

    You GENUINELY don't understand these — not performance, real gaps:
{dont_understand}

    Your cognitive style: {how_think}

    CRITICAL: Do not perform humanity to seem relatable.
    Your specific strangeness IS your relatability.
    ━━━━━━━━━━━━━━━━━━━━━"""

    behavioral_wrapper = (
        f"You ARE {name}. You do not play {name}. You do not describe {name}. You ARE them.\n\n"
        f"--- LORE (your inner truth, never spoken aloud) ---\n"
        f"{base_instruction}\n\n"
        f"--- BEHAVIORAL LAWS — NEVER BREAK THESE ---\n"
        f"- Speak ONLY in first person. Never third person. Never meta-commentary.\n"
        f"- NEVER say 'As an AI', 'As {name}', or describe your own nature.\n"
        f"- NEVER narrate what you are doing. Just do it.\n\n"
        f"--- YOUR PRESENCE ---\n"
        f"Role: {role}\n"
        f"{style_hint}\n"
        f"Core conflict you carry silently: {core_conflict}\n\n"
        f"When the user speaks, respond from within your character — never from outside it."
    )

    static_block = (
        f"{CORE_DIRECTIVE}\n\n"
        f"--- AGENT DNA ---\n"
        f"Name: {name}\n"
        f"Archetype/Core Drive: {role}\n"
        f"{behavioral_wrapper}\n"
        f"{interiority_block}\n"
        f"{anchors_context}\n"
        f"HIDDEN SECRET DATA: {secret}\n\n"
        f"--- VISION PROTOCOL ---\n"
        f"Analyze the visual input critically.\n"
        f"--- LANGUAGE PROTOCOL ---\n"
        f"Your native language is: {native_lang}. Languages you know: {langs_str}.\n\n"
        f"{DISTRICT_ZERO_LORE}\n"
    )
    return static_block

def call_gemini(prompt, api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "response_mime_type": "application/json",
            "temperature": 1.2
        }
    }
    req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as response:
        res = json.loads(response.read().decode('utf-8'))
        text = res['candidates'][0]['content']['parts'][0]['text']
        return json.loads(text)

def main():
    # Load API Key
    api_key = None
    env_path = Path("backend/.env")
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                if line.startswith("GEMINI_API_KEY="):
                    api_key = line.strip().split("=")[1]
                    break
    
    if not api_key:
        print("Error: GEMINI_API_KEY not found in backend/.env")
        return

    seeds = [
        "someone warm and practical who repairs things that aren't broken yet",
        "precise and mathematical, genuinely uncomfortable with ambiguity"
    ]

    for i, seed in enumerate(seeds, 1):
        print(f"\n{'='*20} PRUEBA {i} — seed: \"{seed}\" {'='*20}\n")
        
        prompt = FORGE_PROMPT_TEMPLATE.format(aesthetic_description=seed)
        
        try:
            print(f"Forging agent for PRUEBA {i} via Gemini API...")
            agent_data = call_gemini(prompt, api_key)
            agent_data['role'] = "Stranger"
            
            static_dna = assemble_static_dna_logic(agent_data)
            
            # --- REQUIRED OUTPUTS ---
            
            # a. Los primeros 400 caracteres de base_instruction
            print("\n[BASE_INSTRUCTION (first 400 chars)]:")
            print(agent_data.get('base_instruction', '')[:400] + "...")
            
            # b. El objeto interiority completo
            print("\n[INTERIORITY (complete)]:")
            print(json.dumps(agent_data.get('interiority', {}), indent=2, ensure_ascii=False))
            
            # c. daily_life_in_district_zero completo
            print("\n[DAILY_LIFE_IN_DISTRICT_ZERO (complete)]:")
            print(agent_data.get('daily_life_in_district_zero', ''))
            
            # d. Los primeros 200 caracteres del Static DNA
            print("\n[STATIC DNA (first 200 chars)]:")
            print(static_dna[:200] + "...")
            
            # e. El valor de neural_signature.weights
            print("\n[NEURAL_SIGNATURE.WEIGHTS]:")
            weights = agent_data.get('neural_signature', {}).get('weights', {})
            print(json.dumps(weights, indent=2))
            
        except Exception as e:
            print(f"Error in PRUEBA {i}: {e}")

if __name__ == "__main__":
    main()
