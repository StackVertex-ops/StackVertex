/**
 * Blueprints Page
 * Zeigt alle verfügbaren Infrastructure Blueprints
 */

// SECURITY FIX: No hardcoded URL
const API_BASE_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000') + '/api/v1';

let allBlueprints = [];
let currentFilters = {
    category: '',
    difficulty: '',
    maxCost: null,
    search: ''
};

// ============================================================================
// API Calls
// ============================================================================

async function fetchBlueprints() {
    try {
        const params = new URLSearchParams();

        if (currentFilters.category) params.append('category', currentFilters.category);
        if (currentFilters.difficulty) params.append('difficulty', currentFilters.difficulty);
        if (currentFilters.maxCost) params.append('max_cost_usd', currentFilters.maxCost);
        if (currentFilters.search) params.append('search', currentFilters.search);

        const url = `${API_BASE_URL}/blueprints?${params.toString()}`;
        const response = await fetch(url);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        return data.blueprints || [];
    } catch (error) {
        console.error('Fehler beim Laden der Blueprints:', error);
        throw error;
    }
}

// ============================================================================
// UI Rendering
// ============================================================================

function getDifficultyBadge(difficulty) {
    const badges = {
        beginner: { label: 'Beginner', class: 'bg-green-100 text-green-700' },
        intermediate: { label: 'Intermediate', class: 'bg-yellow-100 text-yellow-700' },
        advanced: { label: 'Advanced', class: 'bg-red-100 text-red-700' }
    };

    const badge = badges[difficulty] || badges.beginner;
    return `<span class="px-2 py-1 rounded-full text-xs font-medium ${badge.class}">${badge.label}</span>`;
}

function getCategoryIcon(category) {
    const icons = {
        static: '📄',
        webapp: '🌐',
        api: '🔌',
        database: '💾'
    };

    return icons[category] || '📦';
}

function renderBlueprintCard(blueprint) {
    const { metadata, form_schema } = blueprint;
    const costRange = metadata.estimated_cost;

    return `
        <div class="bg-white rounded-lg shadow-md hover:shadow-xl transition-shadow duration-300 overflow-hidden cursor-pointer"
             onclick="window.location.href='/blueprint-architecture-builder.html?blueprint=${metadata.id}'">
            <!-- Header mit Icon -->
            <div class="p-6 bg-gradient-to-br from-purple-50 to-indigo-50">
                <div class="flex items-start justify-between mb-3">
                    <div class="text-4xl">${getCategoryIcon(metadata.category)}</div>
                    ${getDifficultyBadge(metadata.difficulty)}
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
                <!-- Cost Estimate -->
                <div class="mb-4 p-3 bg-gray-50 rounded-lg">
                    <div class="text-xs text-gray-600 mb-1">Geschätzte monatliche Kosten</div>
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
                    <span>Setup: ~${metadata.setup_time_minutes} Minuten</span>
                </div>

                <!-- Use Cases (max 3) -->
                <div class="mb-4">
                    <div class="text-xs font-medium text-gray-700 mb-2">Geeignet für:</div>
                    <ul class="space-y-1">
                        ${metadata.use_cases.slice(0, 3).map(useCase => `
                            <li class="text-sm text-gray-600 flex items-start gap-2">
                                <svg class="w-4 h-4 text-green-500 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
                                </svg>
                                <span>${useCase}</span>
                            </li>
                        `).join('')}
                        ${metadata.use_cases.length > 3 ? `
                            <li class="text-sm text-gray-500">
                                +${metadata.use_cases.length - 3} weitere...
                            </li>
                        ` : ''}
                    </ul>
                </div>

                <!-- CTA Button -->
                <button class="w-full px-4 py-2 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 transition">
                    Blueprint verwenden
                </button>
            </div>
        </div>
    `;
}

function renderBlueprints(blueprints) {
    const grid = document.getElementById('blueprintsGrid');
    const emptyState = document.getElementById('emptyState');
    const errorState = document.getElementById('errorState');

    // Verstecke Error State
    errorState.classList.add('hidden');

    if (blueprints.length === 0) {
        grid.classList.add('hidden');
        emptyState.classList.remove('hidden');
        return;
    }

    grid.classList.remove('hidden');
    emptyState.classList.add('hidden');

    grid.innerHTML = blueprints.map(bp => renderBlueprintCard(bp)).join('');
}

function showLoading() {
    document.getElementById('loadingState').classList.remove('hidden');
    document.getElementById('blueprintsGrid').classList.add('hidden');
    document.getElementById('errorState').classList.add('hidden');
    document.getElementById('emptyState').classList.add('hidden');
}

function hideLoading() {
    document.getElementById('loadingState').classList.add('hidden');
}

function showError(message) {
    document.getElementById('errorState').classList.remove('hidden');
    document.getElementById('errorMessage').textContent = message;
    document.getElementById('blueprintsGrid').classList.add('hidden');
    document.getElementById('emptyState').classList.add('hidden');
    hideLoading();
}

// ============================================================================
// Filter Handling
// ============================================================================

function applyFilters() {
    showLoading();

    fetchBlueprints()
        .then(blueprints => {
            allBlueprints = blueprints;
            renderBlueprints(blueprints);
            hideLoading();
        })
        .catch(error => {
            showError(`Fehler beim Laden der Blueprints: ${error.message}`);
        });
}

function setupFilters() {
    const categoryFilter = document.getElementById('categoryFilter');
    const difficultyFilter = document.getElementById('difficultyFilter');
    const costFilter = document.getElementById('costFilter');
    const searchInput = document.getElementById('searchInput');

    categoryFilter.addEventListener('change', (e) => {
        currentFilters.category = e.target.value;
        applyFilters();
    });

    difficultyFilter.addEventListener('change', (e) => {
        currentFilters.difficulty = e.target.value;
        applyFilters();
    });

    costFilter.addEventListener('change', (e) => {
        currentFilters.maxCost = e.target.value ? parseFloat(e.target.value) : null;
        applyFilters();
    });

    // Debounced search
    let searchTimeout;
    searchInput.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            currentFilters.search = e.target.value;
            applyFilters();
        }, 300);
    });
}

// ============================================================================
// Init
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    setupFilters();
    applyFilters();
});
