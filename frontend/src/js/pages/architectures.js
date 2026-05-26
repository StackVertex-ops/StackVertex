/**
 * StackVertex - Architectures Page
 *
 * Hauptseite für die Darstellung und Verwaltung von Architekturen
 */

import { renderArchitectureList } from '../components/architecture-list.js';

/**
 * Rendert die Architectures Page
 * @param {HTMLElement} container - Container-Element für die Page
 */
export async function renderArchitecturesPage(container) {
    // Page Layout erstellen
    container.innerHTML = `
        <div class="max-w-7xl mx-auto">
            <div id="architectures-content"></div>
        </div>
    `;

    // Architecture List Component in Content-Bereich rendern
    const contentContainer = container.querySelector('#architectures-content');
    await renderArchitectureList(contentContainer);
}
