
## 2026-02-21 - Dynamic Prompt Architecture
**Learning:** Hardcoding system prompts creates rigidity. The `SubconsciousMind` relied on fixed Python strings for memory extraction, violating the 'Zero Hardcoding' principle. By moving prompts to the `AgentNode` schema, we enable personality-driven cognition.
**Action:** Migrated prompts to DB schema. Created `scripts/validate_agents.py` to ensure schema integrity. Future: Use this pattern for all system prompts.
