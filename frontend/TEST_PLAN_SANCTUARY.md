# Jules Sanctuary (Neural Lab) Test Plan

This document outlines the testing procedures for the Jules Sanctuary (Neural Lab) hidden interface, ensuring all interactive components function as intended.

## Test Environment
- **Browser:** Chrome / Edge (Latest)
- **Permissions:** Camera access required.
- **Backend:** Must be running locally (`uvicorn backend.app.main:app --reload`).

## Test Cases

### 1. Activation & Visibility
| ID | Action | Expected Result | Pass/Fail |
|----|--------|-----------------|-----------|
| TC-01 | Press `Ctrl + Shift + P` anywhere in the app. | The "Neural Lab" overlay appears, centered on screen. | |
| TC-02 | Click the "X" button in the top-right corner. | The overlay closes. | |
| TC-03 | Press `Ctrl + Shift + P` again while open. | The overlay toggles (closes/opens). | |

### 2. Camera Feed
| ID | Action | Expected Result | Pass/Fail |
|----|--------|-----------------|-----------|
| TC-04 | Open Neural Lab. observe the video feed. | The camera feed is visible. If permission is denied, "NO SIGNAL" is shown. | |
| TC-05 | Verify "LIVE" indicator. | If the backend is connected (`api.connected` is true), a blinking red dot and "LIVE" text appear in the top-right of the video feed. | |

### 3. Image Transmission
| ID | Action | Expected Result | Pass/Fail |
|----|--------|-----------------|-----------|
| TC-06 | Click "CAPTURE FRAME" button. | A log entry "MANUAL: Frame sent" appears in the logs panel. The backend receives the image. | |
| TC-07 | Click "AUTO SYNC (2s)" button. | The button turns red and text changes to "STOP SYNC". Every 2 seconds, a log "AUTO-SYNC: Frame sent" appears. | |
| TC-08 | Click "STOP SYNC". | The button reverts to default style. Logs stop appearing. | |

### 4. AI Interaction Feedback
| ID | Action | Expected Result | Pass/Fail |
|----|--------|-----------------|-----------|
| TC-09 | Trigger an AI response (speak to microphone). | The AI's text response appears in the "Logs" panel, prefixed with `AI: ...`. | |
| TC-10 | Disconnect from AI (Power button in main UI). | The "CONNECTION" status in Neural Lab updates to "DISCONNECTED". | |

## Automated Verification (Ideally)
- Use Playwright to simulate key press `Control+Shift+P`.
- Verify visibility of element with text "NEURAL LAB // JULES ACCESS".
- Verify `video` element exists and has `srcObject` (or is playing).
