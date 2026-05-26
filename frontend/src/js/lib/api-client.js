/**
 * StackVertex - API Client
 *
 * Wrapper around Fetch API for communicating with the FastAPI backend.
 * Supports automatic token refresh when Access Token expires (15 min).
 */

export class APIClient {
    /**
     * Create API client
     * @param {string} baseURL - Base URL of the API (e.g., 'http://localhost:8000')
     *
     * SECURITY FIX: No hardcoded URLs - use environment variable.
     * Falls from Vite env (VITE_API_URL), sonst localhost default.
     */
    constructor(baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000') {
        this.baseURL = baseURL.replace(/\/$/, ''); // Remove trailing slash
        this.isRefreshing = false;
        this.refreshPromise = null;
    }

    /**
     * Make HTTP request
     * @param {string} endpoint - API endpoint (e.g., '/health')
     * @param {Object} options - Fetch options
     * @returns {Promise<any>} Response data
     */
    async request(endpoint, options = {}) {
        try {
            return await this._makeRequest(endpoint, options);
        } catch (error) {
            // If 401 and not already refreshing, try refresh
            if (error.message.includes('401') && !this.isRefreshing && endpoint !== '/api/v1/auth/refresh') {
                return await this._retryWithRefresh(endpoint, options);
            }
            throw error;
        }
    }

    /**
     * Internal: Make HTTP request
     * @private
     */
    async _makeRequest(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;

        const config = {
            credentials: 'include',  // Send cookies (Access + Refresh Token)
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
            ...options,
        };

        const response = await fetch(url, config);

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
            throw new Error(error.detail || `HTTP ${response.status}`);
        }

        // 204 No Content hat keinen Body
        if (response.status === 204) {
            return null;
        }

        return await response.json();
    }

    /**
     * Internal: Retry request after refreshing token
     * @private
     */
    async _retryWithRefresh(endpoint, options) {
        // Only one refresh at a time (deduplicate parallel requests)
        if (!this.refreshPromise) {
            this.isRefreshing = true;
            this.refreshPromise = this._refreshToken();
        }

        try {
            await this.refreshPromise;
            // Retry original request
            return await this._makeRequest(endpoint, options);
        } catch (error) {
            // Refresh failed -> redirect to login
            localStorage.removeItem('stackvertex-user');
            window.location.href = '/login.html';
            throw error;
        } finally {
            this.isRefreshing = false;
            this.refreshPromise = null;
        }
    }

    /**
     * Internal: Refresh Access Token using Refresh Token
     * @private
     */
    async _refreshToken() {
        const response = await fetch(`${this.baseURL}/api/v1/auth/refresh`, {
            method: 'POST',
            credentials: 'include',  // Send refresh_token cookie
        });

        if (!response.ok) {
            throw new Error('Refresh failed');
        }

        return await response.json();
    }

    /**
     * GET request
     * @param {string} endpoint - API endpoint
     * @returns {Promise<any>}
     */
    async get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    }

    /**
     * POST request
     * @param {string} endpoint - API endpoint
     * @param {Object} data - Request body
     * @returns {Promise<any>}
     */
    async post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    /**
     * PUT request
     * @param {string} endpoint - API endpoint
     * @param {Object} data - Request body
     * @returns {Promise<any>}
     */
    async put(endpoint, data) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    }

    /**
     * DELETE request
     * @param {string} endpoint - API endpoint
     * @returns {Promise<any>}
     */
    async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }
}
