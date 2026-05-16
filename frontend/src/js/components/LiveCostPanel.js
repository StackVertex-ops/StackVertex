/**
 * LiveCostPanel - Real-Time Cost Estimation Panel
 *
 * Zeigt Kosten-Breakdown und updated automatisch bei Form-Änderungen
 */

export class LiveCostPanel {
    /**
     * @param {string} blueprintId - Blueprint ID (z.B. "static-website")
     */
    constructor(blueprintId) {
        this.blueprintId = blueprintId;
        this.costData = null;
        this.updateTimeout = null;
        this.isLoading = false;
        this.error = null;
    }

    /**
     * Updated Kosten basierend auf Form-Daten
     * @param {Object} formData - Form-Daten aus FormBuilder
     */
    async updateCost(formData) {
        // Debounce API calls (wait 500ms after last change)
        clearTimeout(this.updateTimeout);

        this.updateTimeout = setTimeout(async () => {
            await this.fetchCost(formData);
        }, 500);
    }

    /**
     * Fetcht Kosten vom Backend
     * @param {Object} formData - Form-Daten
     */
    async fetchCost(formData) {
        this.isLoading = true;
        this.error = null;
        this.render(); // Show loading state

        try {
            const response = await fetch('http://localhost:8000/api/v1/costs/calculate-live', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    blueprint_id: this.blueprintId,
                    configuration: formData
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Cost calculation failed');
            }

            this.costData = await response.json();
            this.isLoading = false;
            this.render();

        } catch (error) {
            console.error('Cost calculation error:', error);
            this.error = error.message;
            this.isLoading = false;
            this.render();
        }
    }

    /**
     * Rendert das Cost Panel
     */
    render() {
        const container = document.getElementById('liveCostPanel');
        if (!container) {
            console.warn('Live cost panel container not found');
            return;
        }

        // Loading State
        if (this.isLoading) {
            container.innerHTML = `
                <div class="cost-estimation-panel loading">
                    <div class="flex items-center justify-center py-8">
                        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                        <span class="ml-3 text-gray-600">Berechne Kosten...</span>
                    </div>
                </div>
            `;
            return;
        }

        // Error State
        if (this.error) {
            container.innerHTML = `
                <div class="cost-estimation-panel error">
                    <div class="bg-red-50 border border-red-200 rounded-lg p-4">
                        <div class="flex items-start">
                            <svg class="h-5 w-5 text-red-400 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
                            </svg>
                            <div class="ml-3">
                                <h3 class="text-sm font-medium text-red-800">Fehler bei Kostenberechnung</h3>
                                <p class="mt-1 text-sm text-red-700">${this.error}</p>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            return;
        }

        // Empty State
        if (!this.costData) {
            container.innerHTML = `
                <div class="cost-estimation-panel empty">
                    <div class="text-center py-8 text-gray-500">
                        <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                        </svg>
                        <p class="mt-2 text-sm">Fülle das Formular aus, um die Kosten zu sehen</p>
                    </div>
                </div>
            `;
            return;
        }

        // Cost Data Render
        container.innerHTML = `
            <div class="cost-estimation-panel">
                <h3 class="cost-estimation-title">
                    <svg class="inline h-5 w-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                    </svg>
                    Kostenübersicht
                </h3>

                <!-- Cost Items -->
                <div class="space-y-2 mb-4">
                    ${this.costData.items.map(item => `
                        <div class="cost-breakdown-item">
                            <div class="cost-breakdown-label">
                                <span class="cost-service-badge">${item.service}</span>
                                <span class="cost-resource-name">${item.resource}</span>
                            </div>
                            <div class="cost-breakdown-value">
                                $${this.formatCost(item.total)}
                            </div>
                        </div>
                    `).join('')}
                </div>

                <!-- Total -->
                <div class="cost-total">
                    <div class="cost-total-label">Gesamt / Monat</div>
                    <div class="cost-total-value" data-cost="${this.costData.total}">
                        $${this.formatCost(this.costData.total)}
                    </div>
                </div>

                <!-- Assumptions -->
                ${this.costData.assumptions && this.costData.assumptions.length > 0 ? `
                    <div class="cost-assumptions">
                        <div class="cost-assumptions-title">Annahmen:</div>
                        <ul class="cost-assumptions-list">
                            ${this.costData.assumptions.map(assumption => `
                                <li>${assumption}</li>
                            `).join('')}
                        </ul>
                    </div>
                ` : ''}

                <!-- Yearly Projection -->
                <div class="cost-yearly-projection">
                    <div class="flex justify-between text-sm text-gray-600">
                        <span>Hochrechnung / Jahr:</span>
                        <span class="font-semibold">$${this.formatCost(this.costData.total * 12)}</span>
                    </div>
                </div>
            </div>
        `;

        // Animate total value change
        this.animateTotalValue();
    }

    /**
     * Formatiert Kosten mit Tausender-Trennzeichen
     * @param {number} cost - Kosten
     * @returns {string}
     */
    formatCost(cost) {
        if (typeof cost !== 'number') {
            cost = parseFloat(cost);
        }

        return cost.toLocaleString('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    }

    /**
     * Animiert die Total-Value mit Smooth Transition
     */
    animateTotalValue() {
        const totalElement = document.querySelector('.cost-total-value');
        if (!totalElement) return;

        // Add animation class
        totalElement.classList.add('cost-value-updated');

        // Remove after animation
        setTimeout(() => {
            totalElement.classList.remove('cost-value-updated');
        }, 600);
    }

    /**
     * Gibt aktuellen Total Cost zurück
     * @returns {number|null}
     */
    getTotalCost() {
        return this.costData ? this.costData.total : null;
    }

    /**
     * Gibt aktuellen Breakdown zurück
     * @returns {Object|null}
     */
    getCostBreakdown() {
        return this.costData;
    }

    /**
     * Resettet das Panel
     */
    reset() {
        this.costData = null;
        this.error = null;
        this.isLoading = false;
        this.render();
    }
}
