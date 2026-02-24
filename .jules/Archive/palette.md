# Palette's Journal

## 2026-02-22 - The Invisible Interface
**Learning:** Users often miss keyboard shortcuts in "immersive" interfaces because standard cues (like button tooltips) are hidden to preserve the aesthetic.
**Action:** Always add subtle, thematic visual hints (like low-opacity technical text) for critical keyboard interactions, ensuring they blend with the UI while remaining discoverable.

## 2026-02-23 - Toggle Semantics
**Learning:** Using standard buttons for "On/Off" states in settings panels forces screen reader users to guess the current state.
**Action:** Always use `role="switch"` with `aria-checked` for toggle controls, even if they look like buttons visually, to provide immediate state feedback.
