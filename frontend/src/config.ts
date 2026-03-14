/**
 * Centralized backend URL config.
 * In development: falls back to localhost:8000.
 * In production (Tauri build or `npm run build`): uses VITE_BACKEND_URL from .env.production.
 */
const BACKEND_URL = import.meta.env.VITE_BACKEND_URL ?? 'http://localhost:8000';

export const API_URL = BACKEND_URL.replace(/\/$/, ''); // strip trailing slash
export const WS_URL = API_URL.replace(/^https/, 'wss').replace(/^http/, 'ws');
