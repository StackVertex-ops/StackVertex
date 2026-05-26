/**
 * StackVertex - Component Palette
 *
 * Sidebar mit allen verfügbaren AWS-Components zum Hinzufügen zur Canvas
 */

import { AWS_COMPONENTS, getCategoriesForProvider, getComponentsByCategory } from '../lib/aws-components.js';

/**
 * Rendert die Component Palette
 * @param {HTMLElement} container - Container-Element
 * @param {string} provider - Cloud Provider (aws, azure, gcp)
 * @param {Function} onComponentSelect - Callback wenn Component ausgewählt wird
 */
export function renderComponentPalette(container, provider = 'aws', onComponentSelect) {
    const categories = getCategoriesForProvider(provider);

    container.innerHTML = `
        <div class="flex flex-col h-full">
            <!-- Header -->
            <div class="p-4 border-b border-gray-200 dark:border-gray-700">
                <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                    Components
                </h2>
                <input
                    type="text"
                    id="component-search"
                    placeholder="Suche Components..."
                    class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
            </div>

            <!-- Templates -->
            <div class="p-4 border-b border-gray-200 dark:border-gray-700">
                <h3 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Quick Start Templates
                </h3>
                <div class="space-y-2">
                    <button
                        class="template-btn w-full text-left px-3 py-2 bg-blue-50 dark:bg-blue-900/20 text-blue-900 dark:text-blue-100 rounded-lg hover:bg-blue-100 dark:hover:bg-blue-900/40 transition-colors text-sm"
                        data-template="web-app"
                    >
                        <div class="font-medium">Web Application</div>
                        <div class="text-xs text-blue-700 dark:text-blue-300">VPC + ALB + EC2 + RDS + S3</div>
                    </button>
                    <button
                        class="template-btn w-full text-left px-3 py-2 bg-purple-50 dark:bg-purple-900/20 text-purple-900 dark:text-purple-100 rounded-lg hover:bg-purple-100 dark:hover:bg-purple-900/40 transition-colors text-sm"
                        data-template="serverless"
                    >
                        <div class="font-medium">Serverless API</div>
                        <div class="text-xs text-purple-700 dark:text-purple-300">API Gateway + Lambda + DynamoDB</div>
                    </button>
                    <button
                        class="template-btn w-full text-left px-3 py-2 bg-green-50 dark:bg-green-900/20 text-green-900 dark:text-green-100 rounded-lg hover:bg-green-100 dark:hover:bg-green-900/40 transition-colors text-sm"
                        data-template="static-site"
                    >
                        <div class="font-medium">Static Website</div>
                        <div class="text-xs text-green-700 dark:text-green-300">S3 + CloudFront + Route53</div>
                    </button>
                </div>
            </div>

            <!-- Categories -->
            <div class="flex-1 overflow-y-auto p-4">
                ${categories.map(category => renderCategory(provider, category)).join('')}
            </div>
        </div>
    `;

    // Setup Event Handlers
    setupPaletteHandlers(container, provider, onComponentSelect);
}

/**
 * Rendert eine Kategorie mit ihren Components
 */
function renderCategory(provider, category) {
    const components = getComponentsByCategory(provider, category);
    const componentEntries = Object.entries(components);

    if (componentEntries.length === 0) {
        return '';
    }

    return `
        <div class="mb-4 component-category" data-category="${category}">
            <button class="category-toggle w-full flex items-center justify-between text-left text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 hover:text-gray-900 dark:hover:text-white">
                <span class="capitalize">${category}</span>
                <svg class="w-4 h-4 transform transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
                </svg>
            </button>
            <div class="category-items space-y-1">
                ${componentEntries.map(([key, component]) => renderComponentItem(key, component)).join('')}
            </div>
        </div>
    `;
}

/**
 * Rendert ein einzelnes Component Item
 */
function renderComponentItem(key, component) {
    return `
        <button
            class="component-item w-full flex items-center space-x-2 px-3 py-2 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors group"
            data-component-key="${key}"
            data-component-service="${component.provider_service}"
            draggable="true"
        >
            <span class="text-2xl">${component.icon}</span>
            <div class="flex-1 text-left">
                <div class="text-sm font-medium text-gray-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400">
                    ${component.name}
                </div>
                <div class="text-xs text-gray-500 dark:text-gray-400">
                    ${component.description}
                </div>
            </div>
            <svg class="w-4 h-4 text-gray-400 group-hover:text-blue-600 dark:group-hover:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
            </svg>
        </button>
    `;
}

/**
 * Setup Event Handlers für die Palette
 */
function setupPaletteHandlers(container, provider, onComponentSelect) {
    // Search Handler
    const searchInput = container.querySelector('#component-search');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            filterComponents(container, e.target.value);
        });
    }

    // Category Toggle Handler
    const categoryToggles = container.querySelectorAll('.category-toggle');
    categoryToggles.forEach(toggle => {
        toggle.addEventListener('click', () => {
            const category = toggle.closest('.component-category');
            const items = category.querySelector('.category-items');
            const icon = toggle.querySelector('svg');

            items.classList.toggle('hidden');
            icon.classList.toggle('rotate-180');
        });
    });

    // Template Buttons
    const templateButtons = container.querySelectorAll('.template-btn');
    templateButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const template = btn.dataset.template;
            if (onComponentSelect) {
                onComponentSelect({ type: 'template', templateId: template });
            }
        });
    });

    // Component Item Click Handler
    const componentItems = container.querySelectorAll('.component-item');
    componentItems.forEach(item => {
        item.addEventListener('click', () => {
            const componentKey = item.dataset.componentKey;
            const componentService = item.dataset.componentService;

            if (onComponentSelect) {
                onComponentSelect({
                    type: 'component',
                    key: componentKey,
                    service: componentService
                });
            }
        });

        // Drag & Drop Support
        item.addEventListener('dragstart', (e) => {
            const componentKey = item.dataset.componentKey;
            const componentService = item.dataset.componentService;

            e.dataTransfer.effectAllowed = 'copy';
            e.dataTransfer.setData('application/json', JSON.stringify({
                type: 'component',
                key: componentKey,
                service: componentService
            }));

            // Visual Feedback
            item.classList.add('opacity-50');
        });

        item.addEventListener('dragend', (e) => {
            item.classList.remove('opacity-50');
        });
    });
}

/**
 * Filtere Components basierend auf Suchbegriff
 */
function filterComponents(container, searchTerm) {
    const term = searchTerm.toLowerCase().trim();
    const categories = container.querySelectorAll('.component-category');

    categories.forEach(category => {
        const items = category.querySelectorAll('.component-item');
        let hasVisibleItems = false;

        items.forEach(item => {
            const name = item.querySelector('.text-sm').textContent.toLowerCase();
            const description = item.querySelector('.text-xs').textContent.toLowerCase();

            if (term === '' || name.includes(term) || description.includes(term)) {
                item.classList.remove('hidden');
                hasVisibleItems = true;
            } else {
                item.classList.add('hidden');
            }
        });

        // Hide category if no visible items
        if (term === '') {
            category.classList.remove('hidden');
        } else if (hasVisibleItems) {
            category.classList.remove('hidden');
            // Expand category
            const items = category.querySelector('.category-items');
            const icon = category.querySelector('.category-toggle svg');
            items.classList.remove('hidden');
            icon.classList.add('rotate-180');
        } else {
            category.classList.add('hidden');
        }
    });
}
