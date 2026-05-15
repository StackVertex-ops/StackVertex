/**
 * OverCloud - Billing Page
 *
 * Displays subscription status and allows users to manage their billing.
 */

import { billingAPI } from '../api/billing.js';
import { requireAuth, getAccessToken, getOrgId } from '../lib/auth.js';

let subscriptionData = null;

/**
 * Initialize billing page
 */
async function init() {
    // Check authentication (redirects to login if not authenticated)
    if (!requireAuth('/src/billing.html')) {
        return;
    }

    const token = getAccessToken();
    const orgId = getOrgId();

    // Load subscription data
    await loadSubscription(orgId, token);

    // Setup event listeners
    setupEventListeners(orgId, token);
}

/**
 * Load subscription data
 * @param {string} orgId - Organisation ID
 * @param {string} token - Access token
 */
async function loadSubscription(orgId, token) {
    const loadingState = document.getElementById('loadingState');
    const errorState = document.getElementById('errorState');
    const subscriptionContent = document.getElementById('subscriptionContent');

    try {
        subscriptionData = await billingAPI.getSubscriptionStatus(orgId, token);

        // Hide loading, show content
        loadingState.classList.add('hidden');
        errorState.classList.add('hidden');
        subscriptionContent.classList.remove('hidden');

        // Render subscription details
        renderSubscription(subscriptionData);

    } catch (error) {
        console.error('Failed to load subscription:', error);

        loadingState.classList.add('hidden');
        showError('Subscription-Daten konnten nicht geladen werden. Bitte versuche es später erneut.');
    }
}

/**
 * Render subscription details
 * @param {Object} data - Subscription data
 */
function renderSubscription(data) {
    const planBadge = document.getElementById('planBadge');
    const statusBadge = document.getElementById('statusBadge');
    const subscriptionDetails = document.getElementById('subscriptionDetails');
    const planActions = document.getElementById('planActions');
    const upgradeCard = document.getElementById('upgradeCard');

    // Plan Badge
    const planColors = {
        'free': 'bg-gray-100 text-gray-800',
        'pro': 'bg-blue-100 text-blue-800',
        'enterprise': 'bg-purple-100 text-purple-800'
    };

    planBadge.textContent = data.plan.toUpperCase();
    planBadge.className = `px-3 py-1 rounded-full text-sm font-medium ${planColors[data.plan.toLowerCase()]}`;

    // Status Badge
    if (data.has_subscription) {
        const statusColors = {
            'active': 'bg-green-100 text-green-800',
            'past_due': 'bg-yellow-100 text-yellow-800',
            'canceled': 'bg-red-100 text-red-800',
            'grace_period': 'bg-orange-100 text-orange-800'
        };

        const statusText = {
            'active': 'Aktiv',
            'past_due': 'Zahlungsrückstand',
            'canceled': 'Gekündigt',
            'grace_period': 'Grace Period'
        };

        statusBadge.textContent = statusText[data.status] || data.status;
        statusBadge.className = `px-3 py-1 rounded-full text-sm font-medium ${statusColors[data.status]}`;
    } else {
        statusBadge.remove();
    }

    // Subscription Details
    let detailsHTML = '';

    if (data.has_subscription) {
        const currentPeriodEnd = new Date(data.current_period_end).toLocaleDateString('de-DE');

        detailsHTML = `
            <p><strong>Intervall:</strong> ${data.interval === 'monthly' ? 'Monatlich' : 'Jährlich'}</p>
            <p><strong>Läuft bis:</strong> ${currentPeriodEnd}</p>
            ${data.cancel_at_period_end ? `
                <p class="text-orange-600">
                    ⚠️ Wird am ${currentPeriodEnd} gekündigt
                </p>
            ` : ''}
            ${data.auto_renewal ? `
                <p class="text-green-600">
                    ✓ Automatische Verlängerung aktiviert
                </p>
            ` : `
                <p class="text-gray-600">
                    Automatische Verlängerung deaktiviert
                </p>
            `}
        `;
    } else {
        detailsHTML = `
            <p class="text-gray-600">Du nutzt den kostenlosen Plan.</p>
        `;
    }

    subscriptionDetails.innerHTML = detailsHTML;

    // Plan Actions
    let actionsHTML = '';

    if (data.plan.toLowerCase() === 'free') {
        actionsHTML = `
            <a href="/src/pricing.html" class="px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition text-center">
                Plan upgraden
            </a>
        `;

        // Show upgrade card
        upgradeCard.classList.remove('hidden');
    } else if (data.has_subscription && !data.cancel_at_period_end) {
        actionsHTML = `
            ${!data.auto_renewal ? `
                <button id="enableAutoRenewalBtn" class="px-4 py-2 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700 transition text-center">
                    Auto-Renewal aktivieren
                </button>
            ` : ''}
            <button id="cancelSubscriptionBtn" class="px-4 py-2 bg-red-600 text-white rounded-lg font-medium hover:bg-red-700 transition text-center">
                Subscription kündigen
            </button>
        `;
    }

    planActions.innerHTML = actionsHTML;
}

/**
 * Setup event listeners
 * @param {string} orgId - Organisation ID
 * @param {string} token - Access token
 */
function setupEventListeners(orgId, token) {
    // Billing Portal Button
    const openBillingPortalBtn = document.getElementById('openBillingPortalBtn');
    if (openBillingPortalBtn) {
        openBillingPortalBtn.addEventListener('click', async () => {
            await openBillingPortal(orgId, token);
        });
    }

    // Enable Auto-Renewal Button (dynamically added)
    document.addEventListener('click', async (e) => {
        if (e.target.id === 'enableAutoRenewalBtn') {
            await enableAutoRenewal(orgId, token);
        }

        if (e.target.id === 'cancelSubscriptionBtn') {
            await cancelSubscription(orgId, token);
        }
    });
}

/**
 * Open Stripe Billing Portal
 * @param {string} orgId - Organisation ID
 * @param {string} token - Access token
 */
async function openBillingPortal(orgId, token) {
    const button = document.getElementById('openBillingPortalBtn');
    const originalText = button.textContent;

    try {
        button.disabled = true;
        button.textContent = 'Wird geöffnet...';

        const returnUrl = window.location.href;
        const response = await billingAPI.createBillingPortalSession(orgId, returnUrl, token);

        if (response.billing_portal_url) {
            window.location.href = response.billing_portal_url;
        } else {
            throw new Error('Keine Billing-Portal-URL erhalten');
        }

    } catch (error) {
        console.error('Failed to open billing portal:', error);
        alert('Billing Portal konnte nicht geöffnet werden. Bitte versuche es erneut.');

        button.disabled = false;
        button.textContent = originalText;
    }
}

/**
 * Enable auto-renewal
 * @param {string} orgId - Organisation ID
 * @param {string} token - Access token
 */
async function enableAutoRenewal(orgId, token) {
    if (!confirm('Möchtest du die automatische Verlängerung aktivieren?')) {
        return;
    }

    try {
        await billingAPI.enableAutoRenewal(orgId, token);

        alert('✓ Automatische Verlängerung aktiviert!');

        // Reload subscription data
        await loadSubscription(orgId, token);

    } catch (error) {
        console.error('Failed to enable auto-renewal:', error);
        alert('Auto-Renewal konnte nicht aktiviert werden. Bitte versuche es erneut.');
    }
}

/**
 * Cancel subscription
 * @param {string} orgId - Organisation ID
 * @param {string} token - Access token
 */
async function cancelSubscription(orgId, token) {
    const confirmed = confirm(
        'Möchtest du deine Subscription wirklich kündigen?\n\n' +
        'Dein Plan bleibt bis zum Ende der bezahlten Periode aktiv. ' +
        'Danach startet eine 30-tägige Grace Period.'
    );

    if (!confirmed) {
        return;
    }

    try {
        // Cancel at period end (not immediately)
        await billingAPI.cancelSubscription(orgId, false, token);

        alert('✓ Subscription wurde gekündigt!\n\nDein Plan läuft noch bis zum Ende der aktuellen Periode.');

        // Reload subscription data
        await loadSubscription(orgId, token);

    } catch (error) {
        console.error('Failed to cancel subscription:', error);
        alert('Kündigung fehlgeschlagen. Bitte versuche es erneut oder kontaktiere den Support.');
    }
}

/**
 * Show error message
 * @param {string} message - Error message
 */
function showError(message) {
    const errorState = document.getElementById('errorState');
    const errorMessage = document.getElementById('errorMessage');

    errorMessage.textContent = message;
    errorState.classList.remove('hidden');
}

// Initialize page when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
