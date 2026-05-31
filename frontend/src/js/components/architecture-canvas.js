/**
 * StackVertex - Architecture Canvas
 *
 * Drag & Drop Canvas für visuelle Architektur-Modellierung
 */

import { findComponentByService } from '../lib/aws-components.js';

/**
 * Architecture Canvas Class
 */
export class ArchitectureCanvas {
    constructor(container, options = {}) {
        this.container = container;
        this.provider = options.provider || 'aws';
        this.onComponentAdd = options.onComponentAdd;
        this.onComponentSelect = options.onComponentSelect;
        this.onComponentRemove = options.onComponentRemove;
        this.onRelationshipAdd = options.onRelationshipAdd;

        // State
        this.components = new Map(); // id -> component data
        this.relationships = []; // array of {from, to, type}
        this.selectedComponentId = null;
        this.scale = 1;
        this.panX = 0;
        this.panY = 0;
        this.isPanning = false;
        this.startPanX = 0;
        this.startPanY = 0;

        // Initialize
        this.render();
        this.setupEventHandlers();
    }

    /**
     * Rendert die Canvas
     */
    render() {
        this.container.innerHTML = `
            <div class="relative w-full h-full overflow-hidden">
                <!-- Canvas Controls -->
                <div class="absolute top-4 left-4 z-10 flex flex-col space-y-2">
                    <div class="bg-white dark:bg-gray-800 rounded-lg shadow-md p-2 flex flex-col space-y-1">
                        <button
                            id="zoom-in"
                            class="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors"
                            title="Zoom In"
                        >
                            <svg class="w-5 h-5 text-gray-700 dark:text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
                            </svg>
                        </button>
                        <button
                            id="zoom-out"
                            class="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors"
                            title="Zoom Out"
                        >
                            <svg class="w-5 h-5 text-gray-700 dark:text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18 12H6"></path>
                            </svg>
                        </button>
                        <button
                            id="zoom-reset"
                            class="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors"
                            title="Reset Zoom"
                        >
                            <svg class="w-5 h-5 text-gray-700 dark:text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4"></path>
                            </svg>
                        </button>
                    </div>
                    <div class="bg-white dark:bg-gray-800 rounded-lg shadow-md px-3 py-2 text-sm text-gray-700 dark:text-gray-300">
                        <span id="zoom-level">100%</span>
                    </div>
                </div>

                <!-- Canvas Grid -->
                <svg
                    id="canvas-svg"
                    class="w-full h-full cursor-move"
                    style="background-image: radial-gradient(circle, #d1d5db 1px, transparent 1px); background-size: 20px 20px;"
                >
                    <defs>
                        <!-- Arrow Marker for Relationships -->
                        <marker
                            id="arrow"
                            viewBox="0 0 10 10"
                            refX="9"
                            refY="5"
                            markerWidth="6"
                            markerHeight="6"
                            orient="auto-start-reverse"
                        >
                            <path d="M 0 0 L 10 5 L 0 10 z" fill="#3b82f6" />
                        </marker>
                    </defs>

                    <!-- Relationships Layer (rendered as SVG lines) -->
                    <g id="relationships-layer"></g>

                    <!-- Components Layer (rendered as foreignObject with HTML) -->
                    <g id="components-layer"></g>
                </svg>

                <!-- Empty State -->
                <div id="canvas-empty-state" class="absolute inset-0 flex items-center justify-center pointer-events-none">
                    <div class="text-center">
                        <div class="text-6xl mb-4">🏗️</div>
                        <h3 class="text-2xl font-semibold text-gray-900 dark:text-white mb-2">
                            Beginne mit deiner Architektur
                        </h3>
                        <p class="text-gray-600 dark:text-gray-400">
                            Wähle Components aus der linken Sidebar oder lade ein Template
                        </p>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Setup Event Handlers
     */
    setupEventHandlers() {
        const svg = this.container.querySelector('#canvas-svg');
        const zoomInBtn = this.container.querySelector('#zoom-in');
        const zoomOutBtn = this.container.querySelector('#zoom-out');
        const zoomResetBtn = this.container.querySelector('#zoom-reset');

        // Drag & Drop
        svg.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'copy';
        });

        svg.addEventListener('drop', (e) => {
            e.preventDefault();
            const data = JSON.parse(e.dataTransfer.getData('application/json'));

            if (data.type === 'component') {
                // Calculate drop position relative to canvas
                const rect = svg.getBoundingClientRect();
                const x = (e.clientX - rect.left - this.panX) / this.scale;
                const y = (e.clientY - rect.top - this.panY) / this.scale;

                this.addComponent(data.key, data.service, x, y);
            }
        });

        // Panning
        svg.addEventListener('mousedown', (e) => {
            if (e.button === 0 && !e.target.closest('.component-node')) {
                this.isPanning = true;
                this.startPanX = e.clientX - this.panX;
                this.startPanY = e.clientY - this.panY;
                svg.style.cursor = 'grabbing';
            }
        });

        svg.addEventListener('mousemove', (e) => {
            if (this.isPanning) {
                this.panX = e.clientX - this.startPanX;
                this.panY = e.clientY - this.startPanY;
                this.updateTransform();
            }
        });

        svg.addEventListener('mouseup', () => {
            this.isPanning = false;
            svg.style.cursor = 'move';
        });

        svg.addEventListener('mouseleave', () => {
            this.isPanning = false;
            svg.style.cursor = 'move';
        });

        // Zoom
        if (zoomInBtn) {
            zoomInBtn.addEventListener('click', () => this.zoom(1.2));
        }
        if (zoomOutBtn) {
            zoomOutBtn.addEventListener('click', () => this.zoom(0.8));
        }
        if (zoomResetBtn) {
            zoomResetBtn.addEventListener('click', () => this.resetZoom());
        }

        // Mouse Wheel Zoom
        svg.addEventListener('wheel', (e) => {
            e.preventDefault();
            const delta = e.deltaY > 0 ? 0.9 : 1.1;
            this.zoom(delta);
        });
    }

    /**
     * Füge Component zur Canvas hinzu
     */
    addComponent(componentKey, providerService, x, y) {
        const componentDef = findComponentByService(this.provider, providerService);

        if (!componentDef) {
            console.error('Component not found:', providerService);
            return;
        }

        const id = `component-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

        const component = {
            id,
            key: componentKey,
            type: componentDef.category,
            name: componentDef.name,
            provider_service: providerService,
            icon: componentDef.icon,
            position: { x, y },
            configuration: {}
        };

        this.components.set(id, component);
        this.renderComponents();
        this.updateEmptyState();

        // Callback
        if (this.onComponentAdd) {
            this.onComponentAdd(component);
        }

        // Select component
        this.selectComponent(id);
    }

    /**
     * Entferne Component
     */
    removeComponent(componentId) {
        this.components.delete(componentId);

        // Remove related relationships
        this.relationships = this.relationships.filter(
            rel => rel.from !== componentId && rel.to !== componentId
        );

        this.renderComponents();
        this.renderRelationships();
        this.updateEmptyState();

        // Callback
        if (this.onComponentRemove) {
            this.onComponentRemove(componentId);
        }

        // Deselect
        if (this.selectedComponentId === componentId) {
            this.selectedComponentId = null;
            if (this.onComponentSelect) {
                this.onComponentSelect(null);
            }
        }
    }

    /**
     * Rendert alle Components
     */
    renderComponents() {
        const layer = this.container.querySelector('#components-layer');
        if (!layer) return;

        layer.innerHTML = '';

        this.components.forEach((component) => {
            const foreignObject = document.createElementNS('http://www.w3.org/2000/svg', 'foreignObject');
            foreignObject.setAttribute('x', component.position.x);
            foreignObject.setAttribute('y', component.position.y);
            foreignObject.setAttribute('width', '200');
            foreignObject.setAttribute('height', '100');

            foreignObject.innerHTML = `
                <div
                    class="component-node bg-white dark:bg-gray-800 border-2 ${
                        this.selectedComponentId === component.id
                            ? 'border-blue-500'
                            : 'border-gray-300 dark:border-gray-600'
                    } rounded-lg shadow-lg p-4 cursor-move hover:shadow-xl transition-shadow"
                    data-component-id="${component.id}"
                    style="width: 200px;"
                >
                    <div class="flex items-start justify-between mb-2">
                        <div class="flex items-center space-x-2">
                            <span class="text-2xl">${component.icon}</span>
                            <div>
                                <div class="text-sm font-medium text-gray-900 dark:text-white">
                                    ${component.name}
                                </div>
                                <div class="text-xs text-gray-500 dark:text-gray-400">
                                    ${component.type}
                                </div>
                            </div>
                        </div>
                        <button
                            class="component-delete text-gray-400 hover:text-red-600 transition-colors"
                            data-component-id="${component.id}"
                        >
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                            </svg>
                        </button>
                    </div>
                    <div class="text-xs text-gray-600 dark:text-gray-400">
                        ID: ${component.id.split('-')[1]}...
                    </div>
                </div>
            `;

            layer.appendChild(foreignObject);

            // Setup Component Event Handlers
            const node = foreignObject.querySelector('.component-node');
            const deleteBtn = foreignObject.querySelector('.component-delete');

            // Click to Select
            node.addEventListener('click', (e) => {
                e.stopPropagation();
                this.selectComponent(component.id);
            });

            // Delete
            deleteBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.removeComponent(component.id);
            });

            // Drag Component
            let isDragging = false;
            let startX, startY;

            node.addEventListener('mousedown', (e) => {
                if (e.target.closest('.component-delete')) return;

                isDragging = true;
                startX = e.clientX - component.position.x * this.scale;
                startY = e.clientY - component.position.y * this.scale;
                node.style.cursor = 'grabbing';
            });

            document.addEventListener('mousemove', (e) => {
                if (!isDragging) return;

                const newX = (e.clientX - startX) / this.scale;
                const newY = (e.clientY - startY) / this.scale;

                component.position.x = newX;
                component.position.y = newY;

                foreignObject.setAttribute('x', newX);
                foreignObject.setAttribute('y', newY);

                this.renderRelationships();
            });

            document.addEventListener('mouseup', () => {
                if (isDragging) {
                    isDragging = false;
                    node.style.cursor = 'move';
                }
            });
        });
    }

    /**
     * Rendert alle Relationships
     */
    renderRelationships() {
        const layer = this.container.querySelector('#relationships-layer');
        if (!layer) return;

        layer.innerHTML = '';

        this.relationships.forEach((rel) => {
            const fromComp = this.components.get(rel.from);
            const toComp = this.components.get(rel.to);

            if (!fromComp || !toComp) return;

            // Calculate line positions (center of components)
            const x1 = fromComp.position.x + 100;
            const y1 = fromComp.position.y + 50;
            const x2 = toComp.position.x + 100;
            const y2 = toComp.position.y + 50;

            const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            line.setAttribute('x1', x1);
            line.setAttribute('y1', y1);
            line.setAttribute('x2', x2);
            line.setAttribute('y2', y2);
            line.setAttribute('stroke', '#3b82f6');
            line.setAttribute('stroke-width', '2');
            line.setAttribute('marker-end', 'url(#arrow)');

            layer.appendChild(line);
        });
    }

    /**
     * Selektiere Component
     */
    selectComponent(componentId) {
        this.selectedComponentId = componentId;
        this.renderComponents();

        const component = this.components.get(componentId);
        if (this.onComponentSelect && component) {
            this.onComponentSelect(component);
        }
    }

    /**
     * Update Transform (Zoom & Pan)
     */
    updateTransform() {
        const componentsLayer = this.container.querySelector('#components-layer');
        const relationshipsLayer = this.container.querySelector('#relationships-layer');

        const transform = `translate(${this.panX}, ${this.panY}) scale(${this.scale})`;

        if (componentsLayer) {
            componentsLayer.setAttribute('transform', transform);
        }
        if (relationshipsLayer) {
            relationshipsLayer.setAttribute('transform', transform);
        }

        // Update Zoom Level Display
        const zoomLevel = this.container.querySelector('#zoom-level');
        if (zoomLevel) {
            zoomLevel.textContent = `${Math.round(this.scale * 100)}%`;
        }
    }

    /**
     * Zoom In/Out
     */
    zoom(factor) {
        this.scale = Math.max(0.1, Math.min(3, this.scale * factor));
        this.updateTransform();
    }

    /**
     * Reset Zoom
     */
    resetZoom() {
        this.scale = 1;
        this.panX = 0;
        this.panY = 0;
        this.updateTransform();
    }

    /**
     * Update Empty State
     */
    updateEmptyState() {
        const emptyState = this.container.querySelector('#canvas-empty-state');
        if (emptyState) {
            emptyState.style.display = this.components.size > 0 ? 'none' : 'flex';
        }
    }

    /**
     * Load Architecture JSON
     */
    loadArchitecture(architectureJson) {
        // Clear current state
        this.components.clear();
        this.relationships = [];

        // Load components
        if (architectureJson.architecture?.components) {
            architectureJson.architecture.components.forEach((comp, index) => {
                // Position components in a grid if no position specified
                const x = comp.position?.x || (index % 4) * 250 + 50;
                const y = comp.position?.y || Math.floor(index / 4) * 150 + 50;

                const componentDef = findComponentByService(this.provider, comp.provider_service);

                if (componentDef) {
                    this.components.set(comp.id, {
                        ...comp,
                        icon: componentDef.icon,
                        position: { x, y }
                    });
                }
            });
        }

        // Load relationships
        if (architectureJson.architecture?.relationships) {
            this.relationships = architectureJson.architecture.relationships;
        }

        this.renderComponents();
        this.renderRelationships();
        this.updateEmptyState();
    }

    /**
     * Export Architecture JSON
     */
    exportArchitecture() {
        const components = Array.from(this.components.values()).map(comp => ({
            id: comp.id,
            type: comp.type,
            name: comp.name,
            provider_service: comp.provider_service,
            position: comp.position,
            configuration: comp.configuration
        }));

        return {
            components,
            relationships: this.relationships
        };
    }
}
