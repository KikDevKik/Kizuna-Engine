## 2025-05-18 - [React Audio Performance]
**Learning:** Directly coupling high-frequency audio data (like volume levels from an AudioWorklet) to React state causes excessive re-renders (e.g., 100+ Hz), blocking the main thread.
**Action:** Use `useRef` to store mutable, high-frequency data and update the DOM directly via `requestAnimationFrame` loops, bypassing React's render cycle entirely for visualizations.
