/**
 * OverCloud - Billing Page
 *
 * Displays subscription status and allows users to manage their billing.
 */

import { billingAPI } from '../api/billing.js';
import { voucherAPI } from '../api/voucher.js';
import { requireAuth, getAccessToken, getOrgId } from '../lib/auth.js';

let subscriptionData = null;
let validatedVoucher = null;

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

        // Render voucher status
        renderVoucherStatus(subscriptionData);

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

    // Voucher Validation Button
    const validateVoucherBtn = document.getElementById('validateVoucherBtn');
    if (validateVoucherBtn) {
        validateVoucherBtn.addEventListener('click', async () => {
            await handleValidateVoucher(orgId, token);
        });
    }

    // Voucher Input - Enter key
    const voucherInput = document.getElementById('voucherCodeInput');
    if (voucherInput) {
        voucherInput.addEventListener('keypress', async (e) => {
            if (e.key === 'Enter') {
                await handleValidateVoucher(orgId, token);
            }
        });
    }

    // Remove Voucher Button
    const removeVoucherBtn = document.getElementById('removeVoucherBtn');
    if (removeVoucherBtn) {
        removeVoucherBtn.addEventListener('click', async () => {
            await handleRemoveVoucher(orgId, token);
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

/**
 * Render voucher status
 * @param {Object} data - Subscription data
 */
function renderVoucherStatus(data) {
    const activeVoucherDisplay = document.getElementById('activeVoucherDisplay');
    const activeVoucherDetails = document.getElementById('activeVoucherDetails');
    const voucherInputForm = document.getElementById('voucherInputForm');

    // Check if subscription has active voucher
    if (data.subscription && data.subscription.voucher_code) {
        const voucher = data.subscription;

        // Show active voucher display
        activeVoucherDisplay.classList.remove('hidden');
        voucherInputForm.classList.add('hidden');

        // Format discount text
        let discountText = '';
        if (voucher.voucher_discount_type === 'percentage') {
            discountText = `${voucher.voucher_discount_value}% Rabatt`;
        } else {
            discountText = `€${voucher.voucher_discount_value} Rabatt`;
        }

        let appliesText = '';
        if (voucher.voucher_applies_to === 'base_fee') {
            appliesText = 'auf Base Fee';
        } else if (voucher.voucher_applies_to === 'aws_percentage') {
            appliesText = 'auf AWS Markup';
        } else {
            appliesText = 'auf Gesamt';
        }

        activeVoucherDetails.textContent = `Code: ${voucher.voucher_code} - ${discountText} ${appliesText}`;
    } else {
        // Show voucher input form
        activeVoucherDisplay.classList.add('hidden');
        voucherInputForm.classList.remove('hidden');
    }
}

/**
 * Handle voucher validation
 * @param {string} orgId - Organisation ID
 * @param {string} token - Access token
 */
async function handleValidateVoucher(orgId, token) {
    const input = document.getElementById('voucherCodeInput');
    const validateBtn = document.getElementById('validateVoucherBtn');
    const resultDiv = document.getElementById('voucherValidationResult');

    const code = input.value.trim().toUpperCase();

    if (!code) {
        showVoucherResult('error', 'Bitte gib einen Gutscheincode ein.');
        return;
    }

    // Disable button
    const originalText = validateBtn.textContent;
    validateBtn.disabled = true;
    validateBtn.textContent = 'Prüfe...';

    try {
        // Validate voucher
        validatedVoucher = await voucherAPI.validateVoucher(code, token);

        // Show success with details
        let discountText = '';
        if (validatedVoucher.discount_type === 'percentage') {
            discountText = `${validatedVoucher.discount_value}%`;
        } else {
            discountText = `€${validatedVoucher.discount_value}`;
        }

        const appliesText = validatedVoucher.applies_to === 'both' ? 'Gesamt' :
                           validatedVoucher.applies_to === 'base_fee' ? 'Base Fee' : 'AWS Markup';

        showVoucherResult('success',
            `Gültiger Gutschein! ${discountText} Rabatt auf ${appliesText}`,
            true
        );

    } catch (error) {
        console.error('Voucher validation failed:', error);
        showVoucherResult('error', error.message || 'Ungültiger Gutscheincode');
        validatedVoucher = null;
    } finally {
        validateBtn.disabled = false;
        validateBtn.textContent = originalText;
    }
}

/**
 * Show voucher validation result
 * @param {string} type - 'success' or 'error'
 * @param {string} message - Result message
 * @param {boolean} showRedeemButton - Show redeem button
 */
function showVoucherResult(type, message, showRedeemButton = false) {
    const resultDiv = document.getElementById('voucherValidationResult');

    if (type === 'success') {
        resultDiv.innerHTML = `
            <div class="flex items-start p-4 bg-green-50 border border-green-200 rounded-lg">
                <svg class="w-5 h-5 text-green-600 mr-3 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                </svg>
                <div class="flex-1">
                    <p class="text-green-900 font-medium">${message}</p>
                    ${showRedeemButton ? `
                        <button id="redeemVoucherBtn" class="mt-3 px-4 py-2 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700 transition">
                            Gutschein einlösen
                        </button>
                    ` : ''}
                </div>
            </div>
        `;

        // Add redeem button listener
        if (showRedeemButton) {
            setTimeout(() => {
                const redeemBtn = document.getElementById('redeemVoucherBtn');
                if (redeemBtn) {
                    redeemBtn.addEventListener('click', async () => {
                        const orgId = getOrgId();
                        const token = getAccessToken();
                        await handleRedeemVoucher(orgId, token);
                    });
                }
            }, 0);
        }
    } else {
        resultDiv.innerHTML = `
            <div class="flex items-start p-4 bg-red-50 border border-red-200 rounded-lg">
                <svg class="w-5 h-5 text-red-600 mr-3 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                </svg>
                <p class="text-red-900">${message}</p>
            </div>
        `;
    }

    resultDiv.classList.remove('hidden');
}

/**
 * Handle voucher redemption
 * @param {string} orgId - Organisation ID
 * @param {string} token - Access token
 */
async function handleRedeemVoucher(orgId, token) {
    if (!validatedVoucher) {
        showVoucherResult('error', 'Bitte validiere den Gutscheincode zuerst.');
        return;
    }

    const redeemBtn = document.getElementById('redeemVoucherBtn');
    if (redeemBtn) {
        redeemBtn.disabled = true;
        redeemBtn.textContent = 'Löse ein...';
    }

    try {
        await voucherAPI.redeemVoucher(validatedVoucher.code, orgId, token);

        // Success!
        alert(`Gutschein ${validatedVoucher.code} erfolgreich eingelöst!`);

        // Reset
        validatedVoucher = null;
        document.getElementById('voucherCodeInput').value = '';
        document.getElementById('voucherValidationResult').classList.add('hidden');

        // Reload subscription
        await loadSubscription(orgId, token);

    } catch (error) {
        console.error('Voucher redemption failed:', error);
        showVoucherResult('error', error.message || 'Gutschein konnte nicht eingelöst werden.');
    } finally {
        if (redeemBtn) {
            redeemBtn.disabled = false;
            redeemBtn.textContent = 'Gutschein einlösen';
        }
    }
}

/**
 * Handle voucher removal
 * @param {string} orgId - Organisation ID
 * @param {string} token - Access token
 */
async function handleRemoveVoucher(orgId, token) {
    if (!confirm('Möchtest du den Gutschein wirklich entfernen?\n\nHinweis: Der Gutschein bleibt als "verwendet" markiert und kann nicht erneut eingelöst werden.')) {
        return;
    }

    const removeBtn = document.getElementById('removeVoucherBtn');
    if (removeBtn) {
        removeBtn.disabled = true;
        removeBtn.textContent = 'Entferne...';
    }

    try {
        await voucherAPI.removeVoucher(orgId, token);

        alert('Gutschein erfolgreich entfernt!');

        // Reload subscription
        await loadSubscription(orgId, token);

    } catch (error) {
        console.error('Failed to remove voucher:', error);
        alert('Gutschein konnte nicht entfernt werden. Bitte versuche es erneut.');
    } finally {
        if (removeBtn) {
            removeBtn.disabled = false;
            removeBtn.textContent = 'Entfernen';
        }
    }
}

// Initialize page when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
