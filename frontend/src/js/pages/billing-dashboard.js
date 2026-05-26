/**
 * Billing Dashboard für eingeloggte User.
 *
 * Zeigt:
 * - Current Subscription
 * - Current Month Costs
 * - Cost Projection
 * - Invoice History
 */

import { API_BASE_URL } from '../api/config.js';
import { getAccessToken, getOrgId } from '../lib/auth.js';

class BillingDashboard {
    constructor() {
        this.orgId = getOrgId();
        this.token = getAccessToken();

        if (!this.token || !this.orgId) {
            window.location.href = '/login.html';
            return;
        }

        this.init();
    }

    async init() {
        await Promise.all([
            this.loadSubscription(),
            this.loadCurrentCosts(),
            this.loadCostProjection(),
            this.loadInvoices()
        ]);
    }

    async loadSubscription() {
        try {
            const response = await fetch(
                `${API_BASE_URL}/billing/${this.orgId}/subscription`,
                {
                    headers: {
                        'Authorization': `Bearer ${this.token}`
                    }
                }
            );

            if (!response.ok) throw new Error('Failed to load subscription');

            const subscription = await response.json();
            this.renderSubscription(subscription);
        } catch (error) {
            console.error('Error loading subscription:', error);
            this.showError('subscription-section', 'Failed to load subscription');
        }
    }

    async loadCurrentCosts() {
        try {
            const response = await fetch(
                `${API_BASE_URL}/billing/${this.orgId}/costs/current`,
                {
                    headers: {
                        'Authorization': `Bearer ${this.token}`
                    }
                }
            );

            if (!response.ok) throw new Error('Failed to load costs');

            const costs = await response.json();
            this.renderCurrentCosts(costs);
        } catch (error) {
            console.error('Error loading costs:', error);
            this.showError('costs-section', 'Failed to load cost data');
        }
    }

    async loadCostProjection() {
        try {
            const response = await fetch(
                `${API_BASE_URL}/billing/${this.orgId}/costs/projection`,
                {
                    headers: {
                        'Authorization': `Bearer ${this.token}`
                    }
                }
            );

            if (!response.ok) throw new Error('Failed to load projection');

            const projection = await response.json();
            this.renderProjection(projection);
        } catch (error) {
            console.error('Error loading projection:', error);
        }
    }

    async loadInvoices() {
        try {
            const response = await fetch(
                `${API_BASE_URL}/billing/${this.orgId}/invoices?limit=10`,
                {
                    headers: {
                        'Authorization': `Bearer ${this.token}`
                    }
                }
            );

            if (!response.ok) throw new Error('Failed to load invoices');

            const invoices = await response.json();
            this.renderInvoices(invoices);
        } catch (error) {
            console.error('Error loading invoices:', error);
            this.showError('invoices-section', 'Failed to load invoices');
        }
    }

    renderSubscription(subscription) {
        const container = document.getElementById('subscription-info');
        if (!container) return;

        if (!subscription.has_subscription) {
            container.innerHTML = `
                <div class="text-center py-8">
                    <p class="text-gray-600 mb-4">No active subscription</p>
                    <a href="/pricing-hybrid.html" class="btn btn-primary">Choose a Plan</a>
                </div>
            `;
            return;
        }

        const periodEnd = new Date(subscription.current_period_end);
        const daysRemaining = Math.ceil((periodEnd - new Date()) / (1000 * 60 * 60 * 24));

        container.innerHTML = `
            <div class="space-y-4">
                <div class="flex justify-between items-start">
                    <div>
                        <h3 class="text-xl font-bold">${subscription.plan.toUpperCase()} Plan</h3>
                        <p class="text-sm text-gray-600">
                            ${subscription.interval === 'monthly' ? 'Monthly' : 'Annual'} billing
                        </p>
                    </div>
                    <span class="px-3 py-1 rounded-full text-xs font-semibold ${
                        subscription.status === 'active' ? 'bg-green-100 text-green-800' :
                        subscription.status === 'trialing' ? 'bg-blue-100 text-blue-800' :
                        'bg-gray-100 text-gray-800'
                    }">
                        ${subscription.status.toUpperCase()}
                    </span>
                </div>

                <div class="border-t pt-4">
                    <p class="text-sm text-gray-600">Current period ends:</p>
                    <p class="font-semibold">${periodEnd.toLocaleDateString('de-DE', {
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric'
                    })}</p>
                    <p class="text-sm text-gray-500">${daysRemaining} days remaining</p>
                </div>

                <div class="flex gap-3 pt-4">
                    <button onclick="manageBilling()" class="btn btn-secondary flex-1">
                        Manage Subscription
                    </button>
                    ${subscription.cancel_at_period_end ? `
                        <button onclick="reactivateSubscription()" class="btn btn-primary flex-1">
                            Reactivate
                        </button>
                    ` : `
                        <button onclick="cancelSubscription()" class="btn btn-outline flex-1">
                            Cancel
                        </button>
                    `}
                </div>

                ${subscription.cancel_at_period_end ? `
                    <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                        <p class="text-sm text-yellow-800">
                            Your subscription will be canceled at the end of the current period.
                        </p>
                    </div>
                ` : ''}
            </div>
        `;
    }

    renderCurrentCosts(costs) {
        const container = document.getElementById('current-costs');
        if (!container) return;

        const totalAWS = costs.total_aws_costs || 0;
        const markupFee = costs.stackvertex_percentage_fee || 0;
        const total = totalAWS + markupFee;

        container.innerHTML = `
            <div class="space-y-4">
                <div>
                    <p class="text-sm text-gray-600">AWS Infrastructure Costs</p>
                    <p class="text-2xl font-bold">€${totalAWS.toFixed(2)}</p>
                </div>
                <div>
                    <p class="text-sm text-gray-600">StackVertex Markup</p>
                    <p class="text-xl font-semibold text-blue-600">€${markupFee.toFixed(2)}</p>
                </div>
                <div class="border-t pt-4">
                    <p class="text-sm text-gray-600">Total This Month (so far)</p>
                    <p class="text-3xl font-bold">€${total.toFixed(2)}</p>
                </div>
            </div>
        `;
    }

    renderProjection(projection) {
        const container = document.getElementById('cost-projection');
        if (!container) return;

        const progressPercent = (projection.days_elapsed / projection.days_in_month) * 100;

        container.innerHTML = `
            <div class="space-y-4">
                <div>
                    <p class="text-sm text-gray-600 mb-2">Month Progress</p>
                    <div class="w-full bg-gray-200 rounded-full h-2">
                        <div
                            class="bg-blue-600 h-2 rounded-full"
                            style="width: ${progressPercent}%"
                        ></div>
                    </div>
                    <p class="text-xs text-gray-500 mt-1">
                        Day ${projection.days_elapsed} of ${projection.days_in_month}
                    </p>
                </div>

                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <p class="text-sm text-gray-600">Current AWS Costs</p>
                        <p class="text-lg font-semibold">€${projection.current_aws_costs.toFixed(2)}</p>
                    </div>
                    <div>
                        <p class="text-sm text-gray-600">Projected Total</p>
                        <p class="text-lg font-bold text-blue-600">€${projection.projected_total.toFixed(2)}</p>
                    </div>
                </div>

                <div class="bg-blue-50 rounded-lg p-3">
                    <p class="text-xs text-gray-700">
                        Based on current usage, your projected end-of-month cost is
                        <strong>€${projection.projected_total.toFixed(2)}</strong>
                        (AWS: €${projection.projected_aws_costs.toFixed(2)} + Markup: €${projection.projected_stackvertex_fee.toFixed(2)})
                    </p>
                </div>
            </div>
        `;
    }

    renderInvoices(invoices) {
        const container = document.getElementById('invoices-list');
        if (!container) return;

        if (invoices.length === 0) {
            container.innerHTML = `
                <div class="text-center py-8 text-gray-500">
                    No invoices yet
                </div>
            `;
            return;
        }

        container.innerHTML = `
            <div class="space-y-3">
                ${invoices.map(invoice => `
                    <div class="flex justify-between items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50">
                        <div>
                            <p class="font-semibold">${invoice.invoice_number}</p>
                            <p class="text-sm text-gray-600">
                                ${new Date(invoice.period_start).toLocaleDateString('de-DE', {
                                    year: 'numeric',
                                    month: 'long'
                                })}
                            </p>
                        </div>
                        <div class="text-right">
                            <p class="font-bold">€${invoice.total.toFixed(2)}</p>
                            <span class="text-xs px-2 py-1 rounded-full ${
                                invoice.status === 'paid' ? 'bg-green-100 text-green-800' :
                                invoice.status === 'sent' ? 'bg-blue-100 text-blue-800' :
                                'bg-gray-100 text-gray-800'
                            }">
                                ${invoice.status.toUpperCase()}
                            </span>
                        </div>
                        <button
                            onclick="viewInvoice('${invoice.invoice_number}')"
                            class="btn btn-sm btn-outline"
                        >
                            View
                        </button>
                    </div>
                `).join('')}
            </div>
        `;
    }

    showError(containerId, message) {
        const container = document.getElementById(containerId);
        if (!container) return;

        container.innerHTML = `
            <div class="bg-red-50 border border-red-200 rounded-lg p-4 text-center">
                <p class="text-red-800">${message}</p>
            </div>
        `;
    }
}

// Global functions for button handlers
window.manageBilling = async function() {
    const orgId = getOrgId();
    const token = getAccessToken();

    try {
        const response = await fetch(
            `${API_BASE_URL}/billing/${orgId}/billing-portal`,
            {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    return_url: window.location.href
                })
            }
        );

        if (!response.ok) throw new Error('Failed to create portal session');

        const data = await response.json();
        window.location.href = data.portal_url;
    } catch (error) {
        console.error('Error opening billing portal:', error);
        alert('Failed to open billing portal. Please try again.');
    }
};

window.viewInvoice = function(invoiceNumber) {
    window.location.href = `/billing/invoice.html?number=${invoiceNumber}`;
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    new BillingDashboard();
});
