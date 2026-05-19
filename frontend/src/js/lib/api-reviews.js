/**
 * Reviews API Client
 */

const API_BASE_URL = window.location.hostname === 'localhost'
    ? 'http://localhost:8000/api/v1'
    : '/api/v1';

/**
 * Submit new review (public)
 * @param {Object} reviewData - Review data {name, email, rating, comment}
 * @returns {Promise<Object>} Created review
 */
export async function submitReview(reviewData) {
    const response = await fetch(`${API_BASE_URL}/reviews`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(reviewData),
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Fehler beim Einreichen des Kommentars');
    }

    return await response.json();
}

/**
 * Get public reviews (approved only)
 * @param {number} limit - Max items to return
 * @returns {Promise<Object>} {reviews: [...], stats: {...}}
 */
export async function getPublicReviews(limit = 20) {
    const response = await fetch(`${API_BASE_URL}/reviews?limit=${limit}`);

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Fehler beim Laden der Bewertungen');
    }

    return await response.json();
}

/**
 * Get rating statistics
 * @returns {Promise<Object>} Rating stats
 */
export async function getRatingStats() {
    const response = await fetch(`${API_BASE_URL}/reviews/stats`);

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Fehler beim Laden der Statistiken');
    }

    return await response.json();
}

/**
 * Get all reviews for moderation (admin only)
 * @param {string|null} status - Filter by status
 * @param {number} limit - Max items
 * @returns {Promise<Array>} List of reviews
 */
export async function getAdminReviews(status = null, limit = 100) {
    const token = localStorage.getItem('access_token');
    const url = status
        ? `${API_BASE_URL}/admin/reviews?status_filter=${status}&limit=${limit}`
        : `${API_BASE_URL}/admin/reviews?limit=${limit}`;

    const response = await fetch(url, {
        headers: {
            'Authorization': `Bearer ${token}`,
        },
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Fehler beim Laden der Reviews');
    }

    return await response.json();
}

/**
 * Approve review (admin only)
 * @param {string} reviewId - Review ID
 * @returns {Promise<Object>} Updated review
 */
export async function approveReview(reviewId) {
    const token = localStorage.getItem('access_token');

    const response = await fetch(`${API_BASE_URL}/admin/reviews/${reviewId}/approve`, {
        method: 'PATCH',
        headers: {
            'Authorization': `Bearer ${token}`,
        },
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Fehler beim Freigeben');
    }

    return await response.json();
}

/**
 * Reject review (admin only)
 * @param {string} reviewId - Review ID
 * @param {string|null} reason - Rejection reason
 * @returns {Promise<Object>} Updated review
 */
export async function rejectReview(reviewId, reason = null) {
    const token = localStorage.getItem('access_token');

    const response = await fetch(`${API_BASE_URL}/admin/reviews/${reviewId}/reject`, {
        method: 'PATCH',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ status: 'rejected', reason }),
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Fehler beim Ablehnen');
    }

    return await response.json();
}

/**
 * Mark review as spam (admin only)
 * @param {string} reviewId - Review ID
 * @returns {Promise<Object>} Updated review
 */
export async function markSpam(reviewId) {
    const token = localStorage.getItem('access_token');

    const response = await fetch(`${API_BASE_URL}/admin/reviews/${reviewId}/spam`, {
        method: 'PATCH',
        headers: {
            'Authorization': `Bearer ${token}`,
        },
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Fehler beim Markieren als Spam');
    }

    return await response.json();
}

/**
 * Bulk approve reviews (admin only)
 * @param {Array<string>} reviewIds - List of review IDs
 * @returns {Promise<Object>} Bulk action result
 */
export async function bulkApproveReviews(reviewIds) {
    const token = localStorage.getItem('access_token');

    const response = await fetch(`${API_BASE_URL}/admin/reviews/bulk-approve`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ review_ids: reviewIds, action: 'approve' }),
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Fehler beim Bulk-Freigeben');
    }

    return await response.json();
}

/**
 * Delete review (admin only)
 * @param {string} reviewId - Review ID
 * @returns {Promise<void>}
 */
export async function deleteReview(reviewId) {
    const token = localStorage.getItem('access_token');

    const response = await fetch(`${API_BASE_URL}/admin/reviews/${reviewId}`, {
        method: 'DELETE',
        headers: {
            'Authorization': `Bearer ${token}`,
        },
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Fehler beim Löschen');
    }
}
