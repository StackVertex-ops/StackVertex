/**
 * Unit Tests für Logout Functionality
 *
 * Testet: Logout Flow, Token Clearing, API Call
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';

// Mock window.location
delete window.location;
window.location = { href: '', pathname: '/dashboard.html' };

// Mock modules FIRST (hoisted)
vi.mock('../../../src/js/api/auth.js', () => ({
    authAPI: {
        logout: vi.fn()
    }
}));

// Import after mocking
import { logout, clearAuthData } from '../../../src/js/lib/auth.js';
import { authAPI as mockAuthAPI } from '../../../src/js/api/auth.js';

describe('Logout Functionality', () => {
    beforeEach(() => {
        // Reset localStorage
        localStorage.clear();
        vi.clearAllMocks();
        window.location.href = '';

        // Mock console.error
        vi.spyOn(console, 'error').mockImplementation(() => {});
    });

    afterEach(() => {
        console.error.mockRestore();
    });

    describe('logout()', () => {
        it('ruft authAPI.logout() auf und cleant localStorage', async () => {
            mockAuthAPI.logout.mockResolvedValue({ message: 'Logged out' });

            await logout();

            expect(mockAuthAPI.logout).toHaveBeenCalled();
            expect(localStorage.removeItem).toHaveBeenCalledWith('access_token');
            expect(localStorage.removeItem).toHaveBeenCalledWith('user');
            expect(localStorage.removeItem).toHaveBeenCalledWith('org_id');
            expect(localStorage.removeItem).toHaveBeenCalledWith('token_expires');
        });

        it('redirected zu /login.html nach Logout', async () => {
            mockAuthAPI.logout.mockResolvedValue({ message: 'Logged out' });

            await logout();

            expect(window.location.href).toBe('/login.html');
        });

        it('cleant localStorage auch wenn API-Call fehlschlägt', async () => {
            mockAuthAPI.logout.mockRejectedValue(new Error('Network error'));

            await logout();

            // Trotz Fehler sollte localStorage gecleant werden
            expect(localStorage.removeItem).toHaveBeenCalledWith('access_token');
            expect(localStorage.removeItem).toHaveBeenCalledWith('user');
            expect(localStorage.removeItem).toHaveBeenCalledWith('org_id');
            expect(localStorage.removeItem).toHaveBeenCalledWith('token_expires');

            // Sollte trotzdem redirecten
            expect(window.location.href).toBe('/login.html');

            // Error sollte geloggt werden
            expect(console.error).toHaveBeenCalledWith('Logout API call failed:', expect.any(Error));
        });

        it('loggt Fehler wenn Backend nicht erreichbar', async () => {
            mockAuthAPI.logout.mockRejectedValue(new Error('Failed to fetch'));

            await logout();

            expect(console.error).toHaveBeenCalled();
            expect(window.location.href).toBe('/login.html');
        });
    });

    describe('clearAuthData()', () => {
        it('entfernt alle Auth-relevanten Keys aus localStorage', () => {
            // Erst Daten setzen
            localStorage.setItem('access_token', 'token-123');
            localStorage.setItem('user', JSON.stringify({ id: '1' }));
            localStorage.setItem('org_id', 'org-456');
            localStorage.setItem('token_expires', '999999');

            clearAuthData();

            expect(localStorage.removeItem).toHaveBeenCalledWith('access_token');
            expect(localStorage.removeItem).toHaveBeenCalledWith('user');
            expect(localStorage.removeItem).toHaveBeenCalledWith('org_id');
            expect(localStorage.removeItem).toHaveBeenCalledWith('token_expires');
        });

        it('ist idempotent (kann mehrmals aufgerufen werden)', () => {
            clearAuthData();
            clearAuthData();
            clearAuthData();

            // Sollte keine Fehler werfen
            expect(localStorage.removeItem).toHaveBeenCalled();
        });
    });

    describe('Edge Cases', () => {
        it('handhabt fehlende localStorage items korrekt', async () => {
            // localStorage ist bereits leer
            localStorage.getItem.mockReturnValue(null);

            await logout();

            expect(window.location.href).toBe('/login.html');
        });

        it('handhabt API 401 Unauthorized beim Logout', async () => {
            mockAuthAPI.logout.mockRejectedValue(new Error('401 Unauthorized'));

            await logout();

            // Sollte trotzdem cleanen und redirecten
            expect(localStorage.removeItem).toHaveBeenCalled();
            expect(window.location.href).toBe('/login.html');
        });

        it('handhabt API 500 Server Error beim Logout', async () => {
            mockAuthAPI.logout.mockRejectedValue(new Error('500 Internal Server Error'));

            await logout();

            expect(localStorage.removeItem).toHaveBeenCalled();
            expect(window.location.href).toBe('/login.html');
        });
    });
});
