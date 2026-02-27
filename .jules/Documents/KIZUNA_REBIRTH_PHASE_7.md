# KIZUNA ENGINE: ARCHITECTURE REBIRTH (PHASE 7)

**Directive:** The Glass Bridge (Neural Sync & Cognitive Architecture)
**Author:** The Bastion (War Room Council)
**Objective:** Eradicate context bloat, decouple task concurrency, and implement a modular "Neural Signature" for instant WebSocket connections.

---

## MODULE 1: THE GREAT REBIRTH (Database Wipe)
**Target:** `backend/app/repositories/local_graph.py` & `backend/app/routers/system.py`
The Director has ordered a clean slate to implement the new DNA structures.
1. **Total Incineration:** Refactor `purge_all_memories` into a true `purge_all_existence`. It must now `delete(NodeModel)` completely, removing all `AgentNode` and `UserNode` entities alongside edges and memories.
2. **Endpoint Update:** Ensure the frontend trigger safely calls this new total wipe without leaving orphaned vector embeddings.

---

## MODULE 2: NEURAL SIGNATURE (The Cognitive DNA)
**Target:** `backend/app/models/graph.py` & `backend/app/services/ritual_service.py`
Agents will no longer just have "traits". They will have a weighted brain map.
1. **Schema Update:** Add a new field to `AgentNode`: `neural_signature: Dict[str, Any]`.
   - It must contain two sub-fields: `"weights": {}` (Float values for cognitive priorities) and `"narrative": ""` (The textual "Conflict" or life logic of the agent).
2. **The Forge Hook:** Update `ritual_service.py` and `agent_service.py` so that when Gemini creates an agent, it generates both the mathematical weights and the narrative conflict based on the user's input.

---

## MODULE 3: MODULAR CACHING (The Speed Engine)
**Target:** `backend/app/services/soul_assembler.py` & `backend/app/services/cache.py`
We are abandoning the monolithic prompt assembly to solve the "20-second latency".
1. **Slot Abstraction:** Refactor `assemble_soul` into two distinct functions:
   - `assemble_static_dna()`: Returns the immutable backstory, secrets, and Neural Signature. (CACHED).
   - `assemble_volatile_state()`: Returns the current social battery, friction, and recent context. (REAL-TIME).
2. **Neural Sync Cache:** Implement a simple `InMemoryCache` interface (Dict-based for now, Redis-ready for the future). The static DNA is stored here upon application boot or first contact.
3. **The Assembly:** The WebSocket session merely concatenates `[Cache.Get(DNA)] + [get_volatile_state()]`. This will reduce the pre-connection database queries by 80%.

---

## MODULE 4: THE COGNITIVE SUPERVISOR (Resilience)
**Target:** `backend/app/services/session_manager.py`
The `TaskGroup` fragility must be destroyed to prevent the "Socket Hang Up" error.
1. **Organ Decoupling:** Remove `subconscious_mind.start`, `reflection_mind.start`, and `send_injections_to_gemini` from the primary `asyncio.TaskGroup` that handles audio.
2. **Supervisor Pattern:** Launch these cognitive tasks as standalone background tasks (`asyncio.create_task`) with their own `try/except` recovery loops. If the Subconscious crashes due to a Gemini Rate Limit, the Audio WebSocket MUST remain open and functional.

---

## MODULE 5: INJECTION PURITY
**Target:** `backend/app/services/audio_session.py`
1. **Format Fix:** Ensure all memory/gossip injections are sent strictly as flat strings (e.g., `[SYSTEM_CONTEXT]: ...`) and never as dictionaries, to avoid the Google GenAI SDK `Unsupported input type` crash.
2. **Contextual Throttling:** Ensure the Subconscious has a cooldown (already partially patched, but must be hardened) so it doesn't flood the injection queue with the same memory every 3 seconds.

---
**EXECUTION PROTOCOL:**
Jules is instructed to execute these modules sequentially, validating stability after each step. Do NOT proceed to Module 3 until the wipe (Module 1) and the schema update (Module 2) are fully functional.
