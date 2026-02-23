# CHRONICLER'S CODEX (2026-XX-XX)
**Status**: ACTIVE | **Context**: KIZUNA ENGINE
**Mandate**: This file contains the IRON LAWS for all coding agents. Deviations are forbidden.

---

## 1. THE PRIME DIRECTIVES (Non-Negotiable)
*   **The Indestructible Connection**: The system MUST NEVER voluntarily disconnect on error. If an error occurs, log it, mask it, and wait in silence. Preserve the illusion of presence.
*   **Zero Hardcoding**:
    *   **NO** static system prompts in Python. All persona data must live in `AgentNode` or `Graph` JSON.
    *   **NO** hardcoded configuration logic. Use `SystemConfigNode` via `repository.get_system_config()`.
    *   **NO** hardcoded hex colors in CSS/JS. Use CSS Variables (`--color-electric-blue`, `--color-abyssal-black`).
*   **Dark Water Aesthetic**: The UI must simulate a submerged, technological abyss. Use `Teko`/`Roboto Condensed` for data, `Inter` for UI. Sharp angles (shards), no circles.

---

## 2. BACKEND ARCHITECTURE (The Bridge)
**Entry Point**: `SessionManager` (`backend/app/services/session_manager.py`) orchestrates the lifecycle.

### A. Session & Audio
*   **Concurrency**: Use `asyncio.TaskGroup` to manage `send_to_gemini`, `receive_from_gemini`, and `subconscious_mind`.
*   **Shutdown**: Implement "Async Shutdown". On error/exit, `await websocket.close()` IMMEDIATELY to free the frontend, then let background tasks cleanup.
*   **Audio Protocol**: 16kHz, 16-bit, Mono PCM. Buffer ~100ms before sending.
*   **True Echo Handling**: `[USER: ...]` text from frontend MUST be routed to Subconscious but NOT sent back to Gemini as audio input to prevent double-processing.

### B. Memory & Sleep (Neural Sync)
*   **Vector Parity**: Use `embedding_service` and Cosine Similarity in `LocalSoulRepository` for all RAG operations (`get_relevant_facts`, `get_relevant_episodes`). Do NOT fall back to keyword matching.
*   **Persistence**: `SleepManager` handles memory consolidation.
    *   **Grace Period**: Wait `settings.SLEEP_GRACE_PERIOD` (5s) before scheduling sleep.
    *   **Rescue Protocol**: On shutdown, `SleepManager` MUST save pending transcripts.

### C. Intelligence & Resilience
*   **Strict Formatting**: The backend relies on regex to parse `[USER: ...]` and `[SPOKEN: ...]`. Internal monologue MUST be stripped before sending to client.
*   **Model Waterfall**: When calling Gemini API (Subconscious/Ritual), iterate through `settings.MODEL_SUBCONSCIOUS` list on 429 errors.
*   **Ontological Decoupling**: Global settings (affinity matrix, core directives) reside in `SystemConfigNode` in the graph, not in `settings.py`.

---

## 3. FRONTEND ARCHITECTURE (The Senses)
**Framework**: React + Vite + TypeScript.

### A. Audio Pipeline
*   **True Echo Protocol**: Use native browser `SpeechRecognition` in `useLiveAPI.ts` to capture user text. Do NOT rely on Gemini for speech-to-text.
*   **Input**: `AudioWorklet` (`pcm-processor.js`) captures raw PCM. **NEVER** connect microphone source to `ctx.destination` (Feedback Loop).
*   **Output**: `AudioStreamManager.ts` implements Dynamic Jitter Buffer.
    *   Target Buffer: 60ms (`0.06s`).
    *   Catch-up: If latency > 200ms, set `playbackRate = 1.05`.

### B. Vision (Argus)
*   **Constraint**: Max 480px width, JPEG Quality 0.5.
*   **Throttling**: Enforce strict rate limits on frame transmission to prevent WebSocket saturation.

---

## 4. DATA & ONTOLOGY
*   **Source of Truth**: `backend/data/agents/` (JSON files) + `graph.json`.
*   **Schema**:
    *   `AgentNode`: Defines `base_instruction`, `voice_name`, `traits`.
    *   `SoulRepository`: Abstract interface. `LocalSoulRepository` provides vector search implementation.
    *   `SystemConfigNode`: Stores global system behavior settings.
*   **RAG**: `SoulAssembler` constructs prompts dynamically using `get_recent_episodes` (Verbatim Priority) and `get_last_dream`.
