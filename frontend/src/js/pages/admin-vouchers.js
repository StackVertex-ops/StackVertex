/**
 * OverCloud - Admin Voucher Management
 *
 * SuperAdmin interface für Gutschein-Verwaltung.
 */

import { voucherAPI } from '../api/voucher.js';
import { requireAuth, getAccessToken } from '../lib/auth.js';

let vouchers = [];

/**
 * Initialize admin vouchers page
 */
async function init() {
    // Check authentication (SuperAdmin only in production)
    if (!requireAuth('/src/admin-vouchers.html')) {
        return;
    }

    const token = getAccessToken();

    // Load vouchers
    await loadVouchers(token);

    // Setup event listeners
    setupEventListeners(token);
}

/**
 * Load all vouchers
 * @param {string} token - Access token
 */
async function loadVouchers(token) {
    const loadingState = document.getElementById('loadingState');
    const errorState = document.getElementById('errorState');
    const vouchersContent = document.getElementById('vouchersContent');

    try {
        vouchers = await voucherAPI.listVouchers(token);

        // Hide loading, show content
        loadingState.classList.add('hidden');
        errorState.classList.add('hidden');
        vouchersContent.classList.remove('hidden');

        // Render table
        renderVouchersTable(vouchers);

    } catch (error) {
        console.error('Failed to load vouchers:', error);

        loadingState.classList.add('hidden');
        showError('Gutscheine konnten nicht geladen werden. Bitte versuche es später erneut.');
    }
}

/**
 * Render vouchers table
 * @param {Array} vouchersList - List of vouchers
 */
function renderVouchersTable(vouchersList) {
    const tbody = document.getElementById('vouchersTableBody');

    if (vouchersList.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="px-6 py-12 text-center text-gray-500">
                    Keine Gutscheine vorhanden. Erstelle deinen ersten Gutschein.
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = vouchersList.map(voucher => {
        // Format discount
        let discountText = '';
        if (voucher.discount_type === 'percentage') {
            discountText = `${voucher.discount_value}%`;
        } else {
            discountText = `€${voucher.discount_value}`;
        }

        // Format applies_to
        const appliesText = voucher.applies_to === 'both' ? 'Beide' :
                          voucher.applies_to === 'base_fee' ? 'Base Fee' : 'AWS Markup';

        // Usage stats
        const usageText = voucher.max_uses === -1
            ? `${voucher.current_uses} / unbegrenzt`
            : `${voucher.current_uses} / ${voucher.max_uses}`;

        // Valid dates
        let validText = 'Immer';
        if (voucher.valid_from || voucher.valid_until) {
            const from = voucher.valid_from ? new Date(voucher.valid_from).toLocaleDateString('de-DE') : '-';
            const until = voucher.valid_until ? new Date(voucher.valid_until).toLocaleDateString('de-DE') : '-';
            validText = `${from} bis ${until}`;
        }

        // Status badge
        const statusClass = voucher.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800';
        const statusText = voucher.is_active ? 'Aktiv' : 'Inaktiv';

        return `
            <tr>
                <td class="px-6 py-4 whitespace-nowrap">
                    <span class="font-mono font-semibold text-gray-900">${voucher.code}</span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <span class="text-gray-900 font-medium">${discountText}</span>
                    <span class="text-gray-500 text-sm ml-1">(${voucher.discount_type})</span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-gray-700">
                    ${appliesText}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-gray-700">
                    ${usageText}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                    ${validText}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <span class="px-2 py-1 rounded-full text-xs font-medium ${statusClass}">
                        ${statusText}
                    </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button
                        class="text-blue-600 hover:text-blue-900 mr-3"
                        onclick="window.viewVoucherStats('${voucher.code}')"
                    >
                        Stats
                    </button>
                    ${voucher.is_active ? `
                        <button
                            class="text-red-600 hover:text-red-900"
                            onclick="window.deactivateVoucher('${voucher.code}')"
                        >
                            Deaktivieren
                        </button>
                    ` : `
                        <button
                            class="text-green-600 hover:text-green-900"
                            onclick="window.reactivateVoucher('${voucher.code}')"
                        >
                            Reaktivieren
                        </button>
                    `}
                </td>
            </tr>
        `;
    }).join('');
}

/**
 * Setup event listeners
 * @param {string} token - Access token
 */
function setupEventListeners(token) {
    // Create Voucher Button
    const createVoucherBtn = document.getElementById('createVoucherBtn');
    createVoucherBtn.addEventListener('click', () => {
        openCreateVoucherModal();
    });

    // Close Modal Button
    const closeModalBtn = document.getElementById('closeModalBtn');
    closeModalBtn.addEventListener('click', () => {
        closeCreateVoucherModal();
    });

    // Cancel Modal Button
    const cancelModalBtn = document.getElementById('cancelModalBtn');
    cancelModalBtn.addEventListener('click', () => {
        closeCreateVoucherModal();
    });

    // Create Voucher Form
    const createVoucherForm = document.getElementById('createVoucherForm');
    createVoucherForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        await handleCreateVoucher(token);
    });

    // Code Input - Auto uppercase
    const codeInput = document.getElementById('voucherCodeField');
    codeInput.addEventListener('input', (e) => {
        e.target.value = e.target.value.toUpperCase();
    });
}

/**
 * Open create voucher modal
 */
function openCreateVoucherModal() {
    const modal = document.getElementById('createVoucherModal');
    modal.classList.remove('hidden');
}

/**
 * Close create voucher modal
 */
function closeCreateVoucherModal() {
    const modal = document.getElementById('createVoucherModal');
    modal.classList.add('hidden');

    // Reset form
    document.getElementById('createVoucherForm').reset();
}

/**
 * Handle create voucher form submission
 * @param {string} token - Access token
 */
async function handleCreateVoucher(token) {
    const code = document.getElementById('voucherCodeField').value.trim().toUpperCase();
    const discountType = document.getElementById('discountTypeField').value;
    const discountValue = parseFloat(document.getElementById('discountValueField').value);
    const appliesTo = document.getElementById('appliesToField').value;
    const maxUses = parseInt(document.getElementById('maxUsesField').value);
    const validFrom = document.getElementById('validFromField').value;
    const validUntil = document.getElementById('validUntilField').value;

    // Validate
    if (!code || code.length < 4) {
        alert('Code muss mindestens 4 Zeichen lang sein.');
        return;
    }

    if (discountValue <= 0) {
        alert('Discount Value muss größer als 0 sein.');
        return;
    }

    if (discountType === 'percentage' && discountValue > 100) {
        alert('Percentage Discount kann nicht größer als 100% sein.');
        return;
    }

    // Build request
    const voucherData = {
        code,
        discount_type: discountType,
        discount_value: discountValue,
        applies_to: appliesTo,
        max_uses: maxUses
    };

    if (validFrom) {
        voucherData.valid_from = new Date(validFrom).toISOString();
    }

    if (validUntil) {
        voucherData.valid_until = new Date(validUntil).toISOString();
    }

    try {
        await voucherAPI.createVoucher(voucherData, token);

        alert(`Gutschein ${code} erfolgreich erstellt!`);

        // Close modal
        closeCreateVoucherModal();

        // Reload vouchers
        await loadVouchers(token);

    } catch (error) {
        console.error('Failed to create voucher:', error);
        alert(`Fehler beim Erstellen: ${error.message}`);
    }
}

/**
 * View voucher stats
 * @param {string} code - Voucher code
 */
window.viewVoucherStats = async function(code) {
    const token = getAccessToken();

    try {
        const stats = await voucherAPI.getVoucherStats(code, token);

        const message = `
Gutschein: ${stats.code}

Verwendungen: ${stats.current_uses} / ${stats.max_uses === -1 ? 'unbegrenzt' : stats.max_uses}
Verbleibend: ${stats.remaining_uses === -1 ? 'unbegrenzt' : stats.remaining_uses}
Usage: ${stats.usage_percentage.toFixed(1)}%
Unique Users: ${stats.unique_users}

Status: ${stats.is_active ? 'Aktiv' : 'Inaktiv'}
Gültig von: ${stats.valid_from ? new Date(stats.valid_from).toLocaleDateString('de-DE') : 'Immer'}
Gültig bis: ${stats.valid_until ? new Date(stats.valid_until).toLocaleDateString('de-DE') : 'Immer'}
Zuletzt verwendet: ${stats.last_used_at ? new Date(stats.last_used_at).toLocaleString('de-DE') : 'Nie'}
        `;

        alert(message);

    } catch (error) {
        console.error('Failed to get voucher stats:', error);
        alert(`Fehler beim Laden der Stats: ${error.message}`);
    }
};

/**
 * Deactivate voucher
 * @param {string} code - Voucher code
 */
window.deactivateVoucher = async function(code) {
    if (!confirm(`Möchtest du den Gutschein ${code} wirklich deaktivieren?`)) {
        return;
    }

    const token = getAccessToken();

    try {
        await voucherAPI.deactivateVoucher(code, token);

        alert(`Gutschein ${code} wurde deaktiviert.`);

        // Reload vouchers
        await loadVouchers(token);

    } catch (error) {
        console.error('Failed to deactivate voucher:', error);
        alert(`Fehler beim Deaktivieren: ${error.message}`);
    }
};

/**
 * Reactivate voucher
 * @param {string} code - Voucher code
 */
window.reactivateVoucher = async function(code) {
    if (!confirm(`Möchtest du den Gutschein ${code} reaktivieren?`)) {
        return;
    }

    const token = getAccessToken();

    try {
        await voucherAPI.reactivateVoucher(code, token);

        alert(`Gutschein ${code} wurde reaktiviert.`);

        // Reload vouchers
        await loadVouchers(token);

    } catch (error) {
        console.error('Failed to reactivate voucher:', error);
        alert(`Fehler beim Reaktivieren: ${error.message}`);
    }
};

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
