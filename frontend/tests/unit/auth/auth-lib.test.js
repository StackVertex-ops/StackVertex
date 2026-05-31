/**
 * Unit Tests für auth.js Library
 *
 * Testet: Token Management, Auth State, Redirects
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import {
    saveAuthData,
    getAccessToken,
    getCurrentUser,
    getOrgId,
    isAuthenticated,
    clearAuthData,
    requireAuth,
    redirectIfAuthenticated,
    getReturnUrl
} from '../../../src/js/lib/auth.js';

// Mock Date.now()
const mockNow = vi.fn(() => 1000000);
global.Date.now = mockNow;

// Mock window.location
delete window.location;
window.location = { href: '', pathname: '/test.html' };

describe('Auth Library - Token Management', () => {
    beforeEach(() => {
        // Clear localStorage
        localStorage.clear();
        vi.clearAllMocks();
        mockNow.mockReturnValue(1000000);
        window.location.href = '';
        window.location.pathname = '/test.html';
    });

    describe('saveAuthData()', () => {
        it('speichert Token, User und Expiry korrekt', () => {
            mockNow.mockReturnValue(1000000); // 1 Sekunde

            const tokenResponse = {
                access_token: 'test-token-123',
                expires_in: 3600, // 3600 Sekunden = 1 Stunde
                user: {
                    id: 'user-123',
                    email: 'test@example.com',
                    name: 'Test User',
                    personal_org_id: 'org-456'
                }
            };

            saveAuthData(tokenResponse);

            expect(localStorage.setItem).toHaveBeenCalledWith('access_token', 'test-token-123');
            expect(localStorage.setItem).toHaveBeenCalledWith('user', JSON.stringify(tokenResponse.user));
            expect(localStorage.setItem).toHaveBeenCalledWith('org_id', 'org-456');
            // expires_in ist in Sekunden, also 3600 * 1000 = 3600000ms
            // 1000000 + 3600000 = 4600000
            expect(localStorage.setItem).toHaveBeenCalledWith('token_expires', '4600000');
        });

        it('berechnet Expiry-Timestamp korrekt', () => {
            mockNow.mockReturnValue(5000000);

            const tokenResponse = {
                access_token: 'token',
                expires_in: 1800, // 30 Minuten
                user: { id: '1', personal_org_id: 'org-1' }
            };

            saveAuthData(tokenResponse);

            expect(localStorage.setItem).toHaveBeenCalledWith('token_expires', '6800000'); // 5000000 + 1800000
        });
    });

    describe('getAccessToken()', () => {
        it('gibt Token zurück wenn vorhanden', () => {
            localStorage.getItem.mockReturnValue('my-token-123');

            const token = getAccessToken();

            expect(token).toBe('my-token-123');
            expect(localStorage.getItem).toHaveBeenCalledWith('access_token');
        });

        it('gibt null zurück wenn kein Token', () => {
            localStorage.getItem.mockReturnValue(null);

            const token = getAccessToken();

            expect(token).toBeNull();
        });
    });

    describe('getCurrentUser()', () => {
        it('parst User-JSON korrekt', () => {
            const user = { id: '123', email: 'test@test.com', name: 'Test' };
            localStorage.getItem.mockReturnValue(JSON.stringify(user));

            const result = getCurrentUser();

            expect(result).toEqual(user);
        });

        it('gibt null zurück wenn kein User gespeichert', () => {
            localStorage.getItem.mockReturnValue(null);

            const result = getCurrentUser();

            expect(result).toBeNull();
        });
    });

    describe('getOrgId()', () => {
        it('gibt Org ID zurück', () => {
            localStorage.getItem.mockReturnValue('org-789');

            const orgId = getOrgId();

            expect(orgId).toBe('org-789');
            expect(localStorage.getItem).toHaveBeenCalledWith('org_id');
        });
    });
});

describe('Auth Library - Authentication State', () => {
    beforeEach(() => {
        localStorage.clear();
        vi.clearAllMocks();
        mockNow.mockReturnValue(1000000);
    });

    describe('isAuthenticated()', () => {
        it('gibt true zurück wenn Token valid und nicht expired', () => {
            localStorage.getItem.mockImplementation((key) => {
                if (key === 'access_token') return 'valid-token';
                if (key === 'token_expires') return '2000000'; // In der Zukunft
                return null;
            });

            mockNow.mockReturnValue(1500000); // Vor Expiry

            expect(isAuthenticated()).toBe(true);
        });

        it('gibt false zurück wenn kein Token vorhanden', () => {
            localStorage.getItem.mockReturnValue(null);

            expect(isAuthenticated()).toBe(false);
        });

        it('gibt false zurück und cleant auth data wenn Token expired', () => {
            localStorage.getItem.mockImplementation((key) => {
                if (key === 'access_token') return 'expired-token';
                if (key === 'token_expires') return '500000'; // In der Vergangenheit
                return null;
            });

            mockNow.mockReturnValue(1000000); // Nach Expiry

            const consoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});

            expect(isAuthenticated()).toBe(false);
            expect(localStorage.removeItem).toHaveBeenCalledWith('access_token');
            expect(localStorage.removeItem).toHaveBeenCalledWith('user');
            expect(localStorage.removeItem).toHaveBeenCalledWith('org_id');
            expect(localStorage.removeItem).toHaveBeenCalledWith('token_expires');
            expect(consoleWarnSpy).toHaveBeenCalledWith('Token expired, clearing auth data');

            consoleWarnSpy.mockRestore();
        });

        it('gibt false zurück wenn Expiry fehlt', () => {
            localStorage.getItem.mockImplementation((key) => {
                if (key === 'access_token') return 'token';
                return null; // Kein token_expires
            });

            expect(isAuthenticated()).toBe(false);
        });

        it('handhabt Grenzfall: genau bei Expiry-Zeit', () => {
            localStorage.getItem.mockImplementation((key) => {
                if (key === 'access_token') return 'token';
                if (key === 'token_expires') return '1000000'; // Genau jetzt
                return null;
            });

            mockNow.mockReturnValue(1000000);

            expect(isAuthenticated()).toBe(false); // >= expiry = expired
        });
    });

    describe('clearAuthData()', () => {
        it('entfernt alle Auth-Keys aus localStorage', () => {
            clearAuthData();

            expect(localStorage.removeItem).toHaveBeenCalledWith('access_token');
            expect(localStorage.removeItem).toHaveBeenCalledWith('user');
            expect(localStorage.removeItem).toHaveBeenCalledWith('org_id');
            expect(localStorage.removeItem).toHaveBeenCalledWith('token_expires');
        });
    });
});

describe('Auth Library - Redirects', () => {
    beforeEach(() => {
        localStorage.clear();
        vi.clearAllMocks();
        mockNow.mockReturnValue(1000000);
        window.location.href = '';
        window.location.pathname = '/blueprints.html';
    });

    describe('requireAuth()', () => {
        it('gibt true zurück wenn authenticated', () => {
            localStorage.getItem.mockImplementation((key) => {
                if (key === 'access_token') return 'token';
                if (key === 'token_expires') return '2000000';
                return null;
            });

            const result = requireAuth();

            expect(result).toBe(true);
            expect(window.location.href).toBe(''); // Kein Redirect
        });

        it('redirected zu /login.html wenn nicht authenticated', () => {
            localStorage.getItem.mockReturnValue(null);

            const result = requireAuth();

            expect(result).toBe(false);
            expect(window.location.href).toBe('/login.html');
            expect(localStorage.setItem).toHaveBeenCalledWith('return_url', '/blueprints.html');
        });

        it('speichert custom redirectAfterLogin URL', () => {
            localStorage.getItem.mockReturnValue(null);

            requireAuth('/custom-page.html');

            expect(localStorage.setItem).toHaveBeenCalledWith('return_url', '/custom-page.html');
        });
    });

    describe('redirectIfAuthenticated()', () => {
        it('redirected zu /dashboard.html wenn authenticated', () => {
            localStorage.getItem.mockImplementation((key) => {
                if (key === 'access_token') return 'token';
                if (key === 'token_expires') return '2000000';
                return null;
            });

            const result = redirectIfAuthenticated();

            expect(result).toBe(true);
            expect(window.location.href).toBe('/dashboard.html');
        });

        it('redirected zu custom URL wenn angegeben', () => {
            localStorage.getItem.mockImplementation((key) => {
                if (key === 'access_token') return 'token';
                if (key === 'token_expires') return '2000000';
                return null;
            });

            redirectIfAuthenticated('/blueprints.html');

            expect(window.location.href).toBe('/blueprints.html');
        });

        it('gibt false zurück und macht nichts wenn nicht authenticated', () => {
            localStorage.getItem.mockReturnValue(null);

            const result = redirectIfAuthenticated();

            expect(result).toBe(false);
            expect(window.location.href).toBe('');
        });
    });

    describe('getReturnUrl()', () => {
        it('gibt return_url aus localStorage zurück und löscht sie', () => {
            localStorage.getItem.mockReturnValue('/pricing.html');

            const url = getReturnUrl();

            expect(url).toBe('/pricing.html');
            expect(localStorage.getItem).toHaveBeenCalledWith('return_url');
            expect(localStorage.removeItem).toHaveBeenCalledWith('return_url');
        });

        it('gibt /dashboard.html zurück wenn keine return_url', () => {
            localStorage.getItem.mockReturnValue(null);

            const url = getReturnUrl();

            expect(url).toBe('/dashboard.html');
        });
    });
});
