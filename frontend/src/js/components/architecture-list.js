/**
 * StackVertex - Architecture List Component
 *
 * Komponente zur Darstellung einer Liste von Architekturen
 */

import { listArchitectures, deleteArchitecture } from '../api/architectures.js';

/**
 * Rendert die Architecture List Komponente
 * @param {HTMLElement} container - Container-Element für die Komponente
 */
export async function renderArchitectureList(container) {
    // Zeige Loading State
    container.innerHTML = renderLoadingState();

    try {
        // Lade Architekturen vom Backend
        const response = await listArchitectures();
        const architectures = response.items || [];

        // Zeige passenden Content basierend auf Daten
        if (architectures.length === 0) {
            container.innerHTML = renderEmptyState();
        } else {
            container.innerHTML = renderArchitectures(architectures);
        }

        // Event Listeners für Delete-Buttons
        setupDeleteHandlers(container);
    } catch (error) {
        console.error('Fehler beim Laden der Architekturen:', error);
        container.innerHTML = renderErrorState(error);
    }
}

/**
 * Rendert den Loading State (Skeleton Loader)
 * @returns {string} HTML für Loading State
 */
function renderLoadingState() {
    return `
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            ${Array(6).fill(0).map(() => `
                <div class="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 animate-pulse">
                    <div class="h-6 bg-gray-300 dark:bg-gray-700 rounded w-3/4 mb-4"></div>
                    <div class="h-4 bg-gray-300 dark:bg-gray-700 rounded w-full mb-2"></div>
                    <div class="h-4 bg-gray-300 dark:bg-gray-700 rounded w-5/6 mb-4"></div>
                    <div class="h-3 bg-gray-300 dark:bg-gray-700 rounded w-1/2"></div>
                </div>
            `).join('')}
        </div>
    `;
}

/**
 * Rendert den Empty State (keine Architekturen vorhanden)
 * @returns {string} HTML für Empty State
 */
function renderEmptyState() {
    return `
        <div class="text-center py-12">
            <div class="text-6xl mb-4">📋</div>
            <h3 class="text-2xl font-semibold text-gray-900 dark:text-white mb-2">
                Noch keine Architekturen
            </h3>
            <p class="text-gray-600 dark:text-gray-400 mb-6">
                Erstelle deine erste Cloud-Architektur und starte durch.
            </p>
            <button
                onclick="window.location.hash = '#/architectures/new'"
                class="inline-flex items-center px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors"
            >
                <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
                </svg>
                Neue Architektur erstellen
            </button>
        </div>
    `;
}

/**
 * Rendert den Error State
 * @param {Error} error - Fehler-Objekt
 * @returns {string} HTML für Error State
 */
function renderErrorState(error) {
    // SECURITY FIX: Escape error message to prevent XSS
    const safeErrorMessage = escapeHtml(error.message || 'Die Architekturen konnten nicht geladen werden.');

    return `
        <div class="text-center py-12">
            <div class="text-6xl mb-4">⚠️</div>
            <h3 class="text-2xl font-semibold text-gray-900 dark:text-white mb-2">
                Fehler beim Laden
            </h3>
            <p class="text-gray-600 dark:text-gray-400 mb-6">
                ${safeErrorMessage}
            </p>
            <button
                onclick="window.location.reload()"
                class="inline-flex items-center px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors"
            >
                Erneut versuchen
            </button>
        </div>
    `;
}

/**
 * Rendert die Liste der Architekturen als Cards
 * @param {Array} architectures - Array von Architecture-Objekten
 * @returns {string} HTML für Architecture Cards
 */
function renderArchitectures(architectures) {
    return `
        <div class="mb-6 flex justify-between items-center">
            <h2 class="text-2xl font-bold text-gray-900 dark:text-white">
                Meine Architekturen (${architectures.length})
            </h2>
            <button
                onclick="window.location.hash = '#/architectures/new'"
                class="inline-flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors"
            >
                <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
                </svg>
                Neue Architektur
            </button>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            ${architectures.map(arch => renderArchitectureCard(arch)).join('')}
        </div>
    `;
}

/**
 * Rendert eine einzelne Architecture Card
 * @param {Object} arch - Architecture-Objekt
 * @returns {string} HTML für Card
 */
function renderArchitectureCard(arch) {
    const createdDate = new Date(arch.created_at).toLocaleDateString('de-DE', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });

    return `
        <div
            class="bg-white dark:bg-gray-800 rounded-lg shadow-md hover:shadow-lg transition-shadow border border-gray-200 dark:border-gray-700 overflow-hidden"
        >
            <div
                class="p-6 cursor-pointer"
                onclick="window.location.hash = '#/architectures/${arch.id}'"
            >
                <h3 class="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                    ${escapeHtml(arch.name)}
                </h3>
                <p class="text-gray-600 dark:text-gray-400 mb-4 line-clamp-2">
                    ${escapeHtml(arch.description || 'Keine Beschreibung')}
                </p>
                <div class="flex items-center justify-between text-sm">
                    <span class="text-gray-500 dark:text-gray-500">
                        Version: ${escapeHtml(arch.version || '1.0.0')}
                    </span>
                    <span class="text-gray-500 dark:text-gray-500">
                        ${createdDate}
                    </span>
                </div>
            </div>

            <div class="px-6 py-3 bg-gray-50 dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700 flex justify-end space-x-2">
                <button
                    onclick="event.stopPropagation(); window.location.hash = '#/architectures/${arch.id}'"
                    class="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 font-medium"
                >
                    Bearbeiten
                </button>
                <button
                    data-architecture-id="${arch.id}"
                    data-architecture-name="${escapeHtml(arch.name)}"
                    class="delete-architecture text-sm text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-300 font-medium"
                >
                    Löschen
                </button>
            </div>
        </div>
    `;
}

/**
 * Setup Event Handlers für Delete-Buttons
 * @param {HTMLElement} container - Container-Element
 */
function setupDeleteHandlers(container) {
    const deleteButtons = container.querySelectorAll('.delete-architecture');

    deleteButtons.forEach(button => {
        button.addEventListener('click', async (event) => {
            event.stopPropagation();

            const architectureId = button.dataset.architectureId;
            const architectureName = button.dataset.architectureName;

            // Bestätigung durch nativen Browser Dialog
            const confirmed = confirm(
                `Möchtest du die Architektur "${architectureName}" wirklich löschen?\n\nDiese Aktion kann nicht rückgängig gemacht werden.`
            );

            if (!confirmed) {
                return;
            }

            try {
                // Löschen durchführen
                await deleteArchitecture(architectureId);

                // Liste neu laden
                await renderArchitectureList(container);
            } catch (error) {
                console.error('Fehler beim Löschen der Architektur:', error);
                alert('Fehler beim Löschen der Architektur. Bitte versuche es erneut.');
            }
        });
    });
}

/**
 * Hilfsfunktion zum Escapen von HTML (XSS-Schutz)
 * @param {string} str - Zu escapender String
 * @returns {string} Escapeter String
 */
function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}
