/**
 * StackVertex - Admin API Client
 *
 * Handles SuperAdmin-related API calls.
 */

import { APIClient } from '../lib/api-client.js';

export class AdminAPI {
    constructor(apiClient = new APIClient()) {
        this.client = apiClient;
    }

    /**
     * Get platform statistics
     * @returns {Promise<Object>} Platform statistics
     */
    async getStatistics() {
        return this.client.get('/api/v1/admin/statistics');
    }

    /**
     * List all users
     * @param {number} skip - Pagination offset
     * @param {number} limit - Max items to return
     * @returns {Promise<Array>} List of users
     */
    async listUsers(skip = 0, limit = 100) {
        return this.client.get(`/api/v1/admin/users?skip=${skip}&limit=${limit}`);
    }

    /**
     * Get user details
     * @param {string} userId - User ID
     * @returns {Promise<Object>} User details
     */
    async getUser(userId) {
        return this.client.get(`/api/v1/admin/users/${userId}`);
    }

    /**
     * Update user status
     * @param {string} userId - User ID
     * @param {string} status - New status (active, inactive, suspended)
     * @param {string} reason - Reason for status change
     * @returns {Promise<Object>} Updated user
     */
    async updateUserStatus(userId, status, reason) {
        return this.client.patch(`/api/v1/admin/users/${userId}/status`, {
            status,
            reason
        });
    }

    /**
     * Update user system role
     * @param {string} userId - User ID
     * @param {string} systemRole - New system role (user, support, auditor, superadmin)
     * @param {string} reason - Reason for role change
     * @returns {Promise<Object>} Updated user
     */
    async updateUserSystemRole(userId, systemRole, reason) {
        return this.client.patch(`/api/v1/admin/users/${userId}/system-role`, {
            system_role: systemRole,
            reason
        });
    }

    /**
     * Reset user password
     * @param {string} userId - User ID
     * @returns {Promise<Object>} New password and user info
     */
    async resetUserPassword(userId) {
        return this.client.post(`/api/v1/admin/users/${userId}/reset-password`, {});
    }

    /**
     * List all organisations
     * @param {number} skip - Pagination offset
     * @param {number} limit - Max items to return
     * @returns {Promise<Array>} List of organisations
     */
    async listOrganisations(skip = 0, limit = 100) {
        return this.client.get(`/api/v1/admin/organisations?skip=${skip}&limit=${limit}`);
    }

    /**
     * Get organisation architectures
     * @param {string} orgId - Organisation ID
     * @returns {Promise<Array>} List of architectures
     */
    async getOrganisationArchitectures(orgId) {
        return this.client.get(`/api/v1/admin/organisations/${orgId}/architectures`);
    }

    /**
     * Get audit logs
     * @param {Object} filters - Filter options
     * @param {string} filters.user - Filter by user email
     * @param {string} filters.action - Filter by action
     * @param {string} filters.resource_type - Filter by resource type
     * @param {string} filters.resource_id - Filter by resource ID
     * @param {string} filters.start_date - Filter by start date
     * @param {string} filters.end_date - Filter by end date
     * @param {number} skip - Pagination offset
     * @param {number} limit - Max items to return
     * @returns {Promise<Object>} Audit logs with pagination
     */
    async getAuditLogs(filters = {}, skip = 0, limit = 100) {
        const params = new URLSearchParams({
            skip: skip.toString(),
            limit: limit.toString(),
            ...Object.fromEntries(
                Object.entries(filters).filter(([_, v]) => v != null)
            )
        });

        return this.client.get(`/api/v1/admin/audit-logs?${params}`);
    }

    /**
     * Impersonate user
     * @param {string} userId - User ID to impersonate
     * @param {string} reason - Reason for impersonation
     * @returns {Promise<Object>} Impersonation token response
     */
    async impersonateUser(userId, reason) {
        return this.client.post(`/api/v1/admin/impersonate/${userId}`, {
            reason
        });
    }
}

// Export singleton instance
export const adminAPI = new AdminAPI();
