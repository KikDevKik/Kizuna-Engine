## 2025-05-18 - Custom Button Accessibility
**Learning:** The custom `kizuna-shard-btn-wrapper` class used for buttons creates a visually distinct "shard" effect but lacks built-in keyboard focus styles. This makes the app difficult to navigate for keyboard users.
**Action:** When using `kizuna-shard-btn-wrapper` or similar custom components, always explicitly add `focus-visible` utility classes (e.g., `focus-visible:ring-2 focus-visible:ring-cyan-400 focus-visible:outline-none`) to ensure focus visibility.
