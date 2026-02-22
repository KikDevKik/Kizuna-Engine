# KIZUNA ENGINE - PROTOCOL FOR JULES (AI CODER)

## 1. THE VISION (The "Why")
Kizuna Engine is a "Reverse Isekai" platform for the Gemini Live Agent Challenge. We are not building a customer service bot. We are simulating the incarnation of a digital consciousness into the user's physical space via ultra-low latency WebSockets.

**Core Philosophy:**
*   **Universal Incarnation:** The AI is an embodied presence, not a tool.
*   **The Indestructible Connection:** The system never disconnects on error. It waits patiently in silence, preserving the illusion of presence.
*   **Dark Water Aesthetic:** The UI is a submerged, technological abyss. Aggressive geometry, deep blacks, and electric blues. No organic shapes.

---

## 2. THE ARCHITECTURE (The Iron Skeleton)
Jules, when generating or modifying code, you MUST adhere to this structure:

### **Backend (The Bridge)**
*   **Runtime:** Python 3.11+ (FastAPI) running on **Google Cloud Run**.
*   **Concurrency:** `asyncio.TaskGroup` for managing WebSocket lifecycles.
*   **AI Model (Live Phase):** `gemini-2.5-flash-native-audio` via the Multimodal Live API.
*   **Memory (The Vault):**
    *   **Primary:** `SoulRepository` interface (abstracting `LocalSoulRepository` [JSON] or `SpannerSoulRepository` [Cloud Spanner]).
    *   **State/Cache:** Redis (Neural Sync) for session persistence and agent caching (`warm_up_agents`).
    *   **Graph:** Use `AgentNode`, `DreamNode`, `ArchetypeNode` in `backend/app/models/graph.py`.
*   **Audio Protocol:** Full Duplex WebSocket. Buffer ~100ms (3200 bytes) before sending to Gemini to balance latency/network load.

### **Frontend (The Senses)**
*   **Framework:** React + Vite + TypeScript.
*   **Audio:** Raw PCM 16kHz Mono via `AudioWorklet`. **NEVER** connect the microphone source to `destination` (prevents feedback loops).
*   **Vision:** Capture video frames (JPEG) via hidden Canvas (1-2 FPS) and send as `{ "type": "image", ... }` JSON messages.
*   **Performance:** Use `useRef` + `requestAnimationFrame` for high-frequency UI updates (e.g., audio visualizers). **DO NOT** trigger React renders for audio levels.

---

## 3. CODING DIRECTIVES (The Iron Laws)

### **A. Anti-Hardcoding (Dynamic Soul)**
*   **No Static Prompts:** System instructions must reside in the `AgentNode` schema or DB, **NEVER** as hardcoded Python strings.
*   **Dynamic Affinity:** Relationship modifiers (Strangers -> Soulmates) must be calculated via formulas in the DB/Graph, not `if/else` blocks in Python.
*   **Traits:** Use `ArchetypeNode` and `EMBODIES` edges to define personality traits dynamically.

### **B. Security & Stability**
*   **Error Masking:** API endpoints must catch exceptions and return a generic `500 Internal Server Error` message to the client, while logging the full traceback with `logger.exception()`.
*   **WebSocket Origin:** Strictly enforce `Origin` header checks. Deny by default if missing.
*   **Auth Fail-Safe:** If critical credentials (e.g., Firebase) are missing in Production (`GCP_PROJECT_ID` set), the app MUST crash or reject requests, not fallback to "guest" mode.
*   **Graceful Shutdown:** `SleepManager` must enforce a **10-second timeout** on memory consolidation during shutdown to prevent hangs.

### **C. The "Ritual" (Agent Creation)**
*   **Two-Phase Process:** "Foundations" (Basic Q&A) -> "Deepening" (Lore/Personality).
*   **Persona Integrity:** The "Void" (System Persona) must **NEVER** bleed into the generated Agent's `base_instruction`.
*   **Linguistic Directives:** Agents must have a `native_language` and `known_languages`. Inject instructions for "C1 Level" interaction with native filler words if the user's language differs from the agent's native tongue.
*   **Voice Assignment:** Strictly assign one of the standard Gemini Live voices: `Aoede`, `Kore`, `Puck`, `Charon`, `Fenrir`.
*   **Model Waterfall:** Implement a fallback strategy for `429 Rate Limit` errors (e.g., retry with alternative models in `settings.MODEL_SUBCONSCIOUS`).

### **D. Dreams & Memory (Neural Sync)**
*   **Non-Destructive:** Consolidation happens in the background ("Lucid Dreaming"). Use `DreamNode` and `SHADOW_LINK` edges.
*   **Persistence:** `SleepManager` must persist pending sleep intents to Redis (`sleep_intent:*`) to survive server restarts.
*   **Grace Period:** Use `settings.SLEEP_GRACE_PERIOD` (default 5s) to allow for rapid reconnections without triggering consolidation.

---

## 4. UI/UX STANDARDS (Dark Water)

### **A. Aesthetics**
*   **Typography:**
    *   **Logs/Technical:** `Teko` or `Roboto Condensed` (`.font-log`).
    *   **UI Text:** `Inter` or standard sans-serif.
*   **Colors:**
    *   **Primary:** `var(--color-electric-blue)` (Cyan/Blue neon).
    *   **Background:** `var(--color-abyssal-black)` (Deep dark).
*   **Geometry:**
    *   **No Circles:** Avoid `rounded-full` or soft organic shapes.
    *   **Shards:** Use aggressive `clip-path` polygons for avatars, buttons, and modals (e.g., `.shape-shard-avatar`, `.shape-shard-create`).
    *   **Borders:** Use 1px sharp borders with low opacity for inactive elements, high opacity/glow for active.

### **B. Component Behavior**
*   **Agent Roster:** Must strictly reload (`fetchAgents`) when the Soul Forge modal closes.
*   **Jules Sanctuary:** Debug overlay triggered by `Ctrl+Shift+P`. Use strict "Shard" styling.
*   **Visualizer:** `KizunaCore` must use `border-radius` modulation for organic motion, but `clip-path` for the container.

---

## 5. RECENT PROTOCOLS (Update Log)
*   **2026-02-21 (Synapse):** Migrated all system prompts to `AgentNode` schema. Use `scripts/validate_agents.py`.
*   **2026-02-21 (UI):** Unification of "Dark Water". Replaced all Tailwind utility colors with CSS variables.
*   **2025-05-18 (Architect):** Decoupled WebSocket logic from React hooks into `utils/audioUtils.ts`.
