import re

with open("backend/app/services/soul_assembler.py", "r") as f:
    content = f.read()

# 1. Add SOUL_STATIC_VERSION
content = content.replace("logger = logging.getLogger(__name__)\n", "logger = logging.getLogger(__name__)\n\nSOUL_STATIC_VERSION = \"v2\"\n")

# 2. Add language block logic
search_pattern = """
    # Module 2: Neural Signature
    neural_sig_context = ""
"""

replace_pattern = """
    # Module 2: Neural Signature
    neural_sig_context = ""
"""

# Let's add it right before static_block assembly
search_pattern = """
    forbidden_secret = getattr(agent, 'forbidden_secret', "This agent has no secrets yet.")
    secret_block = f"HIDDEN SECRET DATA: {forbidden_secret}"

    static_block = (
        f"{system_config.core_directive}\\n\\n"
"""

replace_pattern = """
    forbidden_secret = getattr(agent, 'forbidden_secret', "This agent has no secrets yet.")
    secret_block = f"HIDDEN SECRET DATA: {forbidden_secret}"

    # Language Awareness Block
    native_lang = getattr(agent, 'native_language', 'Unknown')
    known_langs = getattr(agent, 'known_languages', [])

    if known_langs:
        langs_str = ", ".join(known_langs)
        language_block = (
            f"--- LANGUAGE PROTOCOL ---\\n"
            f"Your native language is: {native_lang}.\\n"
            f"Languages you know: {langs_str}.\\n"
            f"CRITICAL: You MUST communicate ONLY in the languages listed above. "
            f"If the user speaks a language you don't know, respond in your native language "
            f"or in the closest language you do know. "
            f"NEVER pretend to speak a language not in your known list. "
            f"This is part of your identity — not a limitation, but who you are."
        )
    else:
        language_block = (
            f"--- LANGUAGE PROTOCOL ---\\n"
            f"Your native language is: {native_lang}. Communicate in this language by default."
        )

    static_block = (
        f"{system_config.core_directive}\\n\\n"
"""

content = content.replace(search_pattern, replace_pattern)

search_pattern = """
        f"{secret_block}\\n\\n"
        f"--- VISION PROTOCOL ---\\n"
        f"{getattr(agent, 'vision_instruction_prompt', 'Analyze the visual input critically.')}\\n"
    )
    return static_block
"""

replace_pattern = """
        f"{secret_block}\\n\\n"
        f"--- VISION PROTOCOL ---\\n"
        f"{getattr(agent, 'vision_instruction_prompt', 'Analyze the visual input critically.')}\\n"
        f"{language_block}\\n"
    )
    return static_block
"""

content = content.replace(search_pattern, replace_pattern)

# 3. Update cache key
content = content.replace('cache_key = f"soul_static:{agent_id}"', 'cache_key = f"soul_static:{SOUL_STATIC_VERSION}:{agent_id}"')

with open("backend/app/services/soul_assembler.py", "w") as f:
    f.write(content)
