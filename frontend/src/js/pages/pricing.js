/**
 * OverCloud - Hybrid Pricing Page
 *
 * Displays hybrid pricing tiers (Base Fee + % AWS Costs) with interactive calculator.
 */

import { billingAPI } from '../api/billing.js';
import { getAccessToken, getOrgId } from '../lib/auth.js';

let currentInterval = 'monthly';
let pricingData = [];
let hybridPricingData = [];
let appliedVoucher = null; // Speichert den aktuell angewendeten Gutschein

/**
 * Initialize pricing page
 */
async function init() {
    // Setup interval toggle
    setupIntervalToggle();

    // Load and display pricing
    await loadPricing();
}

/**
 * Setup monthly/yearly toggle buttons
 */
function setupIntervalToggle() {
    const monthlyBtn = document.getElementById('monthlyBtn');
    const yearlyBtn = document.getElementById('yearlyBtn');

    if (!monthlyBtn || !yearlyBtn) {
        console.error('Toggle buttons not found');
        return;
    }

    monthlyBtn.addEventListener('click', () => {
        if (currentInterval === 'monthly') return;

        currentInterval = 'monthly';
        monthlyBtn.classList.add('active');
        yearlyBtn.classList.remove('active');

        renderPricingCards();
    });

    yearlyBtn.addEventListener('click', () => {
        if (currentInterval === 'yearly') return;

        currentInterval = 'yearly';
        yearlyBtn.classList.add('active');
        monthlyBtn.classList.remove('active');

        renderPricingCards();
    });
}

/**
 * Load pricing data from API
 */
async function loadPricing() {
    const cardsContainer = document.getElementById('pricingCards');

    try {
        pricingData = await billingAPI.getPricing();
        renderPricingCards();
    } catch (error) {
        console.warn('Failed to load pricing from API, using fallback data:', error);

        // Fallback: Use static pricing data when backend is not available
        pricingData = [
            {
                plan: 'FREE',
                monthly_price_eur: 0,
                yearly_price_eur: 0,
                stripe_monthly_price_id: null,
                stripe_yearly_price_id: null
            },
            {
                plan: 'PRO',
                monthly_price_eur: 29,
                yearly_price_eur: 290,
                stripe_monthly_price_id: 'price_pro_monthly',
                stripe_yearly_price_id: 'price_pro_yearly'
            },
            {
                plan: 'ENTERPRISE',
                monthly_price_eur: 99,
                yearly_price_eur: 990,
                stripe_monthly_price_id: 'price_enterprise_monthly',
                stripe_yearly_price_id: 'price_enterprise_yearly'
            }
        ];

        renderPricingCards();
    }
}

/**
 * Render pricing cards based on current interval
 */
function renderPricingCards() {
    const cardsContainer = document.getElementById('pricingCards');

    if (!cardsContainer) {
        console.error('Pricing cards container not found');
        return;
    }

    // Sortierung: FREE, PRO, ENTERPRISE
    const planOrder = { 'free': 0, 'pro': 1, 'enterprise': 2 };
    const sortedPlans = [...pricingData].sort((a, b) =>
        planOrder[a.plan.toLowerCase()] - planOrder[b.plan.toLowerCase()]
    );

    cardsContainer.innerHTML = sortedPlans.map(plan => {
        const price = currentInterval === 'monthly'
            ? plan.monthly_price_eur
            : plan.yearly_price_eur;

        const pricePerMonth = currentInterval === 'yearly'
            ? (plan.yearly_price_eur / 12).toFixed(2)
            : price;

        const isPopular = plan.plan.toLowerCase() === 'pro';
        const isFree = plan.plan.toLowerCase() === 'free';

        return `
            <div class="bg-white rounded-lg shadow-lg p-8 ${isPopular ? 'ring-2 ring-blue-600 relative' : ''}">
                ${isPopular ? `
                    <div class="absolute -top-4 left-1/2 transform -translate-x-1/2">
                        <span class="bg-blue-600 text-white text-sm font-medium px-4 py-1 rounded-full">
                            🔥 Beliebt
                        </span>
                    </div>
                ` : ''}

                <!-- Plan Name -->
                <h3 class="text-2xl font-bold text-gray-900 mb-2">
                    ${plan.plan.toUpperCase()}
                </h3>

                <!-- Price -->
                <div class="mb-6">
                    ${isFree ? `
                        <div class="text-4xl font-bold text-gray-900">
                            Kostenlos
                        </div>
                        <p class="text-gray-600 text-sm mt-2">
                            Perfekt zum Ausprobieren
                        </p>
                    ` : `
                        <div class="text-4xl font-bold text-gray-900">
                            €${price}
                            <span class="text-lg font-normal text-gray-600">
                                ${currentInterval === 'monthly' ? '/Monat' : '/Jahr'}
                            </span>
                        </div>
                        ${currentInterval === 'yearly' ? `
                            <p class="text-green-600 text-sm mt-2">
                                ≈ €${pricePerMonth}/Monat (17% Ersparnis!)
                            </p>
                        ` : ''}
                    `}
                </div>

                <!-- Features -->
                <ul class="space-y-3 mb-8">
                    ${getFeaturesForPlan(plan.plan).map(feature => `
                        <li class="flex items-start">
                            <svg class="w-5 h-5 text-green-600 mr-2 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                            </svg>
                            <span class="text-gray-700">${feature}</span>
                        </li>
                    `).join('')}
                </ul>

                <!-- CTA Button -->
                ${isFree ? `
                    <button disabled class="w-full py-3 px-6 rounded-lg font-medium bg-gray-100 text-gray-500 cursor-not-allowed">
                        Aktueller Plan
                    </button>
                ` : `
                    <button
                        onclick="handleUpgrade('${plan.plan}', '${currentInterval}')"
                        class="w-full py-3 px-6 rounded-lg font-medium transition
                               ${isPopular
                                   ? 'bg-blue-600 text-white hover:bg-blue-700'
                                   : 'bg-gray-900 text-white hover:bg-gray-800'}"
                    >
                        Jetzt upgraden
                    </button>
                `}

                <!-- Cancellation Info -->
                ${!isFree ? `
                    <p class="text-gray-500 text-xs text-center mt-4">
                        ${currentInterval === 'monthly'
                            ? 'Jederzeit monatlich kündbar'
                            : 'Nach 1 Jahr kündbar'}
                    </p>
                ` : ''}
            </div>
        `;
    }).join('');
}

/**
 * Get features list for a plan
 * @param {string} planName - Plan name (free, pro, enterprise)
 * @returns {Array<string>} Features list
 */
function getFeaturesForPlan(planName) {
    const features = {
        free: [
            'Bis zu 10 Architekturen',
            'Maximal 3 Komponenten pro Architektur',
            'JSON Export',
            'Nur 1 Mitglied (Owner)',
            'Kein Terraform Apply',
            'Community Support'
        ],
        pro: [
            'Unbegrenzte Architekturen',
            'Unbegrenzte Komponenten',
            'Terraform Apply & Deployment',
            'Bis zu 10 Teammitglieder',
            'Versionierung & History',
            'Cost Estimation',
            'Email Support',
            'Backup & Recovery'
        ],
        enterprise: [
            'Alles aus PRO',
            'Unbegrenzte Teammitglieder',
            'Multi-Cloud Support (AWS, Azure, GCP)',
            'Custom Blueprints',
            'Dedicated Support',
            'SLA 99.9%',
            'Advanced Security Features',
            'Audit Logs & Compliance'
        ]
    };

    return features[planName.toLowerCase()] || [];
}

/**
 * Handle upgrade button click
 * @param {string} plan - Plan name
 * @param {string} interval - Billing interval
 */
window.handleUpgrade = async function(plan, interval) {
    // Check if user is logged in
    const token = getAccessToken();
    const orgId = getOrgId();

    if (!token || !orgId) {
        // Save current page as return URL
        localStorage.setItem('return_url', window.location.href);
        alert('Bitte melde dich zuerst an, um einen Plan zu kaufen.');
        window.location.href = '/login.html';
        return;
    }

    try {
        // Show loading state
        const button = event.target;
        const originalText = button.textContent;
        button.disabled = true;
        button.textContent = 'Wird geladen...';

        // Create checkout session
        const response = await billingAPI.createCheckoutSession(
            orgId,
            {
                plan: plan.toLowerCase(),
                interval: interval,
                auto_renewal: false, // Default: no auto-renewal
                success_url: `${window.location.origin}/billing/success.html`,
                cancel_url: `${window.location.origin}/pricing.html`
            },
            token
        );

        // Redirect to Stripe Checkout
        if (response.checkout_url) {
            window.location.href = response.checkout_url;
        } else {
            throw new Error('Keine Checkout-URL erhalten');
        }

    } catch (error) {
        console.error('Upgrade failed:', error);
        alert('Upgrade fehlgeschlagen. Bitte versuche es erneut.');

        // Reset button
        const button = event.target;
        button.disabled = false;
        button.textContent = 'Jetzt upgraden';
    }
};

/**
 * Initialize Pricing Calculator
 */
function initPricingCalculator() {
    const tierSelect = document.getElementById('tier-select');
    const awsCostsInput = document.getElementById('aws-costs');
    const numDeploymentsInput = document.getElementById('num-deployments');
    const voucherCodeInput = document.getElementById('voucher-code');
    const applyVoucherBtn = document.getElementById('apply-voucher-btn');

    if (!tierSelect || !awsCostsInput) {
        return;
    }

    // Load hybrid pricing data
    loadHybridPricing().then(() => {
        // Attach event listeners
        tierSelect.addEventListener('change', calculateCosts);
        awsCostsInput.addEventListener('input', calculateCosts);
        if (numDeploymentsInput) {
            numDeploymentsInput.addEventListener('input', calculateCosts);
        }

        // Voucher code handling
        if (voucherCodeInput && applyVoucherBtn) {
            applyVoucherBtn.addEventListener('click', handleApplyVoucher);
            voucherCodeInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    handleApplyVoucher();
                }
            });
        }

        // Initial calculation
        calculateCosts();
    });
}

/**
 * Load hybrid pricing data from API
 */
async function loadHybridPricing() {
    try {
        const response = await fetch('/api/billing/pricing/hybrid');
        if (!response.ok) throw new Error('Failed to load hybrid pricing');

        hybridPricingData = await response.json();
    } catch (error) {
        console.warn('Failed to load hybrid pricing, using fallback:', error);

        // Fallback data
        hybridPricingData = [
            {
                tier: 'starter',
                base_price_monthly: 10.00,
                aws_cost_percentage: 15
            },
            {
                tier: 'pro',
                base_price_monthly: 50.00,
                aws_cost_percentage: 10
            },
            {
                tier: 'enterprise',
                base_price_monthly: 250.00,
                aws_cost_percentage: 5
            },
            {
                tier: 'payg',
                base_price_monthly: 0.00,
                aws_cost_percentage: 20
            }
        ];
    }
}

/**
 * Handle voucher code application
 */
async function handleApplyVoucher() {
    const voucherCodeInput = document.getElementById('voucher-code');
    const statusEl = document.getElementById('voucher-status');
    const applyBtn = document.getElementById('apply-voucher-btn');

    if (!voucherCodeInput || !statusEl) return;

    const code = voucherCodeInput.value.trim().toUpperCase();

    if (!code) {
        showVoucherStatus('error', 'Bitte gib einen Gutscheincode ein.');
        return;
    }

    // Disable button during validation
    applyBtn.disabled = true;
    applyBtn.textContent = 'Prüfe...';

    try {
        const voucher = await billingAPI.validateVoucher(code);

        if (voucher.valid) {
            appliedVoucher = voucher;
            showVoucherStatus('success', `Gutschein angewendet! Du sparst ${voucher.discount_percentage}%.`);
            voucherCodeInput.disabled = true;
            applyBtn.textContent = 'Angewendet';
            applyBtn.classList.remove('bg-blue-600', 'hover:bg-blue-700');
            applyBtn.classList.add('bg-green-600');

            // Recalculate costs with discount
            calculateCosts();
        } else {
            showVoucherStatus('error', voucher.message || 'Ungültiger Gutscheincode.');
            appliedVoucher = null;
        }
    } catch (error) {
        console.error('Voucher validation error:', error);
        showVoucherStatus('error', 'Fehler bei der Validierung. Bitte versuche es erneut.');
        appliedVoucher = null;
    } finally {
        if (!appliedVoucher) {
            applyBtn.disabled = false;
            applyBtn.textContent = 'Einlösen';
        }
    }
}

/**
 * Show voucher status message
 * @param {string} type - 'success' or 'error'
 * @param {string} message - Status message
 */
function showVoucherStatus(type, message) {
    const statusEl = document.getElementById('voucher-status');
    if (!statusEl) return;

    statusEl.textContent = message;
    statusEl.style.display = 'block';

    // Remove existing classes
    statusEl.classList.remove('hidden', 'text-green-600', 'text-red-600', 'success', 'error');

    // Add appropriate class based on type
    if (type === 'success') {
        statusEl.classList.add('text-green-600', 'success');
    } else {
        statusEl.classList.add('text-red-600', 'error');
    }
}

/**
 * Calculate and display costs based on user input
 */
function calculateCosts() {
    const tierSelect = document.getElementById('tier-select');
    const awsCostsInput = document.getElementById('aws-costs');
    const numDeploymentsInput = document.getElementById('num-deployments');

    if (!tierSelect || !awsCostsInput) return;

    const tier = tierSelect.value;
    const awsCosts = parseFloat(awsCostsInput.value) || 0;
    const numDeployments = numDeploymentsInput ? parseInt(numDeploymentsInput.value) || 0 : 0;

    // Find pricing config
    const config = hybridPricingData.find(p => p.tier === tier);
    if (!config) return;

    const basePrice = config.base_price_monthly;
    const markupPercent = config.aws_cost_percentage;
    const markupFee = awsCosts * (markupPercent / 100);

    let deploymentFees = 0;
    if (tier === 'payg' && numDeployments > 0) {
        deploymentFees = numDeployments * 5.00;
    }

    let subtotal = basePrice + markupFee + deploymentFees;

    // Apply voucher discount if available
    let voucherDiscountAmount = 0;
    let voucherDiscountPercent = 0;
    if (appliedVoucher && appliedVoucher.valid) {
        voucherDiscountPercent = appliedVoucher.discount_percentage;
        voucherDiscountAmount = subtotal * (voucherDiscountPercent / 100);
        subtotal -= voucherDiscountAmount;
    }

    const tax = subtotal * 0.19; // 19% VAT
    const total = subtotal + tax;

    // Update UI
    const baseFeeEl = document.getElementById('base-fee');
    const awsCostDisplayEl = document.getElementById('aws-cost-display');
    const markupPercentEl = document.getElementById('markup-percent');
    const markupFeeEl = document.getElementById('markup-fee');
    const subtotalCostEl = document.getElementById('subtotal-cost');
    const voucherDiscountRow = document.getElementById('voucher-discount-row');
    const voucherDiscountPercentEl = document.getElementById('voucher-discount-percent');
    const voucherDiscountAmountEl = document.getElementById('voucher-discount-amount');
    const totalCostEl = document.getElementById('total-cost');

    if (baseFeeEl) baseFeeEl.textContent = `€${basePrice.toFixed(2)}`;
    if (awsCostDisplayEl) awsCostDisplayEl.textContent = `€${awsCosts.toFixed(2)}`;
    if (markupPercentEl) markupPercentEl.textContent = markupPercent;
    if (markupFeeEl) markupFeeEl.textContent = `€${markupFee.toFixed(2)}`;
    if (subtotalCostEl) subtotalCostEl.textContent = `€${(basePrice + markupFee + deploymentFees).toFixed(2)}`;

    // Show/hide voucher discount
    if (appliedVoucher && appliedVoucher.valid && voucherDiscountAmount > 0) {
        if (voucherDiscountRow) voucherDiscountRow.classList.remove('hidden');
        if (voucherDiscountPercentEl) voucherDiscountPercentEl.textContent = voucherDiscountPercent;
        if (voucherDiscountAmountEl) voucherDiscountAmountEl.textContent = `-€${voucherDiscountAmount.toFixed(2)}`;
    } else {
        if (voucherDiscountRow) voucherDiscountRow.classList.add('hidden');
    }

    if (totalCostEl) totalCostEl.textContent = `€${total.toFixed(2)}`;

    // Show/hide deployment fees for PAYG
    const deploymentRow = document.getElementById('deployment-fees-row');
    const deploymentsGroup = document.getElementById('deployments-group');

    if (tier === 'payg') {
        if (deploymentRow) {
            deploymentRow.style.display = 'flex';
            const deploymentFeesEl = document.getElementById('deployment-fees');
            if (deploymentFeesEl) deploymentFeesEl.textContent = `€${deploymentFees.toFixed(2)}`;
        }
        if (deploymentsGroup) deploymentsGroup.style.display = 'block';
    } else {
        if (deploymentRow) deploymentRow.style.display = 'none';
        if (deploymentsGroup) deploymentsGroup.style.display = 'none';
    }
}

// Initialize page when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        init();
        initPricingCalculator();
    });
} else {
    init();
    initPricingCalculator();
}
