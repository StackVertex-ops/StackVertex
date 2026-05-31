/**
 * Vitest Setup File
 *
 * Globale Test-Setup-Konfiguration für Unit-Tests
 */

import { vi } from 'vitest';

// Mock DOM globals
global.window = window;
global.document = document;
global.navigator = {
    userAgent: 'node.js',
    onLine: true
};

// Mock fetch API
global.fetch = vi.fn();

// Mock localStorage
const localStorageMock = {
    getItem: vi.fn(),
    setItem: vi.fn(),
    removeItem: vi.fn(),
    clear: vi.fn()
};
global.localStorage = localStorageMock;

// Mock sessionStorage
const sessionStorageMock = {
    getItem: vi.fn(),
    setItem: vi.fn(),
    removeItem: vi.fn(),
    clear: vi.fn()
};
global.sessionStorage = sessionStorageMock;

// Mock window.location
delete window.location;
window.location = {
    href: '',
    pathname: '/',
    search: ''
};

// Mock import.meta.env
global.import = {
    meta: {
        env: {
            VITE_API_URL: 'http://localhost:8000'
        }
    }
};

// Reset mocks before each test
beforeEach(() => {
    vi.clearAllMocks();
    localStorageMock.getItem.mockClear();
    localStorageMock.setItem.mockClear();
    localStorageMock.removeItem.mockClear();
    localStorageMock.clear.mockClear();
    sessionStorageMock.getItem.mockClear();
    sessionStorageMock.setItem.mockClear();
    sessionStorageMock.removeItem.mockClear();
    sessionStorageMock.clear.mockClear();

    // Reset window.location
    window.location.href = '';
    window.location.pathname = '/';
    window.location.search = '';

    // Reset navigator
    global.navigator.onLine = true;
});
