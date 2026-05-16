/**
 * Infrastructure Designer Page Controller
 *
 * Koordiniert Canvas, Palette und Tabs für den visuellen Infrastructure Designer
 */

import { InfrastructureCanvas } from '../components/InfrastructureCanvas.js';
import { ComponentPalette } from '../components/ComponentPalette.js';
import { TabSystem } from '../components/TabSystem.js';
import { sampleArchitecture } from '../demo/sample-architecture.js';
import { setupDebugHelpers } from '../utils/designer-debug.js';
import {
    saveDesignerArchitecture,
    loadDesignerArchitecture,
    validateArchitecture,
    generateTerraform
} from '../api/designer.js';

class InfrastructureDesignerPage {
    constructor() {
        this.canvas = null;
        this.palette = null;
        this.tabs = null;
        this.architectureState = {
            id: null,
            name: 'Untitled Architecture',
            components: {},
            connections: []
        };

        this.init();
    }

    init() {
        // Initialize Components
        this.palette = new ComponentPalette('component-palette');

        this.canvas = new InfrastructureCanvas(
            'canvas-container',
            (componentId, componentType) => this.handleNodeClick(componentId, componentType),
            (edgeId, edgeData) => this.handleEdgeClick(edgeId, edgeData)
        );

        this.tabs = new TabSystem(
            'tab-headers',
            'tab-content',
            (tabId, component) => this.handleTabChange(tabId, component),
            (tabId) => this.handleTabClose(tabId)
        );

        // Attach Toolbar Event Listeners
        this.attachToolbarListeners();

        // Attach Global Event Listeners
        this.attachGlobalListeners();

        // Load architecture from URL or localStorage
        this.loadArchitecture();

        // Setup debug helpers (dev only)
        setupDebugHelpers(this);
    }

    attachToolbarListeners() {
        // Auto Layout
        document.getElementById('autoLayoutBtn')?.addEventListener('click', () => {
            this.canvas.autoLayout();
        });

        // Fit to View
        document.getElementById('fitBtn')?.addEventListener('click', () => {
            this.canvas.fit();
        });

        // Export Image
        document.getElementById('exportImageBtn')?.addEventListener('click', () => {
            const imageData = this.canvas.exportImage();
            this.downloadImage(imageData);
        });

        // Delete Selected
        document.getElementById('deleteBtn')?.addEventListener('click', () => {
            const selected = this.canvas.getSelectedComponents();
            if (selected.length === 0) {
                alert('Keine Komponenten ausgewählt');
                return;
            }

            if (confirm(`${selected.length} Komponente(n) löschen?`)) {
                const deletedIds = this.canvas.deleteSelected();

                // Remove from state
                deletedIds.forEach(id => {
                    delete this.architectureState.components[id];
                });

                // Close tabs for deleted components
                deletedIds.forEach(id => {
                    if (this.tabs.tabs.has(id)) {
                        this.tabs.closeTab(id);
                    }
                });
            }
        });

        // Validate Architecture
        document.getElementById('validateBtn')?.addEventListener('click', () => {
            this.validateArchitecture();
        });

        // Generate Terraform
        document.getElementById('generateTerraformBtn')?.addEventListener('click', () => {
            this.generateTerraformCode();
        });

        // Save Architecture
        document.getElementById('saveBtn')?.addEventListener('click', () => {
            this.saveArchitecture();
        });
    }

    attachGlobalListeners() {
        // Component added from palette
        window.addEventListener('component-added', (e) => {
            const { component } = e.detail;
            this.architectureState.components[component.id] = component;

            // Auto-open tab for new component
            this.tabs.openTab(component);
        });

        // Component updated from tabs
        window.addEventListener('component-updated', (e) => {
            const { componentId, updates } = e.detail;

            // Update canvas
            this.canvas.updateComponent(componentId, updates);

            // Update state
            const component = this.architectureState.components[componentId];
            if (component) {
                if (updates.name) {
                    component.name = updates.name;
                }
                Object.assign(component.config, updates);
            }

            // Update tab header if name changed
            if (updates.name) {
                this.tabs.updateTab(componentId, { name: updates.name });
            }
        });

        // Component position changed (drag on canvas)
        window.addEventListener('component-position-changed', (e) => {
            const { componentId, position } = e.detail;
            const component = this.architectureState.components[componentId];
            if (component) {
                component.position = position;
            }
        });

        // Load architecture event
        window.addEventListener('load-architecture', (e) => {
            const { architecture } = e.detail;
            this.loadArchitectureData(architecture);
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            // Delete: Delete selected components
            if (e.key === 'Delete' || e.key === 'Backspace') {
                const activeElement = document.activeElement;
                // Don't delete if user is typing in an input
                if (activeElement.tagName === 'INPUT' || activeElement.tagName === 'TEXTAREA') {
                    return;
                }

                const deletedIds = this.canvas.deleteSelected();
                deletedIds.forEach(id => {
                    delete this.architectureState.components[id];
                    if (this.tabs.tabs.has(id)) {
                        this.tabs.closeTab(id);
                    }
                });
            }

            // Ctrl/Cmd + S: Save
            if ((e.ctrlKey || e.metaKey) && e.key === 's') {
                e.preventDefault();
                this.saveArchitecture();
            }

            // Ctrl/Cmd + Z: Undo (TODO: Implement undo/redo)
            if ((e.ctrlKey || e.metaKey) && e.key === 'z') {
                e.preventDefault();
                console.log('Undo (not implemented yet)');
            }
        });
    }

    handleNodeClick(componentId, componentType) {
        const component = this.architectureState.components[componentId];
        if (component) {
            this.tabs.openTab(component);
        }
    }

    handleEdgeClick(edgeId, edgeData) {
        console.log('Edge clicked:', edgeId, edgeData);
        // TODO: Open connection configuration modal
    }

    handleTabChange(tabId, component) {
        // Could highlight component on canvas
        console.log('Tab changed to:', tabId);
    }

    handleTabClose(tabId) {
        console.log('Tab closed:', tabId);
    }

    loadArchitecture() {
        // Check URL for architecture ID
        const urlParams = new URLSearchParams(window.location.search);
        const architectureId = urlParams.get('id');

        if (architectureId === 'demo') {
            // Load demo architecture
            this.loadArchitectureData(sampleArchitecture);
        } else if (architectureId) {
            // Load from API
            this.loadFromAPI(architectureId);
        } else {
            // Load from localStorage (draft)
            const draft = localStorage.getItem('architecture-draft');
            if (draft) {
                try {
                    const data = JSON.parse(draft);
                    this.loadArchitectureData(data);
                } catch (err) {
                    console.error('Failed to load draft:', err);
                }
            }
        }
    }

    async loadFromAPI(architectureId) {
        try {
            const data = await loadDesignerArchitecture(architectureId);
            this.loadArchitectureData(data);
        } catch (err) {
            console.error('Failed to load architecture:', err);
            alert('Fehler beim Laden der Architektur');
        }
    }

    loadArchitectureData(data) {
        this.architectureState = data;
        this.canvas.loadFromJSON(data);

        // Update page title
        document.title = `${data.name || 'Untitled'} - Infrastructure Designer`;
    }

    saveArchitecture() {
        // Export current state from canvas
        const canvasData = this.canvas.exportToJSON();

        // Merge with architecture state
        this.architectureState.components = canvasData.components;
        this.architectureState.connections = canvasData.connections;

        // Save to localStorage as draft
        localStorage.setItem('architecture-draft', JSON.stringify(this.architectureState));

        // If architecture has an ID, save to API
        if (this.architectureState.id) {
            this.saveToAPI();
        } else {
            // First save - show save dialog
            this.showSaveDialog();
        }
    }

    async saveToAPI() {
        try {
            // Export current state from canvas
            const canvasData = this.canvas.exportToJSON();

            // Prepare architecture JSON for designer API
            const architectureJson = {
                version: '1.0.0',
                metadata: {
                    name: this.architectureState.name,
                    description: this.architectureState.description || '',
                    createdAt: new Date().toISOString(),
                    updatedAt: new Date().toISOString()
                },
                components: canvasData.components || {},
                connections: canvasData.connections || [],
                ipAllocations: {}
            };

            // Save via designer API
            const result = await saveDesignerArchitecture({
                name: this.architectureState.name,
                description: this.architectureState.description,
                architecture_json: architectureJson,
                owner: null  // TODO: Get from auth context
            });

            // Update state with saved ID
            if (result.architecture_id) {
                this.architectureState.id = result.architecture_id;
                // Update URL
                window.history.pushState({}, '', `?id=${result.architecture_id}`);
            }

            this.showSuccessMessage('Architektur gespeichert!');
        } catch (err) {
            console.error('Failed to save architecture:', err);
            alert('Fehler beim Speichern der Architektur');
        }
    }

    showSaveDialog() {
        const name = prompt('Name der Architektur:', this.architectureState.name);
        if (!name) return;

        this.architectureState.name = name;

        // Create new architecture via API
        this.createArchitecture();
    }

    async createArchitecture() {
        // Same as saveToAPI (creates new if no ID exists)
        await this.saveToAPI();
    }

    async validateArchitecture() {
        try {
            // Export current state from canvas
            const canvasData = this.canvas.exportToJSON();

            // Prepare architecture JSON
            const architectureJson = {
                version: '1.0.0',
                metadata: {
                    name: this.architectureState.name,
                    description: this.architectureState.description || ''
                },
                components: canvasData.components || {},
                connections: canvasData.connections || []
            };

            // Validate via API
            const result = await validateArchitecture(architectureJson);

            // Show validation result
            if (result.valid) {
                this.showSuccessMessage(
                    `✓ Validation erfolgreich: ${result.component_count} Components, ${result.connection_count} Connections`
                );
                if (result.warnings.length > 0) {
                    console.warn('Validation warnings:', result.warnings);
                    alert(`Warnings:\n${result.warnings.join('\n')}`);
                }
            } else {
                alert(`Validation fehlgeschlagen:\n\n${result.errors.join('\n')}`);
            }
        } catch (err) {
            console.error('Validation error:', err);
            alert('Fehler bei der Validierung');
        }
    }

    async generateTerraformCode() {
        try {
            // Export current state from canvas
            const canvasData = this.canvas.exportToJSON();

            // Prepare architecture JSON
            const architectureJson = {
                version: '1.0.0',
                metadata: {
                    name: this.architectureState.name,
                    description: this.architectureState.description || '',
                    provider: 'aws'
                },
                components: canvasData.components || {},
                connections: canvasData.connections || []
            };

            // Generate via API
            this.showSuccessMessage('Terraform wird generiert...');
            const result = await generateTerraform(architectureJson);

            // Show success
            this.showSuccessMessage(
                `✓ Terraform generiert: ${result.component_count} Components → ${Object.keys(result.files).length} Files`
            );

            // Download as ZIP
            await this.downloadTerraformZip(result.files);

        } catch (err) {
            console.error('Terraform generation error:', err);
            alert('Fehler bei der Terraform-Generierung');
        }
    }

    async downloadTerraformZip(files) {
        // Simple download of individual files (no JSZip dependency)
        // In production, use JSZip or backend endpoint that returns ZIP

        // For now: download main.tf as example
        if (files['main.tf']) {
            const blob = new Blob([files['main.tf']], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = 'main.tf';
            link.click();
            URL.revokeObjectURL(url);

            // Notify user about other files
            const fileList = Object.keys(files).join(', ');
            console.log('Generated files:', fileList);
            alert(`Terraform Dateien generiert:\n${fileList}\n\n(Aktuell wird nur main.tf heruntergeladen)`);
        }
    }

    downloadImage(imageData) {
        const link = document.createElement('a');
        link.download = `${this.architectureState.name || 'architecture'}.png`;
        link.href = imageData;
        link.click();
    }

    showSuccessMessage(message) {
        const toast = document.createElement('div');
        toast.className = 'fixed bottom-4 right-4 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg z-50';
        toast.innerHTML = `
            <div class="flex items-center gap-2">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                </svg>
                <span>${message}</span>
            </div>
        `;
        document.body.appendChild(toast);

        setTimeout(() => {
            toast.remove();
        }, 3000);
    }
}

// Initialize page when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new InfrastructureDesignerPage();
});
