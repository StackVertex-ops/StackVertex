/**
 * Integration Tests für Dashboard Access Control
 *
 * Testet: Auth-geschützte Seiten, Redirect-Logik
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { requireAuth, isAuthenticated } from '../../../src/js/lib/auth.js';

// Mock Date.now()
const mockNow = vi.fn(() => 1000000);
global.Date.now = mockNow;

// Mock window.location
delete window.location;
window.location = { href: '', pathname: '/dashboard.html' };

describe('Dashboard Access Control', () => {
    beforeEach(() => {
        localStorage.clear();
        vi.clearAllMocks();
        mockNow.mockReturnValue(1000000);
        window.location.href = '';
        window.location.pathname = '/dashboard.html';
    });

    describe('Authenticated Access', () => {
        beforeEach(() => {
            // Setup valid auth
            localStorage.getItem.mockImplementation((key) => {
                if (key === 'access_token') return 'valid-token-123';
                if (key === 'token_expires') return '2000000'; // In der Zukunft
                if (key === 'user') return JSON.stringify({
                    id: 'user-1',
                    email: 'test@example.com',
                    name: 'Test User',
                    personal_org_id: 'org-1'
                });
                if (key === 'org_id') return 'org-1';
                return null;
            });
        });

        it('erlaubt Dashboard-Zugriff mit validem Token', () => {
            const allowed = requireAuth();

            expect(allowed).toBe(true);
            expect(window.location.href).toBe('');
        });

        it('erlaubt Blueprints-Zugriff mit validem Token', () => {
            window.location.pathname = '/blueprints.html';

            const allowed = requireAuth();

            expect(allowed).toBe(true);
        });

        it('erlaubt Pricing-Zugriff mit validem Token', () => {
            window.location.pathname = '/pricing.html';

            const allowed = requireAuth();

            expect(allowed).toBe(true);
        });

        it('erlaubt Architecture Builder-Zugriff mit validem Token', () => {
            window.location.pathname = '/architecture-builder.html';

            const allowed = requireAuth();

            expect(allowed).toBe(true);
        });

        it('isAuthenticated() gibt true zurück', () => {
            expect(isAuthenticated()).toBe(true);
        });
    });

    describe('Unauthenticated Access', () => {
        beforeEach(() => {
            // No auth data
            localStorage.getItem.mockReturnValue(null);
        });

        it('blockiert Dashboard-Zugriff ohne Token', () => {
            window.location.pathname = '/dashboard.html';

            const allowed = requireAuth();

            expect(allowed).toBe(false);
            expect(window.location.href).toBe('/login.html');
        });

        it('blockiert Blueprints-Zugriff ohne Token', () => {
            window.location.pathname = '/blueprints.html';

            const allowed = requireAuth();

            expect(allowed).toBe(false);
            expect(window.location.href).toBe('/login.html');
        });

        it('blockiert Pricing-Zugriff ohne Token', () => {
            window.location.pathname = '/pricing.html';

            const allowed = requireAuth();

            expect(allowed).toBe(false);
            expect(window.location.href).toBe('/login.html');
        });

        it('blockiert Architecture Builder-Zugriff ohne Token', () => {
            window.location.pathname = '/architecture-builder.html';

            const allowed = requireAuth();

            expect(allowed).toBe(false);
            expect(window.location.href).toBe('/login.html');
        });

        it('speichert return_url für Redirect nach Login', () => {
            window.location.pathname = '/blueprints.html';

            requireAuth();

            expect(localStorage.setItem).toHaveBeenCalledWith('return_url', '/blueprints.html');
        });

        it('isAuthenticated() gibt false zurück', () => {
            expect(isAuthenticated()).toBe(false);
        });
    });

    describe('Expired Token', () => {
        beforeEach(() => {
            // Setup expired token
            localStorage.getItem.mockImplementation((key) => {
                if (key === 'access_token') return 'expired-token';
                if (key === 'token_expires') return '500000'; // In der Vergangenheit
                if (key === 'user') return JSON.stringify({ id: 'user-1' });
                if (key === 'org_id') return 'org-1';
                return null;
            });

            mockNow.mockReturnValue(1000000);
        });

        it('blockiert Dashboard-Zugriff mit expired Token', () => {
            const allowed = requireAuth();

            expect(allowed).toBe(false);
            expect(window.location.href).toBe('/login.html');
        });

        it('cleant localStorage bei expired Token', () => {
            requireAuth();

            expect(localStorage.removeItem).toHaveBeenCalledWith('access_token');
            expect(localStorage.removeItem).toHaveBeenCalledWith('user');
            expect(localStorage.removeItem).toHaveBeenCalledWith('org_id');
            expect(localStorage.removeItem).toHaveBeenCalledWith('token_expires');
        });

        it('isAuthenticated() gibt false zurück bei expired Token', () => {
            expect(isAuthenticated()).toBe(false);
        });
    });

    describe('Edge Cases', () => {
        it('blockiert Zugriff wenn nur access_token vorhanden (kein expires)', () => {
            localStorage.getItem.mockImplementation((key) => {
                if (key === 'access_token') return 'token';
                return null; // token_expires fehlt
            });

            const allowed = requireAuth();

            expect(allowed).toBe(false);
        });

        it('blockiert Zugriff wenn nur token_expires vorhanden (kein token)', () => {
            localStorage.getItem.mockImplementation((key) => {
                if (key === 'token_expires') return '2000000';
                return null; // access_token fehlt
            });

            const allowed = requireAuth();

            expect(allowed).toBe(false);
        });

        it('handhabt korrupte user JSON', async () => {
            localStorage.getItem.mockImplementation((key) => {
                if (key === 'access_token') return 'token';
                if (key === 'token_expires') return '2000000';
                if (key === 'user') return '{invalid json}';
                return null;
            });

            // getCurrentUser() sollte den Fehler werfen
            const { getCurrentUser } = await import('../../../src/js/lib/auth.js');

            expect(() => getCurrentUser()).toThrow();
        });

        it('handhabt fehlende return_url korrekt', async () => {
            localStorage.getItem.mockReturnValue(null);

            const { getReturnUrl } = await import('../../../src/js/lib/auth.js');

            const url = getReturnUrl();

            expect(url).toBe('/dashboard.html'); // Default
        });

        it('handhabt Token der in 1 Sekunde abläuft', () => {
            localStorage.getItem.mockImplementation((key) => {
                if (key === 'access_token') return 'token';
                if (key === 'token_expires') return '1001000'; // +1 Sekunde
                return null;
            });

            mockNow.mockReturnValue(1000000);

            expect(isAuthenticated()).toBe(true);
        });
    });

    describe('Multiple Protected Pages', () => {
        const protectedPages = [
            '/dashboard.html',
            '/blueprints.html',
            '/pricing.html',
            '/architecture-builder.html',
            '/infrastructure-designer.html',
            '/aws-credentials.html',
            '/billing.html'
        ];

        it.each(protectedPages)('blockiert %s ohne Auth', (page) => {
            localStorage.getItem.mockReturnValue(null);
            window.location.pathname = page;

            const allowed = requireAuth();

            expect(allowed).toBe(false);
            expect(window.location.href).toBe('/login.html');
        });

        it.each(protectedPages)('erlaubt %s mit validem Token', (page) => {
            localStorage.getItem.mockImplementation((key) => {
                if (key === 'access_token') return 'token';
                if (key === 'token_expires') return '2000000';
                return null;
            });
            window.location.pathname = page;

            const allowed = requireAuth();

            expect(allowed).toBe(true);
        });
    });
});

describe('Login/Register Page Access', () => {
    beforeEach(() => {
        localStorage.clear();
        vi.clearAllMocks();
        mockNow.mockReturnValue(1000000);
        window.location.href = '';
        window.location.pathname = '/login.html';
    });

    it('erlaubt Login-Zugriff ohne Auth', async () => {
        localStorage.getItem.mockReturnValue(null);

        // Login Page sollte NICHT requireAuth() aufrufen
        // Stattdessen redirectIfAuthenticated()
        const { redirectIfAuthenticated } = await import('../../../src/js/lib/auth.js');

        const redirected = redirectIfAuthenticated();

        expect(redirected).toBe(false); // Kein redirect weil nicht authenticated
        expect(window.location.href).toBe('');
    });

    it('redirected authenticated User von Login zu Dashboard', async () => {
        localStorage.getItem.mockImplementation((key) => {
            if (key === 'access_token') return 'token';
            if (key === 'token_expires') return '2000000';
            return null;
        });

        const { redirectIfAuthenticated } = await import('../../../src/js/lib/auth.js');

        const redirected = redirectIfAuthenticated();

        expect(redirected).toBe(true);
        expect(window.location.href).toBe('/dashboard.html');
    });

    it('erlaubt Register-Zugriff ohne Auth', async () => {
        localStorage.getItem.mockReturnValue(null);
        window.location.pathname = '/register.html';

        const { redirectIfAuthenticated } = await import('../../../src/js/lib/auth.js');

        const redirected = redirectIfAuthenticated();

        expect(redirected).toBe(false);
    });
});
