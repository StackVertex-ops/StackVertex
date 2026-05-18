/**
 * OverCloud - Auth API Client
 *
 * Handles authentication-related API calls.
 */

import { APIClient } from '../lib/api-client.js';

export class AuthAPI {
    constructor(apiClient = new APIClient()) {
        this.client = apiClient;
    }

    /**
     * Register new user
     * @param {Object} userData - User registration data
     * @param {string} userData.email - Email address
     * @param {string} userData.name - Full name
     * @param {string} userData.password - Password
     * @returns {Promise<Object>} Token response with user data
     */
    async register(userData) {
        return this.client.post('/api/v1/auth/register', {
            email: userData.email.toLowerCase(),
            name: userData.name,
            password: userData.password,
            auth_provider: 'local'
        });
    }

    /**
     * Login with email and password
     * @param {string} email - Email address
     * @param {string} password - Password
     * @returns {Promise<Object>} Token response with user data
     */
    async login(email, password) {
        // OAuth2PasswordRequestForm expects form data
        const formData = new URLSearchParams();
        formData.append('username', email.toLowerCase());
        formData.append('password', password);

        return this.client.request('/api/v1/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: formData
        });
    }

    /**
     * Get current user (requires authentication)
     * @param {string} token - JWT access token
     * @returns {Promise<Object>} User data with organisations
     */
    async getCurrentUser(token) {
        return this.client.request('/api/v1/auth/me', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
    }

    /**
     * Refresh access token
     * @returns {Promise<Object>} New token response
     */
    async refreshToken() {
        return this.client.post('/api/v1/auth/refresh');
    }

    /**
     * Logout user
     * @returns {Promise<Object>} Logout response
     */
    async logout() {
        return this.client.post('/api/v1/auth/logout');
    }
}

// Export singleton instance
export const authAPI = new AuthAPI();
