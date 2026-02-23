# Sentinel's Journal

## 2025-05-18 - [CRITICAL] Production Auth Bypass via Misconfiguration
**Vulnerability:** In `backend/app/main.py`, the `verify_user` function would default to `"guest_user"` if `GCP_PROJECT_ID` (Production) was set but `FIREBASE_CREDENTIALS` were missing, even if a token was provided. This allowed unauthenticated access in a production environment due to a simple misconfiguration.
**Learning:** `if/elif` chains can be dangerous when handling security fallbacks. Explicitly handle all failure modes, especially in production environments. Do not assume that a missing credential means "development mode" if other signals (like `GCP_PROJECT_ID`) indicate otherwise.
**Prevention:** Always enforce "Fail Securely". If a required security component is missing in a production context, the application should crash or reject the request, not degrade to an insecure state.

## 2025-05-20 - [HIGH] WebSocket Origin Check Bypass (CSWH)
**Vulnerability:** The WebSocket endpoint in `backend/app/main.py` skipped origin verification if the `Origin` header was missing (`if origin and origin not in settings.CORS_ORIGINS:`). This allowed non-browser clients and potential attackers using techniques to omit the header to bypass the whitelist.
**Learning:** Checking for truthiness of a header before validating its value creates a bypass for requests that simply omit that header. For WebSockets, which are susceptible to Cross-Site WebSocket Hijacking (CSWH), the `Origin` header must be strictly enforced.
**Prevention:** Use a "Deny by Default" strategy for security headers. Ensure that the absence of a required header results in rejection unless explicitly permitted (e.g., via a wildcard `*`).

## 2025-05-23 - [MEDIUM] Error Masking in API Endpoints
**Vulnerability:** Several endpoints in `backend/app/routers/agents.py` were catching generic `Exception` and returning `str(e)` in the 500 response, potentially leaking stack traces or internal paths.
**Learning:** Defaulting to `detail=str(e)` is convenient for debugging but dangerous in production.
**Prevention:** Always use a generic "Internal Server Error" message for 500 responses. Log the actual exception with `logger.exception` (which includes stack trace) for internal observability.

## 2025-05-24 - [CRITICAL] Unprotected System Endpoints in Production
**Vulnerability:** The `/api/system/*` endpoints (including `purge-memories` and `config`) were missing the `Depends(get_current_user)` dependency. This meant that even in Production mode (where `GCP_PROJECT_ID` is set), these sensitive endpoints were accessible without any authentication.
**Learning:** Adding a global `get_current_user` dependency to `FastAPI` app or relying on middleware is often safer than adding it to individual routers, but if using router-level dependencies, one must ensure *every* sensitive router includes it.
**Prevention:** Audit all routers to ensure they include the authentication dependency. Consider using `APIRouter(dependencies=[Depends(get_current_user)])` for sensitive routers to enforce auth on all routes within that router.
