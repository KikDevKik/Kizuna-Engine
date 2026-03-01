import re

with open("backend/tests/test_subconscious.py", "r") as f:
    content = f.read()

# Fix test_analyze_sentiment_custom_agent_prompt
search_pattern = """
        with patch("app.services.subconscious.settings") as mock_settings:
            mock_settings.MOCK_GEMINI = False
            mock_settings.MODEL_SUBCONSCIOUS = "gemini-test"

            await service._analyze_sentiment("hello", agent_id="agent-123")

            # Verify the prompt sent contained the custom prompt text
            call_args = service.client.aio.models.generate_content.call_args
            assert call_args is not None
"""
replace_pattern = """
        with patch("app.services.subconscious.settings") as mock_settings:
            mock_settings.MOCK_GEMINI = False
            mock_settings.MODEL_SUBCONSCIOUS = "gemini-test"

            await service._analyze_sentiment("hello", agent_id="agent-123")

            # Verify the prompt sent contained the custom prompt text
            call_args = service.client.aio.models.generate_content.call_args
            assert call_args is not None
            # Extract config parameter correctly
            kwargs = call_args.kwargs
            assert "config" in kwargs
            assert kwargs["config"]["system_instruction"] == "CUSTOM_PROMPT: [TRANSCRIPT]"
"""
content = content.replace(search_pattern, replace_pattern)


# Fix test_subconscious_start_resilience
search_pattern = """
        try:
            # Wait for the injection queue to get the "Happy Hint"
            hint_payload = await asyncio.wait_for(injection_queue.get(), timeout=2.0)
            assert hint_payload["text"] == "SYSTEM_HINT: Happy Hint"
"""
replace_pattern = """
        try:
            # Wait for the injection queue to get the "Happy Hint"
            hint_payload = await asyncio.wait_for(injection_queue.get(), timeout=2.0)
            assert hint_payload["text"] == "Happy Hint"
"""
content = content.replace(search_pattern, replace_pattern)

with open("backend/tests/test_subconscious.py", "w") as f:
    f.write(content)


with open("backend/tests/test_subconscious_rag.py", "r") as f:
    content = f.read()

# Fix test_subconscious_event_rag_injection
search_pattern = """
    # Start loop
    task = asyncio.create_task(service.start(transcript_queue, injection_queue, "user", "agent"))

    # Feed input
    await transcript_queue.put("Tell me about the war.")
"""
replace_pattern = """
    # Start loop
    task = asyncio.create_task(service.start(transcript_queue, injection_queue, "user", "agent"))

    # Feed input with a temporal reference to trigger RAG
    await transcript_queue.put("Tell me about the war remember when")
"""
content = content.replace(search_pattern, replace_pattern)

search_pattern = """
    try:
        # Expect injection
        payload = await asyncio.wait_for(injection_queue.get(), timeout=5.0)
        text = payload["text"]
        assert "SYSTEM_HINT: 🌍 [World History]" in text
"""
replace_pattern = """
    try:
        # Expect injection
        payload = await asyncio.wait_for(injection_queue.get(), timeout=5.0)
        text = payload["text"]
        assert "🌍 [World History]" in text
"""
content = content.replace(search_pattern, replace_pattern)

with open("backend/tests/test_subconscious_rag.py", "w") as f:
    f.write(content)
