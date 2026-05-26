/**
 * StackVertex - Architecture Builder Canvas Page
 *
 * Haupt-Controller für den visuellen Architecture Builder
 */

import { renderComponentPalette } from '../components/component-palette.js';
import { ArchitectureCanvas } from '../components/architecture-canvas.js';
import { renderPropertiesPanel } from '../components/properties-panel.js';
import { renderAIAdvisor } from '../components/ai-advisor.js';
import { validateArchitecture } from '../lib/architecture-validator.js';
import { createArchitecture, updateArchitecture, getArchitecture } from '../api/architectures.js';
import { EXAMPLE_SIMPLE_WEB_APP, EXAMPLE_SERVERLESS_API } from '../lib/example-architectures.js';

/**
 * Rendert die Architecture Builder Canvas Page
 * @param {HTMLElement} appContainer - Haupt-App-Container
 * @param {string} architectureId - Optional: ID für Edit-Modus
 */
export async function renderArchitectureBuilderCanvas(appContainer, architectureId = null) {
    const isEditMode = !!architectureId;

    // State
    let currentArchitecture = null;
    let canvas = null;
    let selectedComponent = null;

    try {
        // Load existing architecture if in edit mode
        if (isEditMode) {
            currentArchitecture = await getArchitecture(architectureId);
        } else {
            // Initialize new architecture
            currentArchitecture = {
                metadata: {
                    name: 'Untitled Architecture',
                    description: '',
                    provider: 'aws',
                    region: 'eu-central-1'
                },
                version: '1.0.0',
                requirements: {},
                architecture: {
                    components: [],
                    relationships: []
                }
            };
        }

        // Get containers
        const paletteContainer = document.getElementById('component-palette');
        const canvasContainer = document.getElementById('canvas-container');
        const propertiesContainer = document.getElementById('properties-panel');
        const advisorContainer = document.getElementById('ai-advisor-bar');

        // Render Component Palette
        renderComponentPalette(paletteContainer, 'aws', handleComponentSelection);

        // Initialize Canvas
        canvas = new ArchitectureCanvas(canvasContainer, {
            provider: 'aws',
            onComponentAdd: handleComponentAdd,
            onComponentSelect: handleComponentSelect,
            onComponentRemove: handleComponentRemove
        });

        // Load existing architecture into canvas
        if (currentArchitecture.architecture_json) {
            canvas.loadArchitecture(currentArchitecture.architecture_json);
        } else if (currentArchitecture.architecture) {
            canvas.loadArchitecture(currentArchitecture);
        }

        // Render Properties Panel (initially empty)
        renderPropertiesPanel(propertiesContainer, null);

        // Render AI Advisor (initially collapsed)
        renderAIAdvisor(advisorContainer, currentArchitecture, true);

        // Setup Global Event Handlers
        setupGlobalHandlers(canvas, currentArchitecture, architectureId);

        // Update status and advisor
        updateStatus();
        updateAIAdvisor();

    } catch (error) {
        console.error('Fehler beim Laden der Architecture Builder Canvas:', error);
        appContainer.innerHTML = `
            <div class="flex items-center justify-center h-screen">
                <div class="text-center">
                    <div class="text-6xl mb-4">⚠️</div>
                    <h3 class="text-2xl font-semibold text-gray-900 dark:text-white mb-2">
                        Fehler beim Laden
                    </h3>
                    <p class="text-gray-600 dark:text-gray-400 mb-6">
                        ${error.message}
                    </p>
                    <button
                        onclick="window.location.hash = '#/architectures'"
                        class="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                    >
                        Zurück zur Übersicht
                    </button>
                </div>
            </div>
        `;
    }

    /**
     * Handle Component Selection from Palette
     */
    function handleComponentSelection(selection) {
        if (selection.type === 'template') {
            loadTemplate(selection.templateId);
        } else if (selection.type === 'component') {
            // Components werden via Drag & Drop zur Canvas hinzugefügt
            // Hier könnten wir einen Hint anzeigen
            updateStatus('Ziehe die Component auf die Canvas');
        }
    }

    /**
     * Handle Component Add to Canvas
     */
    function handleComponentAdd(component) {
        updateStatus(`Component hinzugefügt: ${component.name}`);
        updateComponentCount();
    }

    /**
     * Handle Component Select on Canvas
     */
    function handleComponentSelect(component) {
        selectedComponent = component;
        const propertiesContainer = document.getElementById('properties-panel');
        renderPropertiesPanel(propertiesContainer, component, handlePropertyChange);
        updateStatus(component ? `Ausgewählt: ${component.name}` : 'Ready');
    }

    /**
     * Handle Component Remove
     */
    function handleComponentRemove(componentId) {
        updateStatus('Component entfernt');
        updateComponentCount();
    }

    /**
     * Handle Property Change
     */
    function handlePropertyChange(componentId, updatedProperties) {
        const component = canvas.components.get(componentId);
        if (component) {
            component.name = updatedProperties.name;
            component.configuration = updatedProperties.configuration;
            canvas.renderComponents();
            updateStatus('Properties aktualisiert');
            updateAIAdvisor(); // Refresh advisor after property changes
        }
    }

    /**
     * Load Template
     */
    function loadTemplate(templateId) {
        let template;

        switch (templateId) {
            case 'web-app':
                template = EXAMPLE_SIMPLE_WEB_APP;
                break;
            case 'serverless':
                template = EXAMPLE_SERVERLESS_API;
                break;
            case 'static-site':
                // TODO: Create static site template
                alert('Static Site Template kommt bald!');
                return;
            default:
                alert('Template nicht gefunden');
                return;
        }

        canvas.loadArchitecture(template);
        updateStatus(`Template geladen: ${template.metadata.name}`);
        updateComponentCount();
        updateAIAdvisor(); // Refresh advisor after template load
    }

    /**
     * Setup Global Event Handlers
     */
    function setupGlobalHandlers(canvas, architecture, architectureId) {
        // Validate Button
        const validateBtn = document.getElementById('validate-btn');
        if (validateBtn) {
            validateBtn.addEventListener('click', () => {
                validateCurrentArchitecture(canvas, architecture);
            });
        }

        // Export JSON Button
        const exportBtn = document.getElementById('export-json-btn');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => {
                exportJSON(canvas, architecture);
            });
        }

        // Save Button
        const saveBtn = document.getElementById('save-btn');
        if (saveBtn) {
            saveBtn.addEventListener('click', async () => {
                await saveArchitecture(canvas, architecture, architectureId);
            });
        }

        // Toggle JSON View Button
        const toggleJsonBtn = document.getElementById('toggle-json-view');
        if (toggleJsonBtn) {
            toggleJsonBtn.addEventListener('click', () => {
                showJSONModal(canvas, architecture);
            });
        }

        // Toggle AI Advisor Button
        const toggleAdvisorBtn = document.getElementById('toggle-advisor');
        if (toggleAdvisorBtn) {
            toggleAdvisorBtn.addEventListener('click', () => {
                const advisorBar = document.getElementById('ai-advisor-bar');
                const content = advisorBar?.querySelector('#advisor-content');
                if (content) {
                    content.classList.toggle('hidden');
                    updateAIAdvisor(); // Refresh recommendations
                }
            });
        }
    }

    /**
     * Validate Current Architecture
     */
    function validateCurrentArchitecture(canvas, architecture) {
        const canvasData = canvas.exportArchitecture();
        const fullArchitecture = {
            ...architecture,
            architecture: canvasData
        };

        const result = validateArchitecture(fullArchitecture);

        const validationStatus = document.getElementById('validation-status');

        if (result.valid && result.warnings.length === 0) {
            validationStatus.innerHTML = '<span class="text-green-600">✓ Gültig</span>';
            updateStatus('Validierung erfolgreich');
        } else if (result.valid && result.warnings.length > 0) {
            validationStatus.innerHTML = `<span class="text-yellow-600">⚠ ${result.warnings.length} Warnungen</span>`;
            updateStatus(`Validierung: ${result.warnings.length} Warnungen`);
            console.warn('Validation warnings:', result.warnings);
        } else {
            validationStatus.innerHTML = `<span class="text-red-600">✗ ${result.errors.length} Fehler</span>`;
            updateStatus(`Validierung fehlgeschlagen: ${result.errors.length} Fehler`);
            alert('Validierungs-Fehler:\n' + result.errors.join('\n'));
        }
    }

    /**
     * Export JSON
     */
    function exportJSON(canvas, architecture) {
        const canvasData = canvas.exportArchitecture();
        const fullArchitecture = {
            ...architecture,
            metadata: {
                ...architecture.metadata,
                updated_at: new Date().toISOString()
            },
            architecture: canvasData
        };

        const jsonString = JSON.stringify(fullArchitecture, null, 2);
        const blob = new Blob([jsonString], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${architecture.metadata.name || 'architecture'}.json`;
        a.click();
        URL.revokeObjectURL(url);

        updateStatus('JSON exportiert');
    }

    /**
     * Save Architecture
     */
    async function saveArchitecture(canvas, architecture, architectureId) {
        const saveBtn = document.getElementById('save-btn');

        try {
            // Disable button
            saveBtn.disabled = true;
            saveBtn.innerHTML = '<span class="animate-spin">⏳</span> Speichert...';

            // Get canvas data
            const canvasData = canvas.exportArchitecture();

            // Build payload
            const payload = {
                name: architecture.metadata?.name || 'Untitled Architecture',
                description: architecture.metadata?.description || null,
                version: architecture.version || '1.0.0',
                architecture_json: {
                    version: architecture.version || '1.0.0',
                    metadata: {
                        ...architecture.metadata,
                        updated_at: new Date().toISOString()
                    },
                    requirements: architecture.requirements || {},
                    architecture: canvasData
                },
                owner: 'user' // TODO: Get from auth
            };

            let response;
            if (architectureId) {
                // Update
                response = await updateArchitecture(architectureId, payload);
                updateStatus('Architektur aktualisiert');
            } else {
                // Create
                response = await createArchitecture(payload);
                updateStatus('Architektur erstellt');
            }

            // Success
            alert('Architektur erfolgreich gespeichert!');

            // Redirect to architectures list
            setTimeout(() => {
                window.location.hash = '#/architectures';
            }, 500);

        } catch (error) {
            console.error('Fehler beim Speichern:', error);
            alert('Fehler beim Speichern: ' + error.message);

            // Reset button
            saveBtn.disabled = false;
            saveBtn.innerHTML = '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4"></path></svg><span>Speichern</span>';
        }
    }

    /**
     * Show JSON Modal
     */
    function showJSONModal(canvas, architecture) {
        const modal = document.getElementById('json-modal');
        const jsonPreview = document.getElementById('json-preview');
        const closeBtn = document.getElementById('close-json-modal');
        const copyBtn = document.getElementById('copy-json-btn');
        const downloadBtn = document.getElementById('download-json-btn');

        if (!modal || !jsonPreview) return;

        // Get current architecture JSON
        const canvasData = canvas.exportArchitecture();
        const fullArchitecture = {
            ...architecture,
            architecture: canvasData
        };

        const jsonString = JSON.stringify(fullArchitecture, null, 2);
        jsonPreview.textContent = jsonString;

        // Show modal
        modal.classList.remove('hidden');

        // Close handler
        closeBtn.addEventListener('click', () => {
            modal.classList.add('hidden');
        });

        // Copy handler
        copyBtn.addEventListener('click', async () => {
            try {
                await navigator.clipboard.writeText(jsonString);
                copyBtn.textContent = '✓ Kopiert!';
                setTimeout(() => {
                    copyBtn.textContent = 'In Zwischenablage kopieren';
                }, 2000);
            } catch (error) {
                alert('Fehler beim Kopieren');
            }
        });

        // Download handler
        downloadBtn.addEventListener('click', () => {
            exportJSON(canvas, architecture);
        });

        // Close on outside click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.add('hidden');
            }
        });
    }

    /**
     * Update Status Message
     */
    function updateStatus(message = 'Ready') {
        const statusEl = document.getElementById('status-message');
        if (statusEl) {
            statusEl.textContent = message;
        }
    }

    /**
     * Update Component Count
     */
    function updateComponentCount() {
        const countEl = document.getElementById('component-count');
        if (countEl && canvas) {
            countEl.textContent = `${canvas.components.size} Components`;
        }
    }

    /**
     * Update AI Advisor
     */
    function updateAIAdvisor() {
        const advisorContainer = document.getElementById('ai-advisor-bar');
        if (advisorContainer && currentArchitecture && canvas) {
            // Check current collapsed state before re-rendering
            const content = advisorContainer.querySelector('#advisor-content');
            const wasCollapsed = content?.classList.contains('hidden') ?? true;

            // Get current architecture from canvas
            const canvasData = canvas.exportArchitecture();
            const updatedArchitecture = {
                ...currentArchitecture,
                architecture: canvasData
            };

            // Re-render with same collapsed state
            renderAIAdvisor(advisorContainer, updatedArchitecture, wasCollapsed);
        }
    }
}
