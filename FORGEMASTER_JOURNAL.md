# FORGEMASTER'S JOURNAL - PERFORMANCE LEARNINGS ONLY

## 2024-05-22 - [Visual Heartbeat] Learning: Throttling vision to 2000ms significantly reduces bandwidth usage without compromising Gemini's contextual understanding. Action: Implemented strict 2000ms throttle in `useLiveAPI.ts` and updated `JulesSanctuary.tsx` sync rate.

## 2024-05-22 - [Silent Grace] Learning: Raw WebSocket errors disrupt user flow; silent auto-reconnection with exponential backoff provides a smoother experience. Action: Added `shouldReconnect` logic in `useLiveAPI.ts` to handle unexpected closures gracefully.
