# Sentinel's Journal

## 2025-05-18 - [CRITICAL] Production Auth Bypass via Misconfiguration
**Vulnerability:** In `backend/app/main.py`, the `verify_user` function would default to `"guest_user"` if `GCP_PROJECT_ID` (Production) was set but `FIREBASE_CREDENTIALS` were missing, even if a token was provided. This allowed unauthenticated access in a production environment due to a simple misconfiguration.
**Learning:** `if/elif` chains can be dangerous when handling security fallbacks. Explicitly handle all failure modes, especially in production environments. Do not assume that a missing credential means "development mode" if other signals (like `GCP_PROJECT_ID`) indicate otherwise.
**Prevention:** Always enforce "Fail Securely". If a required security component is missing in a production context, the application should crash or reject the request, not degrade to an insecure state.
