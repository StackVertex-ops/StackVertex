/**
 * OverCloud - API Client
 *
 * Wrapper around Fetch API for communicating with the FastAPI backend.
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
    }

    /**
     * Make HTTP request
     * @param {string} endpoint - API endpoint (e.g., '/health')
     * @param {Object} options - Fetch options
     * @returns {Promise<any>} Response data
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;

        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
            ...options,
        };

        try {
            const response = await fetch(url, config);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            // 204 No Content hat keinen Body
            if (response.status === 204) {
                return null;
            }

            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
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
