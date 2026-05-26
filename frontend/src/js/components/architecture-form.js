/**
 * StackVertex - Architecture Form Component
 *
 * Formular für Architecture Metadata und Requirements
 */

import { CLOUD_PROVIDERS, getRegionsForProvider } from '../lib/aws-components.js';

/**
 * Rendert das Architecture Form
 * @param {Object} architecture - Existing architecture data (optional, für Edit-Modus)
 * @param {Function} onSubmit - Callback beim Absenden des Formulars
 * @param {Function} onCancel - Callback beim Abbrechen
 * @returns {string} HTML für das Form
 */
export function renderArchitectureForm(architecture = null, onSubmit = null, onCancel = null) {
    const isEditMode = !!architecture;
    const formData = architecture || getDefaultFormData();

    return `
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow-md">
            <div class="border-b border-gray-200 dark:border-gray-700 px-6 py-4">
                <h2 class="text-xl font-semibold text-gray-900 dark:text-white">
                    ${isEditMode ? 'Architektur bearbeiten' : 'Neue Architektur erstellen'}
                </h2>
            </div>

            <form id="architecture-form" class="p-6 space-y-6">
                ${renderBasicMetadata(formData)}
                ${renderProviderSelection(formData)}
                ${renderFunctionalRequirements(formData)}
                ${renderNonFunctionalRequirements(formData)}
                ${renderFormActions(isEditMode)}
            </form>
        </div>
    `;
}

/**
 * Hole Default-Formular-Daten
 */
function getDefaultFormData() {
    return {
        metadata: {
            name: '',
            description: '',
            provider: 'aws',
            region: 'eu-central-1',
            tags: []
        },
        version: '1.0.0',
        requirements: {
            functional: {
                workload_type: 'web_application',
                expected_traffic: {
                    concurrent_users: 100,
                    requests_per_second: 10,
                    data_transfer_gb_month: 50
                },
                storage_needs: {
                    database_size_gb: 10,
                    file_storage_gb: 20,
                    requires_object_storage: false
                },
                compute_needs: {
                    cpu_intensive: false,
                    memory_intensive: false,
                    gpu_required: false
                }
            },
            non_functional: {
                availability: {
                    target_uptime_percent: 99.9,
                    multi_az: false,
                    disaster_recovery: false
                },
                scalability: {
                    auto_scaling: false,
                    scale_to_zero: false,
                    global_distribution: false
                },
                security: {
                    compliance_requirements: [],
                    data_encryption: {
                        at_rest: true,
                        in_transit: true
                    },
                    network_isolation: true,
                    public_access: true
                },
                performance: {
                    max_latency_ms: 500,
                    cdn_required: false
                },
                cost: {
                    monthly_budget_usd: 100,
                    cost_optimization_priority: 'medium'
                }
            }
        }
    };
}

/**
 * Rendert Basic Metadata Section
 */
function renderBasicMetadata(data) {
    return `
        <div class="space-y-4">
            <h3 class="text-lg font-medium text-gray-900 dark:text-white border-b border-gray-200 dark:border-gray-700 pb-2">
                Grundlegende Informationen
            </h3>

            <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Name <span class="text-red-500">*</span>
                </label>
                <input
                    type="text"
                    name="name"
                    id="arch-name"
                    value="${escapeHtml(data.metadata?.name || '')}"
                    required
                    class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="z.B. E-Commerce Platform"
                />
            </div>

            <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Beschreibung
                </label>
                <textarea
                    name="description"
                    id="arch-description"
                    rows="3"
                    class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Kurze Beschreibung der Architektur..."
                >${escapeHtml(data.metadata?.description || '')}</textarea>
            </div>

            <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Version
                </label>
                <input
                    type="text"
                    name="version"
                    id="arch-version"
                    value="${escapeHtml(data.version || '1.0.0')}"
                    pattern="\\d+\\.\\d+\\.\\d+"
                    class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="1.0.0"
                />
                <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">Format: Major.Minor.Patch (z.B. 1.0.0)</p>
            </div>
        </div>
    `;
}

/**
 * Rendert Provider Selection Section
 */
function renderProviderSelection(data) {
    const selectedProvider = data.metadata?.provider || 'aws';
    const selectedRegion = data.metadata?.region || 'eu-central-1';

    return `
        <div class="space-y-4">
            <h3 class="text-lg font-medium text-gray-900 dark:text-white border-b border-gray-200 dark:border-gray-700 pb-2">
                Cloud Provider
            </h3>

            <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Provider <span class="text-red-500">*</span>
                </label>
                <div class="grid grid-cols-3 gap-4">
                    ${Object.entries(CLOUD_PROVIDERS).map(([key, provider]) => {
                        const isSelected = selectedProvider === key;
                        const isDisabled = !provider.available;

                        return `
                            <div class="relative">
                                <input
                                    type="radio"
                                    name="provider"
                                    id="provider-${key}"
                                    value="${key}"
                                    ${isSelected ? 'checked' : ''}
                                    ${isDisabled ? 'disabled' : ''}
                                    class="peer sr-only"
                                    onchange="window.StackVertex.updateRegionOptions('${key}')"
                                />
                                <label
                                    for="provider-${key}"
                                    class="flex flex-col items-center justify-center p-4 border-2 rounded-lg cursor-pointer transition-all
                                        ${isDisabled ? 'opacity-50 cursor-not-allowed bg-gray-100 dark:bg-gray-900' : 'hover:border-blue-400'}
                                        ${isSelected ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' : 'border-gray-300 dark:border-gray-600'}
                                        peer-focus:ring-2 peer-focus:ring-blue-500"
                                >
                                    <span class="text-3xl mb-2">${provider.icon}</span>
                                    <span class="font-medium text-gray-900 dark:text-white">${provider.short}</span>
                                    ${isDisabled ? '<span class="text-xs text-orange-600 dark:text-orange-400 mt-1">Coming Soon</span>' : ''}
                                </label>
                            </div>
                        `;
                    }).join('')}
                </div>
            </div>

            <div id="region-selection">
                ${renderRegionSelection(selectedProvider, selectedRegion)}
            </div>
        </div>
    `;
}

/**
 * Rendert Region Selection
 */
function renderRegionSelection(provider, selectedRegion) {
    const regions = getRegionsForProvider(provider);

    if (regions.length === 0) {
        return '';
    }

    return `
        <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Region
            </label>
            <select
                name="region"
                id="arch-region"
                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
                ${regions.map(region => `
                    <option value="${region.id}" ${selectedRegion === region.id ? 'selected' : ''}>
                        ${region.name}
                    </option>
                `).join('')}
            </select>
        </div>
    `;
}

/**
 * Rendert Functional Requirements Section
 */
function renderFunctionalRequirements(data) {
    const func = data.requirements?.functional || {};

    return `
        <div class="space-y-4">
            <h3 class="text-lg font-medium text-gray-900 dark:text-white border-b border-gray-200 dark:border-gray-700 pb-2">
                Funktionale Anforderungen
            </h3>

            <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Workload-Typ
                </label>
                <select
                    name="workload_type"
                    id="workload-type"
                    class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
                >
                    <option value="web_application" ${func.workload_type === 'web_application' ? 'selected' : ''}>Web Application</option>
                    <option value="api_service" ${func.workload_type === 'api_service' ? 'selected' : ''}>API Service</option>
                    <option value="static_website" ${func.workload_type === 'static_website' ? 'selected' : ''}>Static Website</option>
                    <option value="data_processing" ${func.workload_type === 'data_processing' ? 'selected' : ''}>Data Processing</option>
                    <option value="microservices" ${func.workload_type === 'microservices' ? 'selected' : ''}>Microservices</option>
                    <option value="serverless_function" ${func.workload_type === 'serverless_function' ? 'selected' : ''}>Serverless Function</option>
                    <option value="container_workload" ${func.workload_type === 'container_workload' ? 'selected' : ''}>Container Workload</option>
                    <option value="batch_job" ${func.workload_type === 'batch_job' ? 'selected' : ''}>Batch Job</option>
                </select>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                    <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Gleichzeitige Nutzer
                    </label>
                    <input
                        type="number"
                        name="concurrent_users"
                        id="concurrent-users"
                        value="${func.expected_traffic?.concurrent_users || 100}"
                        min="1"
                        class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
                    />
                </div>

                <div>
                    <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Requests pro Sekunde
                    </label>
                    <input
                        type="number"
                        name="requests_per_second"
                        id="requests-per-second"
                        value="${func.expected_traffic?.requests_per_second || 10}"
                        min="1"
                        class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
                    />
                </div>

                <div>
                    <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Datenbank-Größe (GB)
                    </label>
                    <input
                        type="number"
                        name="database_size_gb"
                        id="database-size"
                        value="${func.storage_needs?.database_size_gb || 10}"
                        min="0"
                        class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
                    />
                </div>

                <div>
                    <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        File Storage (GB)
                    </label>
                    <input
                        type="number"
                        name="file_storage_gb"
                        id="file-storage"
                        value="${func.storage_needs?.file_storage_gb || 20}"
                        min="0"
                        class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
                    />
                </div>
            </div>

            <div class="space-y-2">
                <label class="flex items-center">
                    <input
                        type="checkbox"
                        name="requires_object_storage"
                        id="requires-object-storage"
                        ${func.storage_needs?.requires_object_storage ? 'checked' : ''}
                        class="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    />
                    <span class="ml-2 text-sm text-gray-700 dark:text-gray-300">Object Storage benötigt (S3/Blob)</span>
                </label>

                <label class="flex items-center">
                    <input
                        type="checkbox"
                        name="cpu_intensive"
                        id="cpu-intensive"
                        ${func.compute_needs?.cpu_intensive ? 'checked' : ''}
                        class="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    />
                    <span class="ml-2 text-sm text-gray-700 dark:text-gray-300">CPU-intensiv</span>
                </label>

                <label class="flex items-center">
                    <input
                        type="checkbox"
                        name="memory_intensive"
                        id="memory-intensive"
                        ${func.compute_needs?.memory_intensive ? 'checked' : ''}
                        class="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    />
                    <span class="ml-2 text-sm text-gray-700 dark:text-gray-300">RAM-intensiv</span>
                </label>

                <label class="flex items-center">
                    <input
                        type="checkbox"
                        name="gpu_required"
                        id="gpu-required"
                        ${func.compute_needs?.gpu_required ? 'checked' : ''}
                        class="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    />
                    <span class="ml-2 text-sm text-gray-700 dark:text-gray-300">GPU benötigt</span>
                </label>
            </div>
        </div>
    `;
}

/**
 * Rendert Non-Functional Requirements Section
 */
function renderNonFunctionalRequirements(data) {
    const nonFunc = data.requirements?.non_functional || {};

    return `
        <div class="space-y-4">
            <h3 class="text-lg font-medium text-gray-900 dark:text-white border-b border-gray-200 dark:border-gray-700 pb-2">
                Nicht-funktionale Anforderungen
            </h3>

            <!-- Availability -->
            <div class="bg-gray-50 dark:bg-gray-900 p-4 rounded-lg space-y-3">
                <h4 class="font-medium text-gray-900 dark:text-white">Verfügbarkeit</h4>

                <div>
                    <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Ziel-Uptime (%)
                    </label>
                    <input
                        type="number"
                        name="target_uptime_percent"
                        id="target-uptime"
                        value="${nonFunc.availability?.target_uptime_percent || 99.9}"
                        min="90"
                        max="100"
                        step="0.1"
                        class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
                    />
                </div>

                <label class="flex items-center">
                    <input
                        type="checkbox"
                        name="multi_az"
                        id="multi-az"
                        ${nonFunc.availability?.multi_az ? 'checked' : ''}
                        class="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    />
                    <span class="ml-2 text-sm text-gray-700 dark:text-gray-300">Multi-AZ Deployment</span>
                </label>

                <label class="flex items-center">
                    <input
                        type="checkbox"
                        name="disaster_recovery"
                        id="disaster-recovery"
                        ${nonFunc.availability?.disaster_recovery ? 'checked' : ''}
                        class="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    />
                    <span class="ml-2 text-sm text-gray-700 dark:text-gray-300">Disaster Recovery</span>
                </label>
            </div>

            <!-- Scalability -->
            <div class="bg-gray-50 dark:bg-gray-900 p-4 rounded-lg space-y-3">
                <h4 class="font-medium text-gray-900 dark:text-white">Skalierbarkeit</h4>

                <label class="flex items-center">
                    <input
                        type="checkbox"
                        name="auto_scaling"
                        id="auto-scaling"
                        ${nonFunc.scalability?.auto_scaling ? 'checked' : ''}
                        class="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    />
                    <span class="ml-2 text-sm text-gray-700 dark:text-gray-300">Auto-Scaling</span>
                </label>

                <label class="flex items-center">
                    <input
                        type="checkbox"
                        name="scale_to_zero"
                        id="scale-to-zero"
                        ${nonFunc.scalability?.scale_to_zero ? 'checked' : ''}
                        class="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    />
                    <span class="ml-2 text-sm text-gray-700 dark:text-gray-300">Scale to Zero (Serverless)</span>
                </label>

                <label class="flex items-center">
                    <input
                        type="checkbox"
                        name="global_distribution"
                        id="global-distribution"
                        ${nonFunc.scalability?.global_distribution ? 'checked' : ''}
                        class="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    />
                    <span class="ml-2 text-sm text-gray-700 dark:text-gray-300">Globale Verteilung</span>
                </label>
            </div>

            <!-- Security -->
            <div class="bg-gray-50 dark:bg-gray-900 p-4 rounded-lg space-y-3">
                <h4 class="font-medium text-gray-900 dark:text-white">Sicherheit</h4>

                <label class="flex items-center">
                    <input
                        type="checkbox"
                        name="encryption_at_rest"
                        id="encryption-at-rest"
                        ${nonFunc.security?.data_encryption?.at_rest ? 'checked' : ''}
                        class="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    />
                    <span class="ml-2 text-sm text-gray-700 dark:text-gray-300">Verschlüsselung at-rest</span>
                </label>

                <label class="flex items-center">
                    <input
                        type="checkbox"
                        name="encryption_in_transit"
                        id="encryption-in-transit"
                        ${nonFunc.security?.data_encryption?.in_transit ? 'checked' : ''}
                        class="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    />
                    <span class="ml-2 text-sm text-gray-700 dark:text-gray-300">Verschlüsselung in-transit</span>
                </label>

                <label class="flex items-center">
                    <input
                        type="checkbox"
                        name="network_isolation"
                        id="network-isolation"
                        ${nonFunc.security?.network_isolation ? 'checked' : ''}
                        class="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    />
                    <span class="ml-2 text-sm text-gray-700 dark:text-gray-300">Private Network (VPC)</span>
                </label>

                <label class="flex items-center">
                    <input
                        type="checkbox"
                        name="public_access"
                        id="public-access"
                        ${nonFunc.security?.public_access ? 'checked' : ''}
                        class="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    />
                    <span class="ml-2 text-sm text-gray-700 dark:text-gray-300">Öffentlicher Zugang erlaubt</span>
                </label>
            </div>

            <!-- Performance & Cost -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="bg-gray-50 dark:bg-gray-900 p-4 rounded-lg space-y-3">
                    <h4 class="font-medium text-gray-900 dark:text-white">Performance</h4>

                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                            Max. Latenz (ms)
                        </label>
                        <input
                            type="number"
                            name="max_latency_ms"
                            id="max-latency"
                            value="${nonFunc.performance?.max_latency_ms || 500}"
                            min="1"
                            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
                        />
                    </div>

                    <label class="flex items-center">
                        <input
                            type="checkbox"
                            name="cdn_required"
                            id="cdn-required"
                            ${nonFunc.performance?.cdn_required ? 'checked' : ''}
                            class="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                        />
                        <span class="ml-2 text-sm text-gray-700 dark:text-gray-300">CDN benötigt</span>
                    </label>
                </div>

                <div class="bg-gray-50 dark:bg-gray-900 p-4 rounded-lg space-y-3">
                    <h4 class="font-medium text-gray-900 dark:text-white">Kosten</h4>

                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                            Monats-Budget (USD)
                        </label>
                        <input
                            type="number"
                            name="monthly_budget_usd"
                            id="monthly-budget"
                            value="${nonFunc.cost?.monthly_budget_usd || 100}"
                            min="0"
                            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
                        />
                    </div>

                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                            Kosten-Optimierung
                        </label>
                        <select
                            name="cost_optimization_priority"
                            id="cost-optimization"
                            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
                        >
                            <option value="low" ${nonFunc.cost?.cost_optimization_priority === 'low' ? 'selected' : ''}>Niedrig</option>
                            <option value="medium" ${nonFunc.cost?.cost_optimization_priority === 'medium' ? 'selected' : ''}>Mittel</option>
                            <option value="high" ${nonFunc.cost?.cost_optimization_priority === 'high' ? 'selected' : ''}>Hoch</option>
                        </select>
                    </div>
                </div>
            </div>
        </div>
    `;
}

/**
 * Rendert Form Actions
 */
function renderFormActions(isEditMode) {
    return `
        <div class="flex justify-end space-x-3 pt-4 border-t border-gray-200 dark:border-gray-700">
            <button
                type="button"
                id="cancel-btn"
                class="px-6 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            >
                Abbrechen
            </button>
            <button
                type="submit"
                id="submit-btn"
                class="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors flex items-center space-x-2"
            >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                </svg>
                <span>${isEditMode ? 'Änderungen speichern' : 'Weiter zum Builder'}</span>
            </button>
        </div>
    `;
}

/**
 * Setup Form Event Handlers
 * @param {HTMLElement} container - Container-Element
 * @param {Function} onSubmit - Submit-Callback
 * @param {Function} onCancel - Cancel-Callback
 */
export function setupFormHandlers(container, onSubmit, onCancel) {
    const form = container.querySelector('#architecture-form');
    const cancelBtn = container.querySelector('#cancel-btn');

    if (form) {
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            const formData = extractFormData(form);
            if (onSubmit) {
                onSubmit(formData);
            }
        });
    }

    if (cancelBtn && onCancel) {
        cancelBtn.addEventListener('click', onCancel);
    }

    // Global Update Region Options Function
    window.StackVertex = window.StackVertex || {};
    window.StackVertex.updateRegionOptions = (provider) => {
        const regionContainer = container.querySelector('#region-selection');
        if (regionContainer) {
            regionContainer.innerHTML = renderRegionSelection(provider, getRegionsForProvider(provider)[0]?.id || '');
        }
    };
}

/**
 * Extrahiere Daten aus dem Formular
 * @param {HTMLFormElement} form - Formular-Element
 * @returns {Object} Extrahierte Daten
 */
function extractFormData(form) {
    const formData = new FormData(form);

    return {
        metadata: {
            name: formData.get('name'),
            description: formData.get('description'),
            provider: formData.get('provider'),
            region: formData.get('region'),
            tags: []
        },
        version: formData.get('version'),
        requirements: {
            functional: {
                workload_type: formData.get('workload_type'),
                expected_traffic: {
                    concurrent_users: parseInt(formData.get('concurrent_users') || 100),
                    requests_per_second: parseInt(formData.get('requests_per_second') || 10),
                    data_transfer_gb_month: parseInt(formData.get('data_transfer_gb_month') || 50)
                },
                storage_needs: {
                    database_size_gb: parseFloat(formData.get('database_size_gb') || 10),
                    file_storage_gb: parseFloat(formData.get('file_storage_gb') || 20),
                    requires_object_storage: formData.get('requires_object_storage') === 'on'
                },
                compute_needs: {
                    cpu_intensive: formData.get('cpu_intensive') === 'on',
                    memory_intensive: formData.get('memory_intensive') === 'on',
                    gpu_required: formData.get('gpu_required') === 'on'
                }
            },
            non_functional: {
                availability: {
                    target_uptime_percent: parseFloat(formData.get('target_uptime_percent') || 99.9),
                    multi_az: formData.get('multi_az') === 'on',
                    disaster_recovery: formData.get('disaster_recovery') === 'on'
                },
                scalability: {
                    auto_scaling: formData.get('auto_scaling') === 'on',
                    scale_to_zero: formData.get('scale_to_zero') === 'on',
                    global_distribution: formData.get('global_distribution') === 'on'
                },
                security: {
                    compliance_requirements: [],
                    data_encryption: {
                        at_rest: formData.get('encryption_at_rest') === 'on',
                        in_transit: formData.get('encryption_in_transit') === 'on'
                    },
                    network_isolation: formData.get('network_isolation') === 'on',
                    public_access: formData.get('public_access') === 'on'
                },
                performance: {
                    max_latency_ms: parseInt(formData.get('max_latency_ms') || 500),
                    cdn_required: formData.get('cdn_required') === 'on'
                },
                cost: {
                    monthly_budget_usd: parseFloat(formData.get('monthly_budget_usd') || 100),
                    cost_optimization_priority: formData.get('cost_optimization_priority')
                }
            }
        }
    };
}

/**
 * Hilfsfunktion zum Escapen von HTML
 */
function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}
