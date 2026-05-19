/**
 * OverCloud Frontend - Main Entry Point
 *
 * Vanilla JavaScript application using ES6+ modules and Vite.
 */

import '../css/main.css';
import { APIClient } from './lib/api-client.js';
import { renderArchitecturesPage } from './pages/architectures.js';
import { renderArchitectureBuilder } from './pages/architecture-builder.js';
import { renderArchitectureDetail } from './pages/architecture-detail.js';

// Import FeedbackWidget (auto-initializes on non-admin pages)
import './components/FeedbackWidget.js';

// Initialize API client - SECURITY FIX: No hardcoded URL
// APIClient now uses import.meta.env.VITE_API_URL
const api = new APIClient();

/**
 * Initialize application
 */
async function init() {
    // Check API connection
    await checkAPIStatus();

    // Setup routing
    setupRouter();

    // Setup event listeners
    setupEventListeners();

    // Handle initial route
    handleRoute();
}

/**
 * Check API health status
 */
async function checkAPIStatus() {
    const statusElement = document.getElementById('api-status');

    if (!statusElement) {
        return; // Element existiert nicht auf allen Seiten
    }

    try {
        const response = await api.get('/health');

        if (response.status === 'healthy') {
            statusElement.textContent = `✓ API Connected (v${response.version})`;
            statusElement.classList.add('text-green-600', 'dark:text-green-400');
        }
    } catch (error) {
        console.error('API connection failed:', error);
        statusElement.textContent = '✗ API Offline - Make sure backend is running';
        statusElement.classList.add('text-red-600', 'dark:text-red-400');
    }
}

/**
 * Setup hash-based routing
 */
function setupRouter() {
    // Reagiere auf Hash-Änderungen
    window.addEventListener('hashchange', handleRoute);
}

/**
 * Handle route changes
 */
async function handleRoute() {
    const hash = window.location.hash || '#/';
    const mainContainer = document.querySelector('main');

    // Route matching with parameter extraction
    if (hash === '#/' || hash === '') {
        // Dashboard / Home
        renderHomePage(mainContainer);
    } else if (hash === '#/architectures') {
        // Architectures List
        await renderArchitecturesPage(mainContainer);
    } else if (hash === '#/architectures/new') {
        // Create New Architecture
        await renderArchitectureBuilder(mainContainer);
    } else if (hash.match(/^#\/architectures\/[^/]+\/edit$/)) {
        // Edit Architecture
        const architectureId = hash.split('/')[2];
        await renderArchitectureBuilder(mainContainer, architectureId);
    } else if (hash.match(/^#\/architectures\/[^/]+$/)) {
        // Architecture Detail View
        const architectureId = hash.split('/')[2];
        await renderArchitectureDetail(mainContainer, architectureId);
    } else if (hash === '#/deployments') {
        // Deployments (Platzhalter)
        mainContainer.innerHTML = '<p class="text-center text-gray-600 dark:text-gray-400">Deployments kommen bald...</p>';
    } else {
        // 404
        mainContainer.innerHTML = '<p class="text-center text-gray-600 dark:text-gray-400">Seite nicht gefunden</p>';
    }
}

/**
 * Rendert die Home Page (ursprünglicher Content)
 * @param {HTMLElement} container - Container-Element
 */
function renderHomePage(container) {
    container.innerHTML = `
        <div class="text-center">
            <h2 class="text-4xl font-bold text-gray-900 dark:text-white mb-4">
                Welcome to OverCloud
            </h2>
            <p class="text-xl text-gray-600 dark:text-gray-400 mb-8">
                Cloud infrastructure made understandable, versionable, and deployable.
            </p>

            <!-- Status Card -->
            <div class="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 max-w-md mx-auto">
                <div class="flex items-center justify-center space-x-2 mb-4">
                    <div class="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                    <span class="text-gray-700 dark:text-gray-300">System Status</span>
                </div>
                <p class="text-sm text-gray-500 dark:text-gray-400" id="api-status">
                    Connecting to API...
                </p>
            </div>

            <!-- Feature Cards -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12">
                <div class="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
                    <div class="text-3xl mb-4">📋</div>
                    <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                        Requirements-Driven
                    </h3>
                    <p class="text-gray-600 dark:text-gray-400">
                        Describe what you need, not how to build it
                    </p>
                </div>

                <div class="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
                    <div class="text-3xl mb-4">📄</div>
                    <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                        JSON-First
                    </h3>
                    <p class="text-gray-600 dark:text-gray-400">
                        Versionable, inspectable source of truth
                    </p>
                </div>

                <div class="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
                    <div class="text-3xl mb-4">🔍</div>
                    <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                        Transparent
                    </h3>
                    <p class="text-gray-600 dark:text-gray-400">
                        See cost, security, and impact before deploying
                    </p>
                </div>
            </div>
        </div>
    `;

    // API Status nach Rendering prüfen
    checkAPIStatus();
}

/**
 * Setup global event listeners
 */
function setupEventListeners() {
    // Add your event listeners here
}

// Initialize app when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

// Export for debugging
window.OverCloud = {
    api,
};
