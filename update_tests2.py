import re

with open("backend/tests/test_subconscious.py", "r") as f:
    content = f.read()

# Fix test_analyze_sentiment_custom_agent_prompt - it's failing because "hello" is < 3 words, so the Wallet Guard blocks it.
search_pattern = """
            await service._analyze_sentiment("hello", agent_id="agent-123")
"""
replace_pattern = """
            await service._analyze_sentiment("hello this is a longer test sentence", agent_id="agent-123")
"""
content = content.replace(search_pattern, replace_pattern)

with open("backend/tests/test_subconscious.py", "w") as f:
    f.write(content)

with open("backend/tests/test_subconscious_rag.py", "r") as f:
    content = f.read()

# Fix test_subconscious_event_rag_injection - Buffer accumulation logic waits for < 5 words AND no punctuation.
# Let's add a punctuation to trigger it immediately.
search_pattern = """
    # Feed input with a temporal reference to trigger RAG
    await transcript_queue.put("Tell me about the war remember when")
"""
replace_pattern = """
    # Feed input with a temporal reference to trigger RAG
    await transcript_queue.put("Tell me about the war remember when.")
"""
content = content.replace(search_pattern, replace_pattern)

with open("backend/tests/test_subconscious_rag.py", "w") as f:
    f.write(content)
