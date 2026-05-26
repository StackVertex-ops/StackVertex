/**
 * StackVertex - Auth Helper
 *
 * Manages authentication state and token storage.
 */

import { authAPI } from '../api/auth.js';

const STORAGE_KEYS = {
    ACCESS_TOKEN: 'access_token',
    USER: 'user',
    ORG_ID: 'org_id',
    TOKEN_EXPIRES: 'token_expires'
};

/**
 * Save authentication data to localStorage
 * @param {Object} tokenResponse - Token response from API
 */
export function saveAuthData(tokenResponse) {
    const { access_token, expires_in, user } = tokenResponse;

    // Calculate expiration timestamp
    const expiresAt = Date.now() + (expires_in * 1000);

    // Save to localStorage
    localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, access_token);
    localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(user));
    localStorage.setItem(STORAGE_KEYS.ORG_ID, user.personal_org_id);
    localStorage.setItem(STORAGE_KEYS.TOKEN_EXPIRES, expiresAt.toString());
}

/**
 * Get access token from localStorage
 * @returns {string|null} Access token or null
 */
export function getAccessToken() {
    return localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);
}

/**
 * Get current user from localStorage
 * @returns {Object|null} User object or null
 */
export function getCurrentUser() {
    const userJson = localStorage.getItem(STORAGE_KEYS.USER);
    return userJson ? JSON.parse(userJson) : null;
}

/**
 * Get organisation ID from localStorage
 * @returns {string|null} Organisation ID or null
 */
export function getOrgId() {
    return localStorage.getItem(STORAGE_KEYS.ORG_ID);
}

/**
 * Check if user is authenticated
 * @returns {boolean} True if user is authenticated
 */
export function isAuthenticated() {
    const token = getAccessToken();
    const expiresAt = localStorage.getItem(STORAGE_KEYS.TOKEN_EXPIRES);

    if (!token || !expiresAt) {
        return false;
    }

    // Check if token is expired
    const now = Date.now();
    const expiry = parseInt(expiresAt);

    if (now >= expiry) {
        console.warn('Token expired, clearing auth data');
        clearAuthData();
        return false;
    }

    return true;
}

/**
 * Clear authentication data (logout)
 */
export function clearAuthData() {
    localStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN);
    localStorage.removeItem(STORAGE_KEYS.USER);
    localStorage.removeItem(STORAGE_KEYS.ORG_ID);
    localStorage.removeItem(STORAGE_KEYS.TOKEN_EXPIRES);
}

/**
 * Require authentication - redirect to login if not authenticated
 * @param {string} redirectAfterLogin - URL to redirect after login
 */
export function requireAuth(redirectAfterLogin = null) {
    if (!isAuthenticated()) {
        const returnUrl = redirectAfterLogin || window.location.pathname;
        localStorage.setItem('return_url', returnUrl);
        window.location.href = '/src/login.html';
        return false;
    }
    return true;
}

/**
 * Redirect if already authenticated
 * @param {string} redirectTo - URL to redirect to (default: dashboard)
 */
export function redirectIfAuthenticated(redirectTo = '/src/index.html') {
    if (isAuthenticated()) {
        window.location.href = redirectTo;
        return true;
    }
    return false;
}

/**
 * Get return URL after login
 * @returns {string} Return URL or default dashboard
 */
export function getReturnUrl() {
    const returnUrl = localStorage.getItem('return_url');
    localStorage.removeItem('return_url');
    return returnUrl || '/src/index.html';
}

/**
 * Logout user
 */
export async function logout() {
    try {
        // Call backend to clear cookie
        await authAPI.logout();
    } catch (error) {
        console.error('Logout API call failed:', error);
        // Continue with client-side logout even if API fails
    }

    // Clear local auth data
    clearAuthData();
    window.location.href = '/src/login.html';
}

/**
 * Refresh user data from API
 * @returns {Promise<Object>} Updated user data
 */
export async function refreshUserData() {
    const token = getAccessToken();

    if (!token) {
        throw new Error('No access token available');
    }

    try {
        const user = await authAPI.getCurrentUser(token);

        // Update stored user data
        localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(user));

        return user;
    } catch (error) {
        console.error('Failed to refresh user data:', error);

        // Token might be invalid, clear auth data
        if (error.message.includes('401')) {
            clearAuthData();
        }

        throw error;
    }
}
