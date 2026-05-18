/**
 * OverCloud - Voucher API Client
 *
 * API calls für Voucher-Verwaltung.
 */

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Validate voucher code
 * @param {string} code - Voucher code
 * @param {string} token - Access token
 * @returns {Promise<Object>} Validation result
 */
async function validateVoucher(code, token) {
    const response = await fetch(`${API_BASE}/api/v1/voucher/validate`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ code })
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Voucher validation failed');
    }

    return response.json();
}

/**
 * Redeem voucher code
 * @param {string} code - Voucher code
 * @param {string} orgId - Organisation ID
 * @param {string} token - Access token
 * @returns {Promise<Object>} Redemption result
 */
async function redeemVoucher(code, orgId, token) {
    const response = await fetch(`${API_BASE}/api/v1/voucher/redeem`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ code, org_id: orgId })
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Voucher redemption failed');
    }

    return response.json();
}

/**
 * Remove voucher from subscription
 * @param {string} orgId - Organisation ID
 * @param {string} token - Access token
 * @returns {Promise<Object>} Remove result
 */
async function removeVoucher(orgId, token) {
    const response = await fetch(`${API_BASE}/api/v1/voucher/remove/${orgId}`, {
        method: 'DELETE',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to remove voucher');
    }

    return response.json();
}

/**
 * List all vouchers (Admin only)
 * @param {string} token - Access token
 * @param {number} skip - Pagination offset
 * @param {number} limit - Max items
 * @returns {Promise<Array>} Voucher list
 */
async function listVouchers(token, skip = 0, limit = 100) {
    const response = await fetch(
        `${API_BASE}/api/v1/admin/vouchers?skip=${skip}&limit=${limit}`,
        {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        }
    );

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to list vouchers');
    }

    return response.json();
}

/**
 * Get voucher details (Admin only)
 * @param {string} code - Voucher code
 * @param {string} token - Access token
 * @returns {Promise<Object>} Voucher details
 */
async function getVoucherDetails(code, token) {
    const response = await fetch(`${API_BASE}/api/v1/admin/vouchers/${code}`, {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to get voucher');
    }

    return response.json();
}

/**
 * Get voucher usage stats (Admin only)
 * @param {string} code - Voucher code
 * @param {string} token - Access token
 * @returns {Promise<Object>} Usage statistics
 */
async function getVoucherStats(code, token) {
    const response = await fetch(`${API_BASE}/api/v1/admin/vouchers/${code}/stats`, {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to get voucher stats');
    }

    return response.json();
}

/**
 * Create new voucher (Admin only)
 * @param {Object} voucherData - Voucher data
 * @param {string} token - Access token
 * @returns {Promise<Object>} Created voucher
 */
async function createVoucher(voucherData, token) {
    const response = await fetch(`${API_BASE}/api/v1/admin/vouchers`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(voucherData)
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to create voucher');
    }

    return response.json();
}

/**
 * Deactivate voucher (Admin only)
 * @param {string} code - Voucher code
 * @param {string} token - Access token
 * @returns {Promise<Object>} Deactivation result
 */
async function deactivateVoucher(code, token) {
    const response = await fetch(`${API_BASE}/api/v1/admin/vouchers/${code}`, {
        method: 'DELETE',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to deactivate voucher');
    }

    return response.json();
}

/**
 * Reactivate voucher (Admin only)
 * @param {string} code - Voucher code
 * @param {string} token - Access token
 * @returns {Promise<Object>} Reactivation result
 */
async function reactivateVoucher(code, token) {
    const response = await fetch(`${API_BASE}/api/v1/admin/vouchers/${code}/reactivate`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to reactivate voucher');
    }

    return response.json();
}

export const voucherAPI = {
    validateVoucher,
    redeemVoucher,
    removeVoucher,
    listVouchers,
    getVoucherDetails,
    getVoucherStats,
    createVoucher,
    deactivateVoucher,
    reactivateVoucher
};
