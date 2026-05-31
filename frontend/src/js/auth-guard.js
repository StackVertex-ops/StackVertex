/**
 * StackVertex - Auth Guard
 *
 * Schützt Seiten vor unauthentisiertem Zugriff.
 * Muss als ERSTES Script in geschützten Seiten geladen werden.
 */

import { requireAuth } from './lib/auth.js';

// Sofort beim Laden prüfen
requireAuth();
