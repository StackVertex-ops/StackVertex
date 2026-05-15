/**
 * OverCloud - Pricing Page
 *
 * Displays pricing plans with monthly/yearly toggle and checkout functionality.
 */

import { billingAPI } from '../api/billing.js';
import { getAccessToken, getOrgId } from '../lib/auth.js';

let currentInterval = 'monthly';
let pricingData = [];

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
        console.error('Failed to load pricing:', error);

        cardsContainer.innerHTML = `
            <div class="col-span-3 text-center py-12">
                <p class="text-red-600 mb-4">⚠️ Pricing-Daten konnten nicht geladen werden</p>
                <p class="text-gray-600 text-sm">Stelle sicher, dass das Backend läuft.</p>
            </div>
        `;
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
        window.location.href = '/src/login.html';
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
                success_url: `${window.location.origin}/src/billing/success.html`,
                cancel_url: `${window.location.origin}/src/pricing.html`
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

// Initialize page when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
