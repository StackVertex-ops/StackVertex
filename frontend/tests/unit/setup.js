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
    userAgent: 'node.js'
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

// Reset mocks before each test
beforeEach(() => {
    vi.clearAllMocks();
    localStorageMock.getItem.mockClear();
    localStorageMock.setItem.mockClear();
    sessionStorageMock.getItem.mockClear();
    sessionStorageMock.setItem.mockClear();
});
