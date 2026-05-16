/**
 * OverCloud - Architecture Builder Entry Point
 *
 * Entry Point für die dedizierte Architecture Builder Page
 */

import '../css/main.css';
import '../css/architecture-builder.css';
import { renderArchitectureBuilderCanvas } from './pages/architecture-builder-canvas.js';

/**
 * Initialize Architecture Builder
 */
async function init() {
    // Get architecture ID from URL query params (if edit mode)
    const params = new URLSearchParams(window.location.search);
    const architectureId = params.get('id');

    // Get app container
    const appContainer = document.getElementById('app');

    if (!appContainer) {
        console.error('App container not found');
        return;
    }

    // Render Architecture Builder Canvas
    await renderArchitectureBuilderCanvas(appContainer, architectureId);
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
