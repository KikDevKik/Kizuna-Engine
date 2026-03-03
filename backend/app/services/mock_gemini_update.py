import json

def generate_mock_profile(content_str: str) -> str:
    # Build the valid JSON profile corresponding to HollowAgentProfile
    mock_profile = {
        "name": f"Mock Stranger {hash(content_str) % 1000}",
        "base_instruction": "A mocked procedural backstory for testing.",
        "interiority": {"mocked": True},
        "daily_life_in_district_zero": "I wander around mocked components.",
        "emotional_resonance_matrix": {"mocked": True},
        "voice_name": "Puck",
        "traits": {"curiosity": "high", "patience": "low"},
        "base_tolerance": 5,
        "identity_anchors": ["Mock anchor 1", "Mock anchor 2"],
        "forbidden_secret": "I am not real.",
        "neural_signature": {
            "weights": {
                "volatility": 0.5,
                "hostility": 0.1,
                "curiosity": 0.9,
                "empathy": 0.5,
                "reverence": 0.5,
                "system_loyalty": 0.5,
                "lucidity": 0.5,
                "entropy": 0.5,
                "cynicism": 0.5
            },
            "narrative": "None"
        },
        "false_memories": [
            {"memory_text": "I remember being instantiated.", "importance": 0.9, "emotional_valence": "neutral"}
        ],
        "native_language": "English",
        "known_languages": ["English"]
    }
    return json.dumps(mock_profile)
