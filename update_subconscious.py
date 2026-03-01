import re

with open("backend/app/services/subconscious.py", "r") as f:
    content = f.read()

# 1. Add TEMPORAL_REFERENCE_TRIGGERS and _has_temporal_reference
new_code = """
logger = logging.getLogger(__name__)

# Palabras y frases que indican que el usuario está referenciando el pasado
TEMPORAL_REFERENCE_TRIGGERS = [
    # Español
    "la vez pasada", "la otra vez", "antes", "recuerdas", "te acuerdas",
    "me dijiste", "dijiste que", "hablamos de", "como cuando", "igual que",
    "anteriormente", "en otra ocasión", "la última vez", "ya hablamos",
    "mencionaste", "me comentaste", "lo que dijiste",
    # English
    "last time", "before", "remember when", "you said", "we talked",
    "you mentioned", "like before", "previously", "earlier", "as before",
    "you told me", "we discussed",
]

def _has_temporal_reference(text: str) -> bool:
    \"\"\"
    Detecta si el usuario está haciendo referencia explícita a una interacción pasada.
    Solo en este caso tiene sentido hacer RAG lookup para inyectar un Flashback.
    \"\"\"
    text_lower = text.lower()
    return any(trigger in text_lower for trigger in TEMPORAL_REFERENCE_TRIGGERS)
"""

content = content.replace("logger = logging.getLogger(__name__)\n", new_code)

# 2. Add guard for memory and event retrieval
search_pattern = """
                    if self.repository:
                        memory_task = asyncio.create_task(
                            self.repository.get_relevant_episodes(user_id, query=full_text, limit=1)
                        )
                        if hasattr(self.repository, 'get_relevant_collective_events'):
                            event_task = asyncio.create_task(
                                self.repository.get_relevant_collective_events(query=full_text, limit=1)
                            )
"""

replace_pattern = """
                    if self.repository and _has_temporal_reference(full_text):
                        memory_task = asyncio.create_task(
                            self.repository.get_relevant_episodes(user_id, query=full_text, limit=1)
                        )
                        if hasattr(self.repository, 'get_relevant_collective_events'):
                            event_task = asyncio.create_task(
                                self.repository.get_relevant_collective_events(query=full_text, limit=1)
                            )
"""

content = content.replace(search_pattern, replace_pattern)

with open("backend/app/services/subconscious.py", "w") as f:
    f.write(content)
