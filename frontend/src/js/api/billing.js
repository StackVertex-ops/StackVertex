/**
 * StackVertex - Billing API Client
 *
 * Handles all billing and payment related API calls.
 */

import { APIClient } from '../lib/api-client.js';

export class BillingAPI {
    constructor(apiClient = new APIClient()) {
        this.client = apiClient;
    }

    /**
     * Get pricing for all plans (public, no auth required)
     * @returns {Promise<Array>} List of plans with pricing
     */
    async getPricing() {
        return this.client.get('/api/v1/billing/pricing');
    }

    /**
     * Create checkout session for plan upgrade
     * @param {string} orgId - Organisation ID
     * @param {Object} checkoutData - Checkout details
     * @param {string} checkoutData.plan - Plan to purchase (pro, enterprise)
     * @param {string} checkoutData.interval - Billing interval (monthly, yearly)
     * @param {boolean} checkoutData.autoRenewal - Enable auto-renewal
     * @param {string} token - JWT access token
     * @returns {Promise<Object>} Checkout session with URL
     */
    async createCheckoutSession(orgId, checkoutData, token) {
        return this.client.request(`/api/v1/billing/${orgId}/checkout`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(checkoutData)
        });
    }

    /**
     * Create billing portal session
     * @param {string} orgId - Organisation ID
     * @param {string} returnUrl - URL to return to after portal
     * @param {string} token - JWT access token
     * @returns {Promise<Object>} Portal session with URL
     */
    async createBillingPortalSession(orgId, returnUrl, token) {
        return this.client.request(`/api/v1/billing/${orgId}/billing-portal`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ return_url: returnUrl })
        });
    }

    /**
     * Get subscription status
     * @param {string} orgId - Organisation ID
     * @param {string} token - JWT access token
     * @returns {Promise<Object>} Subscription status
     */
    async getSubscriptionStatus(orgId, token) {
        return this.client.request(`/api/v1/billing/${orgId}/subscription`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
    }

    /**
     * Enable auto-renewal for subscription
     * @param {string} orgId - Organisation ID
     * @param {string} token - JWT access token
     * @returns {Promise<Object>} Success message
     */
    async enableAutoRenewal(orgId, token) {
        return this.client.request(`/api/v1/billing/${orgId}/subscription/enable-auto-renewal`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
    }

    /**
     * Cancel subscription
     * @param {string} orgId - Organisation ID
     * @param {boolean} immediately - Cancel immediately (true) or at period end (false)
     * @param {string} token - JWT access token
     * @returns {Promise<Object>} Success message
     */
    async cancelSubscription(orgId, immediately = false, token) {
        return this.client.request(`/api/v1/billing/${orgId}/subscription/cancel?immediately=${immediately}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
    }

    /**
     * Validate voucher code (public endpoint, no auth required)
     * @param {string} code - Voucher code
     * @returns {Promise<Object>} Voucher details with discount percentage
     */
    async validateVoucher(code) {
        return this.client.post('/api/v1/voucher/validate', { code });
    }

    /**
     * Get list of pricing tiers (public endpoint)
     * @returns {Promise<Array>} List of tiers with pricing details
     */
    async getTiers() {
        return this.client.get('/api/v1/billing/tiers');
    }
}

// Export singleton instance
export const billingAPI = new BillingAPI();
