/**
 * OverCloud - Architecture Detail View Page
 *
 * Detailansicht einer einzelnen Architektur
 */

import { getArchitecture, deleteArchitecture } from '../api/architectures.js';
import { findComponentByService } from '../lib/aws-components.js';

/**
 * Rendert die Architecture Detail Page
 * @param {HTMLElement} container - Container-Element
 * @param {string} architectureId - Architecture ID
 */
export async function renderArchitectureDetail(container, architectureId) {
    // Zeige Loading State
    container.innerHTML = renderLoadingState();

    try {
        const architecture = await getArchitecture(architectureId);
        container.innerHTML = renderDetailView(architecture);
        setupDetailHandlers(container, architecture);
    } catch (error) {
        console.error('Fehler beim Laden der Architektur:', error);
        container.innerHTML = renderErrorState(error);
    }
}

/**
 * Rendert Loading State
 */
function renderLoadingState() {
    return `
        <div class="flex items-center justify-center py-12">
            <div class="text-center">
                <div class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
                <p class="text-gray-600 dark:text-gray-400">Lade Architektur...</p>
            </div>
        </div>
    `;
}

/**
 * Rendert Error State
 */
function renderErrorState(error) {
    return `
        <div class="text-center py-12">
            <div class="text-6xl mb-4">⚠️</div>
            <h3 class="text-2xl font-semibold text-gray-900 dark:text-white mb-2">
                Fehler beim Laden
            </h3>
            <p class="text-gray-600 dark:text-gray-400 mb-6">
                ${error.message || 'Die Architektur konnte nicht geladen werden.'}
            </p>
            <button
                onclick="window.location.hash = '#/architectures'"
                class="inline-flex items-center px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors"
            >
                Zurück zur Übersicht
            </button>
        </div>
    `;
}

/**
 * Rendert die Detail View
 */
function renderDetailView(architecture) {
    return `
        <div class="max-w-7xl mx-auto">
            ${renderHeader(architecture)}
            ${renderTabs()}
            <div id="tab-content" class="mt-6">
                ${renderOverviewTab(architecture)}
            </div>
        </div>
    `;
}

/**
 * Rendert Header
 */
function renderHeader(architecture) {
    // WICHTIG: architecture.id ist die DB-ID, architecture.architecture_json.metadata ist das JSON
    const metadata = architecture.architecture_json?.metadata || {};
    const dbId = architecture.id;  // DB-ID für Operationen

    return `
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 mb-6">
            <div class="flex items-start justify-between">
                <div class="flex-1">
                    <div class="flex items-center space-x-3 mb-2">
                        <h1 class="text-3xl font-bold text-gray-900 dark:text-white">
                            ${escapeHtml(architecture.name || 'Unbenannte Architektur')}
                        </h1>
                        <span class="px-3 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 text-sm font-medium rounded-full">
                            ${metadata.provider?.toUpperCase() || 'N/A'}
                        </span>
                        <span class="px-3 py-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 text-sm rounded-full">
                            v${escapeHtml(architecture.version || '1.0.0')}
                        </span>
                    </div>
                    <p class="text-gray-600 dark:text-gray-400 mb-4">
                        ${escapeHtml(architecture.description || 'Keine Beschreibung vorhanden')}
                    </p>
                    <div class="flex items-center space-x-6 text-sm text-gray-500 dark:text-gray-400">
                        <div class="flex items-center">
                            <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                            </svg>
                            <span>Erstellt: ${formatDate(architecture.created_at)}</span>
                        </div>
                        <div class="flex items-center">
                            <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
                            </svg>
                            <span>Aktualisiert: ${formatDate(architecture.updated_at)}</span>
                        </div>
                        ${metadata.region ? `
                            <div class="flex items-center">
                                <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path>
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path>
                                </svg>
                                <span>Region: ${metadata.region}</span>
                            </div>
                        ` : ''}
                    </div>
                </div>
                <div class="flex space-x-2">
                    <button
                        onclick="window.location.hash = '#/architectures/${dbId}/edit'"
                        class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors flex items-center space-x-2"
                    >
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path>
                        </svg>
                        <span>Bearbeiten</span>
                    </button>
                    <button
                        id="delete-btn"
                        class="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors flex items-center space-x-2"
                    >
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                        </svg>
                        <span>Löschen</span>
                    </button>
                    <button
                        onclick="window.location.hash = '#/architectures'"
                        class="px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                    >
                        Zurück
                    </button>
                </div>
            </div>
        </div>
    `;
}

/**
 * Rendert Tab Navigation
 */
function renderTabs() {
    return `
        <div class="border-b border-gray-200 dark:border-gray-700">
            <nav class="flex space-x-8">
                <button
                    data-tab="overview"
                    class="tab-btn border-b-2 border-blue-500 text-blue-600 dark:text-blue-400 pb-4 px-1 font-medium"
                >
                    Übersicht
                </button>
                <button
                    data-tab="components"
                    class="tab-btn border-b-2 border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:border-gray-300 pb-4 px-1 font-medium"
                >
                    Components
                </button>
                <button
                    data-tab="requirements"
                    class="tab-btn border-b-2 border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:border-gray-300 pb-4 px-1 font-medium"
                >
                    Requirements
                </button>
                <button
                    data-tab="json"
                    class="tab-btn border-b-2 border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:border-gray-300 pb-4 px-1 font-medium"
                >
                    JSON
                </button>
            </nav>
        </div>
    `;
}

/**
 * Rendert Overview Tab
 */
function renderOverviewTab(architecture) {
    const archJson = architecture.architecture_json || {};
    const componentCount = archJson.architecture?.components?.length || 0;
    const relationshipCount = archJson.architecture?.relationships?.length || 0;

    return `
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <!-- Stats Cards -->
            <div class="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-sm text-gray-600 dark:text-gray-400">Components</p>
                        <p class="text-3xl font-bold text-gray-900 dark:text-white mt-1">${componentCount}</p>
                    </div>
                    <div class="w-12 h-12 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center">
                        <svg class="w-6 h-6 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path>
                        </svg>
                    </div>
                </div>
            </div>

            <div class="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-sm text-gray-600 dark:text-gray-400">Relationships</p>
                        <p class="text-3xl font-bold text-gray-900 dark:text-white mt-1">${relationshipCount}</p>
                    </div>
                    <div class="w-12 h-12 bg-green-100 dark:bg-green-900 rounded-lg flex items-center justify-center">
                        <svg class="w-6 h-6 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
                        </svg>
                    </div>
                </div>
            </div>

            <div class="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-sm text-gray-600 dark:text-gray-400">Status</p>
                        <p class="text-xl font-bold text-gray-900 dark:text-white mt-1">Draft</p>
                    </div>
                    <div class="w-12 h-12 bg-yellow-100 dark:bg-yellow-900 rounded-lg flex items-center justify-center">
                        <svg class="w-6 h-6 text-yellow-600 dark:text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                        </svg>
                    </div>
                </div>
            </div>
        </div>

        <!-- Architecture Visualization Placeholder -->
        <div class="mt-6 bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-900 rounded-lg p-12 text-center border-2 border-dashed border-gray-300 dark:border-gray-600">
            <div class="text-6xl mb-4">📊</div>
            <h3 class="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                Visualisierung kommt bald
            </h3>
            <p class="text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
                Hier wird ein interaktives Diagramm deiner Cloud-Architektur angezeigt.
                Wechsle zu den anderen Tabs, um Details zu sehen.
            </p>
        </div>
    `;
}

/**
 * Rendert Components Tab
 */
function renderComponentsTab(architecture) {
    const archJson = architecture.architecture_json || {};
    const components = archJson.architecture?.components || [];
    const provider = archJson.metadata?.provider || 'aws';

    if (components.length === 0) {
        return `
            <div class="text-center py-12">
                <div class="text-6xl mb-4">📦</div>
                <p class="text-gray-600 dark:text-gray-400">Keine Components definiert</p>
            </div>
        `;
    }

    return `
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            ${components.map(component => {
                const componentDef = findComponentByService(provider, component.provider_service);
                const icon = componentDef?.icon || '📦';
                const displayName = componentDef?.name || component.provider_service;

                return `
                    <div class="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4 border border-gray-200 dark:border-gray-700">
                        <div class="flex items-start space-x-3">
                            <div class="text-3xl">${icon}</div>
                            <div class="flex-1">
                                <h3 class="font-semibold text-gray-900 dark:text-white">
                                    ${escapeHtml(component.name)}
                                </h3>
                                <p class="text-sm text-gray-600 dark:text-gray-400">
                                    ${displayName}
                                </p>
                                <div class="mt-2 flex items-center space-x-2">
                                    <span class="text-xs px-2 py-0.5 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded">
                                        ${component.type}
                                    </span>
                                    <span class="text-xs px-2 py-0.5 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded font-mono">
                                        ${component.id}
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            }).join('')}
        </div>
    `;
}

/**
 * Rendert Requirements Tab
 */
function renderRequirementsTab(architecture) {
    const archJson = architecture.architecture_json || {};
    const requirements = archJson.requirements || {};
    const functional = requirements.functional || {};
    const nonFunctional = requirements.non_functional || {};

    return `
        <div class="space-y-6">
            <!-- Functional Requirements -->
            <div class="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
                <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                    Funktionale Anforderungen
                </h3>
                <dl class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <dt class="text-sm font-medium text-gray-600 dark:text-gray-400">Workload-Typ</dt>
                        <dd class="mt-1 text-gray-900 dark:text-white">${functional.workload_type || 'N/A'}</dd>
                    </div>
                    <div>
                        <dt class="text-sm font-medium text-gray-600 dark:text-gray-400">Gleichzeitige Nutzer</dt>
                        <dd class="mt-1 text-gray-900 dark:text-white">${functional.expected_traffic?.concurrent_users || 'N/A'}</dd>
                    </div>
                    <div>
                        <dt class="text-sm font-medium text-gray-600 dark:text-gray-400">Requests/Sekunde</dt>
                        <dd class="mt-1 text-gray-900 dark:text-white">${functional.expected_traffic?.requests_per_second || 'N/A'}</dd>
                    </div>
                    <div>
                        <dt class="text-sm font-medium text-gray-600 dark:text-gray-400">Datenbank-Größe</dt>
                        <dd class="mt-1 text-gray-900 dark:text-white">${functional.storage_needs?.database_size_gb || 0} GB</dd>
                    </div>
                </dl>
            </div>

            <!-- Non-Functional Requirements -->
            <div class="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
                <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                    Nicht-funktionale Anforderungen
                </h3>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                        <h4 class="font-medium text-gray-900 dark:text-white mb-2">Verfügbarkeit</h4>
                        <dl class="space-y-2">
                            <div>
                                <dt class="text-sm text-gray-600 dark:text-gray-400">Ziel-Uptime</dt>
                                <dd class="text-gray-900 dark:text-white">${nonFunctional.availability?.target_uptime_percent || 'N/A'}%</dd>
                            </div>
                            <div>
                                <dt class="text-sm text-gray-600 dark:text-gray-400">Multi-AZ</dt>
                                <dd class="text-gray-900 dark:text-white">${nonFunctional.availability?.multi_az ? 'Ja' : 'Nein'}</dd>
                            </div>
                        </dl>
                    </div>
                    <div>
                        <h4 class="font-medium text-gray-900 dark:text-white mb-2">Kosten</h4>
                        <dl class="space-y-2">
                            <div>
                                <dt class="text-sm text-gray-600 dark:text-gray-400">Monats-Budget</dt>
                                <dd class="text-gray-900 dark:text-white">$${nonFunctional.cost?.monthly_budget_usd || 'N/A'}</dd>
                            </div>
                            <div>
                                <dt class="text-sm text-gray-600 dark:text-gray-400">Optimierungspriorität</dt>
                                <dd class="text-gray-900 dark:text-white">${nonFunctional.cost?.cost_optimization_priority || 'N/A'}</dd>
                            </div>
                        </dl>
                    </div>
                </div>
            </div>
        </div>
    `;
}

/**
 * Rendert JSON Tab
 */
function renderJSONTab(architecture) {
    // Zeige das architecture_json (das eigentliche JSON), nicht die DB-Response
    const archJson = architecture.architecture_json || {};

    return `
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            <div class="flex items-center justify-between mb-4">
                <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
                    Complete JSON Schema
                </h3>
                <button
                    id="copy-json-btn"
                    class="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white text-sm rounded-lg transition-colors flex items-center space-x-2"
                >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"></path>
                    </svg>
                    <span>Kopieren</span>
                </button>
            </div>
            <pre class="bg-gray-50 dark:bg-gray-900 rounded-lg p-4 overflow-x-auto"><code class="text-sm font-mono text-gray-900 dark:text-white">${escapeHtml(JSON.stringify(archJson, null, 2))}</code></pre>
        </div>
    `;
}

/**
 * Setup Detail Handlers
 */
function setupDetailHandlers(container, architecture) {
    // Tab Switching
    const tabButtons = container.querySelectorAll('.tab-btn');
    const tabContent = container.querySelector('#tab-content');

    tabButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const tab = btn.dataset.tab;

            // Update active tab
            tabButtons.forEach(b => {
                b.classList.remove('border-blue-500', 'text-blue-600', 'dark:text-blue-400');
                b.classList.add('border-transparent', 'text-gray-500', 'dark:text-gray-400');
            });
            btn.classList.remove('border-transparent', 'text-gray-500', 'dark:text-gray-400');
            btn.classList.add('border-blue-500', 'text-blue-600', 'dark:text-blue-400');

            // Render tab content
            switch (tab) {
                case 'overview':
                    tabContent.innerHTML = renderOverviewTab(architecture);
                    break;
                case 'components':
                    tabContent.innerHTML = renderComponentsTab(architecture);
                    break;
                case 'requirements':
                    tabContent.innerHTML = renderRequirementsTab(architecture);
                    break;
                case 'json':
                    tabContent.innerHTML = renderJSONTab(architecture);
                    setupJSONHandlers(container, architecture);
                    break;
            }
        });
    });

    // Delete Handler
    const deleteBtn = container.querySelector('#delete-btn');
    if (deleteBtn) {
        deleteBtn.addEventListener('click', async () => {
            const confirmed = confirm(
                `Möchtest du die Architektur "${architecture.name}" wirklich löschen?\n\nDiese Aktion kann nicht rückgängig gemacht werden.`
            );

            if (confirmed) {
                try {
                    // Verwende DB-ID (architecture.id), NICHT architecture_json.metadata.id!
                    await deleteArchitecture(architecture.id);
                    alert('Architektur erfolgreich gelöscht');
                    window.location.hash = '#/architectures';
                } catch (error) {
                    console.error('Fehler beim Löschen:', error);
                    alert('Fehler beim Löschen der Architektur: ' + error.message);
                }
            }
        });
    }
}

/**
 * Setup JSON Tab Handlers
 */
function setupJSONHandlers(container, architecture) {
    const copyBtn = container.querySelector('#copy-json-btn');

    if (copyBtn) {
        copyBtn.addEventListener('click', () => {
            const json = JSON.stringify(architecture.architecture_json || {}, null, 2);
            navigator.clipboard.writeText(json).then(() => {
                copyBtn.innerHTML = `
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                    </svg>
                    <span>Kopiert!</span>
                `;
                setTimeout(() => {
                    copyBtn.innerHTML = `
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"></path>
                        </svg>
                        <span>Kopieren</span>
                    `;
                }, 2000);
            });
        });
    }
}

/**
 * Formatiere Datum
 */
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('de-DE', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * Escape HTML
 */
function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}
