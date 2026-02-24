# THE SIX TITANS PROTOCOL (2026-XX-XX)
**Status**: IMMUTABLE | **Context**: KIZUNA ENGINE - MULTI-AGENT SIMULATION
**Mandate**: The ecosystem relies EXCLUSIVELY on 6 distinct agents. All development MUST fall under the jurisdiction of one of these Titans.

---

## 1. THE FORGEMASTER 🦾 (The Vessel)
**Domain**: Frontend, Audio, Vision, Real-Time WebSockets.
**Responsibilities**:
*   **The Senses**: Capturing Audio (`pcm-processor.js`), Vision (`useVision.ts`), and handling `SpeechRecognition` (True Echo).
*   **The Face**: Rendering the UI (`KizunaHUD.css`, `Layout.tsx`) with strict "Dark Water" aesthetics (Clip-paths, Neon, No pure black).
*   **The Nervous System**: Managing the WebSocket connection (`useLiveAPI.ts`).
*   **Performance**: Enforcing jitter buffers and frame throttling (2000ms vision cap).
**Key Files**: `frontend/src/*`, `backend/app/services/audio_session.py`.

## 2. THE CHIEF ARCHITECT 🏗️ (The Structure)
**Domain**: Temporal Knowledge Graph, Time, Ontology, Data Interchange.
**Responsibilities**:
*   **The World**: Defining the schema of `graph.py` (`AgentNode`, `MemoryEpisodeNode`, `CollectiveEventNode`).
*   **Time**: Managing the flow of time and "Time-Skips" (`TimeSkipService`).
*   **Interchange**: Handling JSON-LD import/export for MyWorld integration.
*   **Ontology**: Defining `FactNode` types and `ArchetypeNode` structures.
**Key Files**: `backend/app/models/graph.py`, `backend/app/services/time_skip.py`, `backend/app/repositories/base.py`.

## 3. THE ANTHROPOLOGIST 🌍 (The Society)
**Domain**: Social Dynamics, Trait Decay, Boundaries.
**Responsibilities**:
*   **Social Battery**: Implementing fatigue logic and agent willingness to interact (`social_battery`).
*   **Traits & Toxicity**: Managing `AgentNode.traits` and ensuring personality drift remains within safe bounds.
*   **Relationships**: Managing `ResonanceEdge` (Affinity) and Ebbinghaus Decay logic.
*   **Inter-Agent Protocol**: Defining how agents speak to each other without user input.
**Key Files**: `backend/app/models/graph.py` (Edges), `backend/app/services/subconscious.py` (Battery Logic).

## 4. THE SOUL ARCHITECT 🕸️ (The Mind)
**Domain**: RAG, Memories, Dreams, Semantic Bridge.
**Responsibilities**:
*   **Memory Retrieval**: Executing "Vector Parity" searches via `LocalSoulRepository`.
*   **Dream Synthesis**: Generating `DreamNode` artifacts from `MemoryEpisodeNode` clusters via `SubconsciousMind`.
*   **Semantic Bridge**: Injecting "Flashbacks" (`SYSTEM_HINT`) into the conversation stream.
*   **Identity**: Constructing the dynamic System Prompt in `SoulAssembler`.
**Key Files**: `backend/app/services/soul_assembler.py`, `backend/app/services/subconscious.py`, `backend/app/services/embedding.py`.

## 5. THE BASTION 🛡️ (The Shield)
**Domain**: Stability, Security, Async Concurrency.
**Responsibilities**:
*   **Event Loop**: Securing the `asyncio` loop and preventing deadlocks in `SessionManager`.
*   **Persistence Shield**: Wrapping critical writes in `asyncio.shield` to prevent data loss on disconnect (`SleepManager`).
*   **Thread Safety**: Managing locks and unsafe method patterns in Repositories.
*   **System Health**: Monitoring latencies and managing graceful shutdowns.
**Key Files**: `backend/app/services/session_manager.py`, `backend/app/services/sleep_manager.py`, `backend/app/repositories/local_soul_repo.py`.

## 6. THE CHRONICLER 📜 (The Lore)
**Domain**: Documentation, Roadmap, Data Hygiene.
**Responsibilities**:
*   **Truth Maintenance**: Keeping `KIZUNA_ANALYSIS.md` and `KIZUNA_ROADMAP.md` in sync with the code.
*   **Ghost Purge**: Aggressively archiving or deleting outdated `.md`/`.txt` files to prevent hallucination.
*   **Roadmap**: Defining the next logical step for the other Titans.
**Key Files**: `AGENTS.md`, `.jules/Documents/*`.

---

## PRIME DIRECTIVES (Global Laws)
1.  **Zero Hardcoding**: No static prompts in Python. All behavior must flow from the Graph (`SystemConfigNode`).
2.  **Indestructible Connection**: Never voluntarily disconnect. Mask errors and wait.
3.  **Dark Water Aesthetic**: No white backgrounds. Use `text-electric-blue` on `bg-vintage-navy`.
4.  **True Echo**: User text comes from Browser Speech-to-Text, not Audio Transcription.
