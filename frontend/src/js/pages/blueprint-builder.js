/**
 * Blueprint-based Architecture Builder
 *
 * 3-Step Flow:
 * 1. Blueprint Selection
 * 2. Configuration (Smart Forms)
 * 3. Review & Deploy
 */

import { FormBuilder } from '../components/forms/FormBuilder.js';

// SECURITY FIX: No hardcoded URL
const API_BASE_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000') + '/api/v1';

class BlueprintArchitectureBuilder {
    constructor() {
        this.currentStep = 'select-blueprint';
        this.selectedBlueprint = null;
        this.formBuilder = null;
        this.formData = {};
        this.costEstimate = null;
        this.terraformCode = '';

        this.init();
    }

    async init() {
        // Check URL params für direkte Blueprint-Auswahl
        const urlParams = new URLSearchParams(window.location.search);
        const blueprintId = urlParams.get('blueprint');

        if (blueprintId) {
            // Direkt zu Blueprint gehen
            await this.loadAndSelectBlueprint(blueprintId);
        } else {
            // Blueprints laden
            await this.loadBlueprints();
        }

        this.setupEventListeners();
    }

    // ========================================================================
    // Step 1: Blueprint Selection
    // ========================================================================

    async loadBlueprints() {
        try {
            this.showBlueprintLoading();

            const response = await fetch(`${API_BASE_URL}/blueprints`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            const blueprints = data.blueprints || [];

            this.renderBlueprintGrid(blueprints);
        } catch (error) {
            console.error('Fehler beim Laden der Blueprints:', error);
            this.showBlueprintError(error.message);
        }
    }

    async loadAndSelectBlueprint(blueprintId) {
        try {
            this.showBlueprintLoading();

            const response = await fetch(`${API_BASE_URL}/blueprints/${blueprintId}`);
            if (!response.ok) {
                throw new Error(`Blueprint nicht gefunden: ${blueprintId}`);
            }

            const data = await response.json();
            await this.selectBlueprint(data.blueprint);
        } catch (error) {
            console.error('Fehler beim Laden des Blueprints:', error);
            this.showBlueprintError(error.message);
        }
    }

    renderBlueprintGrid(blueprints) {
        const grid = document.getElementById('blueprintGrid');
        const loadingState = document.getElementById('blueprintLoadingState');

        loadingState.classList.add('hidden');
        grid.classList.remove('hidden');

        grid.innerHTML = blueprints.map(bp => this.renderBlueprintCard(bp)).join('');

        // Click Handlers für Blueprint Cards
        grid.querySelectorAll('.blueprint-card').forEach((card, index) => {
            card.addEventListener('click', () => {
                this.selectBlueprint(blueprints[index]);
            });
        });
    }

    renderBlueprintCard(blueprint) {
        const { metadata } = blueprint;
        const costRange = metadata.estimated_cost;

        return `
            <div class="blueprint-card bg-white rounded-lg shadow-md hover:shadow-xl transition-all overflow-hidden">
                <!-- Header -->
                <div class="p-6 bg-gradient-to-br from-purple-50 to-indigo-50">
                    <div class="flex items-start justify-between mb-3">
                        <div class="text-4xl">${this.getCategoryIcon(metadata.category)}</div>
                        ${this.getDifficultyBadge(metadata.difficulty)}
                    </div>

                    <h3 class="text-xl font-bold text-gray-900 mb-2">
                        ${metadata.name}
                    </h3>

                    <p class="text-sm text-gray-600 line-clamp-2">
                        ${metadata.description}
                    </p>
                </div>

                <!-- Body -->
                <div class="p-6">
                    <!-- Cost -->
                    <div class="mb-4 p-3 bg-gray-50 rounded-lg">
                        <div class="text-xs text-gray-600 mb-1">Geschätzte Kosten/Monat</div>
                        <div class="flex items-baseline gap-2">
                            <span class="text-2xl font-bold text-purple-600">
                                $${costRange.typical_usd}
                            </span>
                            <span class="text-sm text-gray-500">
                                ($${costRange.min_usd} - $${costRange.max_usd})
                            </span>
                        </div>
                    </div>

                    <!-- Setup Time -->
                    <div class="flex items-center gap-2 text-sm text-gray-600 mb-4">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                        </svg>
                        <span>Setup: ~${metadata.setup_time_minutes} Min</span>
                    </div>

                    <!-- CTA -->
                    <button class="w-full px-4 py-2 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 transition">
                        Blueprint verwenden
                    </button>
                </div>
            </div>
        `;
    }

    getCategoryIcon(category) {
        const icons = {
            static: '📄',
            webapp: '🌐',
            api: '🔌',
            database: '💾'
        };
        return icons[category] || '📦';
    }

    getDifficultyBadge(difficulty) {
        const badges = {
            beginner: { label: 'Beginner', class: 'bg-green-100 text-green-700' },
            intermediate: { label: 'Intermediate', class: 'bg-yellow-100 text-yellow-700' },
            advanced: { label: 'Advanced', class: 'bg-red-100 text-red-700' }
        };

        const badge = badges[difficulty] || badges.beginner;
        return `<span class="px-2 py-1 rounded-full text-xs font-medium ${badge.class}">${badge.label}</span>`;
    }

    showBlueprintLoading() {
        document.getElementById('blueprintLoadingState').classList.remove('hidden');
        document.getElementById('blueprintGrid').classList.add('hidden');
        document.getElementById('blueprintErrorState').classList.add('hidden');
    }

    showBlueprintError(message) {
        document.getElementById('blueprintLoadingState').classList.add('hidden');
        document.getElementById('blueprintGrid').classList.add('hidden');
        document.getElementById('blueprintErrorState').classList.remove('hidden');
        document.getElementById('blueprintErrorMessage').textContent = message;
    }

    async selectBlueprint(blueprint) {
        this.selectedBlueprint = blueprint;
        this.goToStep('configure');
        await this.showBlueprintForm();
    }

    // ========================================================================
    // Step 2: Configuration Form
    // ========================================================================

    async showBlueprintForm() {
        if (!this.selectedBlueprint) {
            console.error('Kein Blueprint ausgewählt');
            return;
        }

        // Blueprint Name anzeigen
        document.getElementById('blueprintNameDisplay').textContent = this.selectedBlueprint.metadata.name;

        // FormBuilder initialisieren
        this.formBuilder = new FormBuilder(this.selectedBlueprint);

        // Form rendern
        const formContainer = document.getElementById('blueprint-form-container');
        formContainer.innerHTML = '';
        formContainer.appendChild(this.formBuilder.render());

        // Live Cost Calculation bei Field Changes
        this.formBuilder.onChange(async (field, allData) => {
            this.formData = allData;
            await this.updateCostEstimate(allData);
        });

        // Initiale Kosten berechnen
        this.formData = this.formBuilder.getData();
        await this.updateCostEstimate(this.formData);
    }

    async updateCostEstimate(formData) {
        try {
            this.showCostLoading();

            const response = await fetch(`${API_BASE_URL}/costs/estimate-blueprint`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    blueprint_id: this.selectedBlueprint.metadata.id,
                    configuration: formData
                })
            });

            if (!response.ok) {
                throw new Error(`Fehler bei Kostenberechnung: ${response.status}`);
            }

            const costData = await response.json();
            this.costEstimate = costData;

            this.renderCostBreakdown(costData);
        } catch (error) {
            console.error('Fehler bei Kostenberechnung:', error);
            this.hideCostLoading();
            // Fallback: Schätzung aus Blueprint verwenden
            this.renderCostBreakdown({
                items: [
                    {
                        service: this.selectedBlueprint.metadata.name,
                        amount: this.selectedBlueprint.metadata.estimated_cost.typical_usd,
                        unit: 'monatlich'
                    }
                ],
                total: this.selectedBlueprint.metadata.estimated_cost.typical_usd,
                currency: 'USD',
                period: 'monthly'
            });
        }
    }

    renderCostBreakdown(costData) {
        this.hideCostLoading();

        const breakdownContainer = document.getElementById('costBreakdown');
        const totalCostElement = document.getElementById('totalCost');

        // Items rendern
        breakdownContainer.innerHTML = costData.items.map(item => `
            <div class="cost-item">
                <div>
                    <div class="cost-item-label">${item.service}</div>
                    <div class="cost-item-unit">${item.unit}</div>
                </div>
                <div class="cost-item-amount">$${item.amount.toFixed(2)}</div>
            </div>
        `).join('');

        // Total
        totalCostElement.textContent = `$${costData.total.toFixed(2)}`;
    }

    showCostLoading() {
        document.getElementById('costLoadingState').classList.remove('hidden');
        document.getElementById('costBreakdown').classList.add('hidden');
    }

    hideCostLoading() {
        document.getElementById('costLoadingState').classList.add('hidden');
        document.getElementById('costBreakdown').classList.remove('hidden');
    }

    async continueToReview() {
        // Validierung
        const isValid = await this.formBuilder.validateAll();

        if (!isValid) {
            // Scroll to first error
            await this.formBuilder.showValidation();
            return;
        }

        // Daten speichern
        this.formData = this.formBuilder.getData();

        // Terraform generieren
        await this.generateTerraform();

        // Zu Review gehen
        this.goToStep('review');
        this.showReviewSummary();
    }

    // ========================================================================
    // Step 3: Review & Deploy
    // ========================================================================

    async generateTerraform() {
        try {
            const response = await fetch(`${API_BASE_URL}/terraform/generate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    blueprint_id: this.selectedBlueprint.metadata.id,
                    configuration: this.formData
                })
            });

            if (!response.ok) {
                throw new Error(`Terraform-Generierung fehlgeschlagen: ${response.status}`);
            }

            const data = await response.json();
            this.terraformCode = data.terraform_code || '';
        } catch (error) {
            console.error('Fehler bei Terraform-Generierung:', error);
            this.terraformCode = '# Fehler bei der Generierung\n# Bitte versuchen Sie es später erneut';
        }
    }

    showReviewSummary() {
        // Summary rendern
        const summaryContainer = document.getElementById('architectureSummary');
        summaryContainer.innerHTML = `
            <div class="summary-item">
                <div class="summary-label">Blueprint</div>
                <div class="summary-value">${this.selectedBlueprint.metadata.name}</div>
            </div>
            <div class="summary-item">
                <div class="summary-label">Kategorie</div>
                <div class="summary-value">${this.selectedBlueprint.metadata.category}</div>
            </div>
            <div class="summary-item">
                <div class="summary-label">Geschätzte Kosten</div>
                <div class="summary-value">$${this.costEstimate?.total.toFixed(2) || '0.00'} / Monat</div>
            </div>
            ${Object.entries(this.formData).map(([key, value]) => `
                <div class="summary-item">
                    <div class="summary-label">${this.formatFieldName(key)}</div>
                    <div class="summary-value">${this.formatFieldValue(value)}</div>
                </div>
            `).join('')}
        `;

        // Terraform Code rendern
        document.getElementById('terraformPreview').querySelector('code').textContent = this.terraformCode;
    }

    formatFieldName(name) {
        return name
            .replace(/_/g, ' ')
            .replace(/\b\w/g, l => l.toUpperCase());
    }

    formatFieldValue(value) {
        if (typeof value === 'boolean') {
            return value ? 'Ja' : 'Nein';
        }
        if (typeof value === 'object') {
            return JSON.stringify(value);
        }
        return String(value);
    }

    async downloadTerraform() {
        const blob = new Blob([this.terraformCode], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${this.selectedBlueprint.metadata.id}.tf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    async copyTerraform() {
        try {
            await navigator.clipboard.writeText(this.terraformCode);
            // Visual Feedback
            const button = document.getElementById('copyTerraformBtn');
            const originalText = button.innerHTML;
            button.innerHTML = '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg><span>Kopiert!</span>';
            setTimeout(() => {
                button.innerHTML = originalText;
            }, 2000);
        } catch (error) {
            console.error('Fehler beim Kopieren:', error);
            alert('Fehler beim Kopieren in Zwischenablage');
        }
    }

    async deploy() {
        if (!confirm('Möchten Sie diese Architektur wirklich deployen?')) {
            return;
        }

        try {
            const response = await fetch(`${API_BASE_URL}/deployments`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    blueprint_id: this.selectedBlueprint.metadata.id,
                    configuration: this.formData,
                    terraform_code: this.terraformCode
                })
            });

            if (!response.ok) {
                throw new Error(`Deployment fehlgeschlagen: ${response.status}`);
            }

            const data = await response.json();

            alert('Deployment erfolgreich gestartet!');
            window.location.href = `/deployments.html?id=${data.deployment_id}`;
        } catch (error) {
            console.error('Fehler beim Deployment:', error);
            alert(`Deployment fehlgeschlagen: ${error.message}`);
        }
    }

    // ========================================================================
    // Navigation
    // ========================================================================

    goToStep(stepName) {
        // Update current step
        this.currentStep = stepName;

        // Hide all steps
        document.querySelectorAll('.step-content').forEach(el => {
            el.classList.add('hidden');
        });

        // Show current step
        const stepMap = {
            'select-blueprint': 'blueprintSelection',
            'configure': 'blueprintConfiguration',
            'review': 'blueprintReview'
        };

        const contentId = stepMap[stepName];
        if (contentId) {
            document.getElementById(contentId).classList.remove('hidden');
        }

        // Update step indicators
        this.updateStepIndicators(stepName);

        // Scroll to top
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    updateStepIndicators(currentStep) {
        const steps = ['select-blueprint', 'configure', 'review'];
        const currentIndex = steps.indexOf(currentStep);

        document.querySelectorAll('.step-indicator').forEach((indicator, index) => {
            indicator.classList.remove('active', 'completed');

            if (index < currentIndex) {
                indicator.classList.add('completed');
            } else if (index === currentIndex) {
                indicator.classList.add('active');
            }
        });
    }

    // ========================================================================
    // Event Listeners
    // ========================================================================

    setupEventListeners() {
        // Back to Blueprints
        document.getElementById('backToBlueprintsBtn')?.addEventListener('click', () => {
            this.goToStep('select-blueprint');
        });

        // Continue to Review
        document.getElementById('continueToReviewBtn')?.addEventListener('click', () => {
            this.continueToReview();
        });

        // Back to Config
        document.getElementById('backToConfigBtn')?.addEventListener('click', () => {
            this.goToStep('configure');
        });

        // Download Terraform
        document.getElementById('downloadTerraformBtn')?.addEventListener('click', () => {
            this.downloadTerraform();
        });

        // Copy Terraform
        document.getElementById('copyTerraformBtn')?.addEventListener('click', () => {
            this.copyTerraform();
        });

        // Deploy
        document.getElementById('deployBtn')?.addEventListener('click', () => {
            this.deploy();
        });

        // Toggle Cost Details
        document.getElementById('toggleCostDetails')?.addEventListener('click', (e) => {
            const details = document.getElementById('costBreakdown');
            const button = e.target;

            if (details.classList.contains('expanded')) {
                details.classList.remove('expanded');
                button.textContent = 'Details anzeigen';
            } else {
                details.classList.add('expanded');
                button.textContent = 'Details verbergen';
            }
        });
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new BlueprintArchitectureBuilder();
});
