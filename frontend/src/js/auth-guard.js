/**
 * StackVertex - Auth Guard
 *
 * Schützt Seiten vor unauthentisiertem Zugriff.
 * Muss als ERSTES Script in geschützten Seiten geladen werden.
 *
 * Security Features:
 * - Immediate redirect if not authenticated
 * - Token expiry check
 * - Periodic token validation (every 5 min)
 * - Auto-logout on token expiry
 */

import { requireAuth, isAuthenticated } from './lib/auth.js';

// Sofort beim Laden prüfen
if (!requireAuth()) {
    // Already redirected to login
    throw new Error('Authentication required');
}

// Periodic token validation (every 5 minutes)
// Prevents users from staying logged in with expired tokens
setInterval(() => {
    if (!isAuthenticated()) {
        console.warn('Token expired - redirecting to login');
        window.location.href = '/login.html';
    }
}, 5 * 60 * 1000); // 5 minutes

// Validate token on page visibility change
// User returns to tab → check if still authenticated
document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') {
        if (!isAuthenticated()) {
            console.warn('Token expired while page was hidden - redirecting to login');
            window.location.href = '/login.html';
        }
    }
});
