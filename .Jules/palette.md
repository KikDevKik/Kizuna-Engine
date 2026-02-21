## 2025-02-21 - Keyboard Navigation Interference
**Learning:** Adding global keyboard shortcuts (like arrow keys for carousel) can severely impact UX if they interfere with text inputs or textareas. Users expect arrow keys to move the cursor when typing.
**Action:** Always check `e.target` in global keydown handlers and ignore if the target is an input, textarea, or contentEditable element.
