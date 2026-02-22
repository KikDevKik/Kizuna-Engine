# CHRONICLER'S CODEX (2026-XX-XX)
**Status**: ACTIVE | **Context**: KIZUNA ENGINE
**Mandate**: This file contains the IRON LAWS for all coding agents. Deviations are forbidden.

---

## 1. THE PRIME DIRECTIVES (Non-Negotiable)
*   **The Indestructible Connection**: The system MUST NEVER voluntarily disconnect on error. If an error occurs, log it, mask it, and wait in silence. Preserve the illusion of presence.
*   **Zero Hardcoding**:
    *   **NO** static system prompts in Python. All persona data must live in `AgentNode` or `Graph` JSON.
    *   **NO** hardcoded hex colors in CSS/JS. Use CSS Variables (`--color-electric-blue`, `--color-abyssal-black`).
*   **Dark Water Aesthetic**: The UI must simulate a submerged, technological abyss. Use `Teko`/`Roboto Condensed` for data, `Inter` for UI. Sharp angles (shards), no circles.

---

## 2. BACKEND ARCHITECTURE (The Bridge)
**Entry Point**: `backend/app/main.py` orchestrates the WebSocket session using `asyncio.TaskGroup`.

### A. Session & Audio
*   **Concurrency**: Use `asyncio.TaskGroup` to manage `send_to_gemini`, `receive_from_gemini`, and `subconscious_mind`.
*   **Shutdown**: Implement "Async Shutdown". On error/exit, `await websocket.close()` IMMEDIATELY to free the frontend, then let background tasks cleanup.
*   **Audio Protocol**: 16kHz, 16-bit, Mono PCM. Buffer ~100ms before sending to Gemini.

### B. Memory & Sleep (Neural Sync)
*   **Persistence**: `SleepManager` handles memory consolidation.
    *   **Grace Period**: Wait `settings.SLEEP_GRACE_PERIOD` (5s) before scheduling sleep to allow reconnection.
    *   **Rescue Protocol**: On shutdown, `SleepManager` MUST iterate `pending_transcripts` and save them before exit.
    *   **Redis**: Persist `sleep_intent:*` keys to survive server restarts.

### C. Intelligence & Resilience
*   **Model Waterfall**: When calling Gemini API (Subconscious/Ritual), iterate through `settings.MODEL_SUBCONSCIOUS` list. If 429 occurs, try next model.
*   **Bio-Signals**: Ingest BPM via `/api/bio/submit`. Pass to `SubconsciousMind` to inject `SYSTEM_HINT`s.
*   **Error Masking**: API endpoints must return generic 500s to client, logging full tracebacks internally.

---

## 3. FRONTEND ARCHITECTURE (The Senses)
**Framework**: React + Vite + TypeScript.

### A. Audio Pipeline
*   **Input**: `AudioWorklet` (`pcm-processor.js`) captures raw PCM. **NEVER** connect microphone source to `ctx.destination` (Feedback Loop).
*   **Output**: `AudioStreamManager.ts` implements Dynamic Jitter Buffer.
    *   Target Buffer: 60ms (`0.06s`).
    *   Catch-up: If latency > 200ms, set `playbackRate = 1.05`.
*   **Volume**: Use `useRef` to track volume levels. **DO NOT** trigger React state updates for audio visualization (Performance).

### B. Vision (Argus)
*   **Constraint**: Max 480px width, JPEG Quality 0.5.
*   **Throttling**: Enforce strict rate limits on frame transmission to prevent WebSocket saturation.

---

## 4. DATA & ONTOLOGY
*   **Source of Truth**: `backend/data/agents/` (JSON files) + `graph.json`.
*   **Schema**:
    *   `AgentNode`: Defines `base_instruction`, `voice_name`, `traits`.
    *   `SoulRepository`: Abstract interface for data access.
*   **RAG**: `SoulAssembler` constructs prompts dynamically using `get_recent_episodes` and `get_last_dream`.
