/**
 * Infrastructure Canvas Component
 *
 * Visuelle Darstellung der Cloud-Architektur mit Cytoscape.js
 * Features:
 * - Drag & Drop aus der Component Palette
 * - AWS Resource Nodes (VPC, EC2, RDS, S3, etc.)
 * - Verbindungen zwischen Ressourcen
 * - IP-Adressen-Anzeige auf Nodes
 * - Auto-Layout und manuelle Positionierung
 * - Click zum Öffnen der Settings in Tabs
 */

import cytoscape from 'cytoscape';

export class InfrastructureCanvas {
    constructor(containerId, onNodeClick, onEdgeClick) {
        this.container = document.getElementById(containerId);
        this.onNodeClick = onNodeClick;
        this.onEdgeClick = onEdgeClick;
        this.cy = null;
        this.components = new Map(); // componentId -> component data

        this.init();
    }

    init() {
        this.cy = cytoscape({
            container: this.container,

            style: [
                // VPC Node Style
                {
                    selector: 'node[type="vpc"]',
                    style: {
                        'background-color': '#667eea',
                        'label': 'data(label)',
                        'color': '#fff',
                        'text-valign': 'center',
                        'text-halign': 'center',
                        'width': 200,
                        'height': 150,
                        'shape': 'roundrectangle',
                        'border-width': 3,
                        'border-color': '#764ba2',
                        'font-size': '12px',
                        'text-wrap': 'wrap',
                        'text-max-width': '180px'
                    }
                },

                // EC2 Node Style
                {
                    selector: 'node[type="ec2"]',
                    style: {
                        'background-color': '#FF9900',
                        'label': 'data(label)',
                        'color': '#fff',
                        'width': 120,
                        'height': 80,
                        'shape': 'roundrectangle',
                        'border-width': 2,
                        'border-color': '#CC7A00',
                        'font-size': '11px',
                        'text-wrap': 'wrap',
                        'text-max-width': '100px'
                    }
                },

                // RDS Node Style
                {
                    selector: 'node[type="rds"]',
                    style: {
                        'background-color': '#527FFF',
                        'label': 'data(label)',
                        'color': '#fff',
                        'width': 120,
                        'height': 80,
                        'shape': 'roundrectangle',
                        'border-width': 2,
                        'border-color': '#3D5FCC',
                        'font-size': '11px',
                        'text-wrap': 'wrap',
                        'text-max-width': '100px'
                    }
                },

                // S3 Node Style
                {
                    selector: 'node[type="s3"]',
                    style: {
                        'background-color': '#569A31',
                        'label': 'data(label)',
                        'color': '#fff',
                        'width': 100,
                        'height': 100,
                        'shape': 'barrel',
                        'border-width': 2,
                        'border-color': '#3D6B22',
                        'font-size': '11px',
                        'text-wrap': 'wrap',
                        'text-max-width': '80px'
                    }
                },

                // ALB Node Style
                {
                    selector: 'node[type="alb"]',
                    style: {
                        'background-color': '#8C4FFF',
                        'label': 'data(label)',
                        'color': '#fff',
                        'width': 140,
                        'height': 60,
                        'shape': 'roundrectangle',
                        'border-width': 2,
                        'border-color': '#6B3ACC',
                        'font-size': '11px'
                    }
                },

                // Lambda Node Style
                {
                    selector: 'node[type="lambda"]',
                    style: {
                        'background-color': '#FF9900',
                        'label': 'data(label)',
                        'color': '#fff',
                        'width': 90,
                        'height': 90,
                        'shape': 'triangle',
                        'border-width': 2,
                        'border-color': '#CC7A00',
                        'font-size': '11px'
                    }
                },

                // ECS Node Style
                {
                    selector: 'node[type="ecs"]',
                    style: {
                        'background-color': '#FF9900',
                        'label': 'data(label)',
                        'color': '#fff',
                        'width': 110,
                        'height': 90,
                        'shape': 'hexagon',
                        'border-width': 2,
                        'border-color': '#CC7A00',
                        'font-size': '11px'
                    }
                },

                // DynamoDB Node Style
                {
                    selector: 'node[type="dynamodb"]',
                    style: {
                        'background-color': '#4053D6',
                        'label': 'data(label)',
                        'color': '#fff',
                        'width': 120,
                        'height': 80,
                        'shape': 'roundrectangle',
                        'border-width': 2,
                        'border-color': '#2D3A99',
                        'font-size': '11px'
                    }
                },

                // ElastiCache Node Style
                {
                    selector: 'node[type="elasticache"]',
                    style: {
                        'background-color': '#C925D1',
                        'label': 'data(label)',
                        'color': '#fff',
                        'width': 120,
                        'height': 80,
                        'shape': 'roundrectangle',
                        'border-width': 2,
                        'border-color': '#991A9E',
                        'font-size': '11px'
                    }
                },

                // Subnet Node Style (nested in VPC)
                {
                    selector: 'node[type="subnet"]',
                    style: {
                        'background-color': 'data(subnetColor)',
                        'label': 'data(label)',
                        'width': 160,
                        'height': 100,
                        'shape': 'roundrectangle',
                        'border-width': 2,
                        'border-color': '#666',
                        'border-style': 'dashed',
                        'font-size': '11px',
                        'color': '#333'
                    }
                },

                // Internet Gateway Node Style
                {
                    selector: 'node[type="igw"]',
                    style: {
                        'background-color': '#232F3E',
                        'label': 'data(label)',
                        'color': '#fff',
                        'width': 100,
                        'height': 60,
                        'shape': 'diamond',
                        'border-width': 2,
                        'border-color': '#000',
                        'font-size': '11px'
                    }
                },

                // NAT Gateway Node Style
                {
                    selector: 'node[type="nat"]',
                    style: {
                        'background-color': '#D45B07',
                        'label': 'data(label)',
                        'color': '#fff',
                        'width': 100,
                        'height': 60,
                        'shape': 'diamond',
                        'border-width': 2,
                        'border-color': '#A04605',
                        'font-size': '11px'
                    }
                },

                // Security Group Node Style
                {
                    selector: 'node[type="sg"]',
                    style: {
                        'background-color': '#DD344C',
                        'label': 'data(label)',
                        'color': '#fff',
                        'width': 100,
                        'height': 70,
                        'shape': 'roundrectangle',
                        'border-width': 2,
                        'border-color': '#A82638',
                        'font-size': '11px'
                    }
                },

                // Network ACL Node Style
                {
                    selector: 'node[type="nacl"]',
                    style: {
                        'background-color': '#B0084D',
                        'label': 'data(label)',
                        'color': '#fff',
                        'width': 100,
                        'height': 70,
                        'shape': 'roundrectangle',
                        'border-width': 2,
                        'border-color': '#7A0536',
                        'font-size': '11px'
                    }
                },

                // IAM Role Node Style
                {
                    selector: 'node[type="iam"]',
                    style: {
                        'background-color': '#DD344C',
                        'label': 'data(label)',
                        'color': '#fff',
                        'width': 90,
                        'height': 90,
                        'shape': 'pentagon',
                        'border-width': 2,
                        'border-color': '#A82638',
                        'font-size': '11px'
                    }
                },

                // Edge (Connection) Style
                {
                    selector: 'edge',
                    style: {
                        'width': 3,
                        'line-color': '#999',
                        'target-arrow-color': '#999',
                        'target-arrow-shape': 'triangle',
                        'curve-style': 'bezier',
                        'label': 'data(label)',
                        'font-size': '10px',
                        'text-background-color': '#fff',
                        'text-background-opacity': 0.8,
                        'text-background-padding': '3px'
                    }
                },

                // Selected Style
                {
                    selector: ':selected',
                    style: {
                        'border-width': 4,
                        'border-color': '#FF6B6B'
                    }
                }
            ],

            layout: {
                name: 'preset'
            },

            // Enable interactions
            userZoomingEnabled: true,
            userPanningEnabled: true,
            boxSelectionEnabled: true,
            minZoom: 0.3,
            maxZoom: 3
        });

        this.attachEventListeners();
        this.setupDropZone();
    }

    attachEventListeners() {
        // Node click -> Open settings tab
        this.cy.on('tap', 'node', (evt) => {
            const node = evt.target;
            const componentId = node.id();
            const componentType = node.data('type');

            if (this.onNodeClick) {
                this.onNodeClick(componentId, componentType);
            }
        });

        // Edge click
        this.cy.on('tap', 'edge', (evt) => {
            const edge = evt.target;
            if (this.onEdgeClick) {
                this.onEdgeClick(edge.id(), edge.data());
            }
        });

        // Drag end -> Update positions in JSON
        this.cy.on('dragfree', 'node', (evt) => {
            const node = evt.target;
            const position = node.position();
            this.updateComponentPosition(node.id(), position);
        });
    }

    setupDropZone() {
        this.container.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'copy';
        });

        this.container.addEventListener('drop', (e) => {
            e.preventDefault();
            const componentType = e.dataTransfer.getData('componentType');

            if (!componentType) return;

            // Calculate drop position in Cytoscape coordinates
            const rect = this.container.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;

            // Convert DOM coordinates to Cytoscape coordinates
            const pos = this.cy.renderer().projectIntoViewport(x, y);

            // Generate unique ID
            const componentId = `${componentType}-${Date.now()}`;

            // Create component with default config
            const component = {
                id: componentId,
                type: componentType,
                name: this.generateDefaultName(componentType),
                config: this.generateDefaultConfig(componentType),
                position: { x: pos[0], y: pos[1] }
            };

            this.addComponent(component);

            // Trigger event for state sync
            window.dispatchEvent(new CustomEvent('component-added', {
                detail: { component }
            }));
        });
    }

    generateDefaultName(type) {
        const count = this.cy.nodes(`[type="${type}"]`).length + 1;
        const names = {
            vpc: 'VPC',
            subnet: 'Subnet',
            ec2: 'EC2 Instance',
            rds: 'RDS Database',
            s3: 'S3 Bucket',
            lambda: 'Lambda Function',
            alb: 'Load Balancer',
            ecs: 'ECS Service',
            dynamodb: 'DynamoDB Table',
            elasticache: 'ElastiCache',
            igw: 'Internet Gateway',
            nat: 'NAT Gateway',
            sg: 'Security Group',
            nacl: 'Network ACL',
            iam: 'IAM Role'
        };
        return `${names[type] || type} ${count}`;
    }

    generateDefaultConfig(type) {
        const configs = {
            vpc: {
                cidr: '10.0.0.0/16',
                enableDnsHostnames: true,
                enableDnsSupport: true
            },
            subnet: {
                cidr: '10.0.1.0/24',
                subnetType: 'public',
                availabilityZone: 'us-east-1a'
            },
            ec2: {
                instanceType: 't3.micro',
                ami: 'ami-0c55b159cbfafe1f0',
                privateIp: null,
                hasPublicIp: false,
                publicIp: null
            },
            rds: {
                engine: 'postgres',
                engineVersion: '14.7',
                instanceClass: 'db.t3.micro',
                privateIp: null
            },
            s3: {
                versioning: false,
                encryption: true,
                publicAccess: false
            },
            lambda: {
                runtime: 'python3.11',
                memory: 128,
                timeout: 30
            },
            alb: {
                scheme: 'internet-facing',
                ipAddressType: 'ipv4'
            },
            ecs: {
                launchType: 'FARGATE',
                cpu: '256',
                memory: '512'
            },
            dynamodb: {
                billingMode: 'PAY_PER_REQUEST',
                partitionKey: 'id'
            },
            elasticache: {
                engine: 'redis',
                nodeType: 'cache.t3.micro'
            },
            igw: {},
            nat: {
                subnetId: null
            },
            sg: {
                description: 'Security Group',
                rules: []
            },
            nacl: {
                rules: []
            },
            iam: {
                policies: []
            }
        };
        return configs[type] || {};
    }

    /**
     * Add component to canvas
     */
    addComponent(component) {
        const { id, type, name, config } = component;

        // Build label with IP info
        let label = name;
        if (config.privateIp) {
            label += `\n${config.privateIp}`;
        }
        if (config.hasPublicIp) {
            label += `\n${config.publicIp || '[Public IP]'}`;
        }
        if (config.cidr) {
            label += `\n${config.cidr}`;
        }

        // Determine subnet color
        let subnetColor = '#E8F4F8';
        if (config.subnetType === 'public') {
            subnetColor = '#C8E6C9'; // Green
        } else if (config.subnetType === 'private') {
            subnetColor = '#BBDEFB'; // Blue
        } else if (config.subnetType === 'database') {
            subnetColor = '#F8BBD0'; // Pink
        }

        this.cy.add({
            group: 'nodes',
            data: {
                id: id,
                type: type,
                label: label,
                subnetColor: subnetColor,
                ...config
            },
            position: component.position || { x: 200, y: 200 }
        });

        this.components.set(id, component);
    }

    /**
     * Update component (z.B. wenn IP in Tabs geändert wird)
     */
    updateComponent(componentId, updates) {
        const node = this.cy.getElementById(componentId);
        if (!node) return;

        const component = this.components.get(componentId);
        Object.assign(component.config, updates);

        // Update label with new IP
        let label = component.name;
        if (updates.privateIp || component.config.privateIp) {
            label += `\n${updates.privateIp || component.config.privateIp}`;
        }
        if (updates.publicIp) {
            label += `\n${updates.publicIp}`;
        }
        if (updates.cidr) {
            label += `\n${updates.cidr}`;
        }

        // Update subnet color if changed
        if (updates.subnetType) {
            let subnetColor = '#E8F4F8';
            if (updates.subnetType === 'public') {
                subnetColor = '#C8E6C9';
            } else if (updates.subnetType === 'private') {
                subnetColor = '#BBDEFB';
            } else if (updates.subnetType === 'database') {
                subnetColor = '#F8BBD0';
            }
            node.data('subnetColor', subnetColor);
        }

        node.data('label', label);

        // Update other data fields
        Object.assign(node.data(), updates);
    }

    /**
     * Remove component
     */
    removeComponent(componentId) {
        this.cy.getElementById(componentId).remove();
        this.components.delete(componentId);
    }

    /**
     * Add connection between components
     */
    addConnection(fromId, toId, connectionData = {}) {
        const edgeId = `${fromId}-${toId}`;

        let label = '';
        if (connectionData.port) {
            label = `:${connectionData.port}`;
        }
        if (connectionData.protocol) {
            label += ` (${connectionData.protocol})`;
        }

        this.cy.add({
            group: 'edges',
            data: {
                id: edgeId,
                source: fromId,
                target: toId,
                label: label,
                ...connectionData
            }
        });
    }

    /**
     * Remove connection
     */
    removeConnection(edgeId) {
        this.cy.getElementById(edgeId).remove();
    }

    /**
     * Auto-layout
     */
    autoLayout() {
        const layout = this.cy.layout({
            name: 'breadthfirst',
            directed: true,
            spacingFactor: 1.5,
            padding: 30
        });
        layout.run();
    }

    /**
     * Fit to viewport
     */
    fit() {
        this.cy.fit(null, 50);
    }

    /**
     * Export as image
     */
    exportImage() {
        return this.cy.png({ scale: 2, full: true, bg: '#F9FAFB' });
    }

    /**
     * Update component position (called after drag)
     */
    updateComponentPosition(componentId, position) {
        const component = this.components.get(componentId);
        if (component) {
            component.position = position;
            // Trigger sync to JSON state
            window.dispatchEvent(new CustomEvent('component-position-changed', {
                detail: { componentId, position }
            }));
        }
    }

    /**
     * Load from JSON
     */
    loadFromJSON(architectureJSON) {
        this.cy.elements().remove();
        this.components.clear();

        // Add all components
        for (const [id, component] of Object.entries(architectureJSON.components || {})) {
            this.addComponent({
                id,
                type: component.type,
                name: component.name,
                config: component.config,
                position: component.position
            });
        }

        // Add all connections
        for (const connection of architectureJSON.connections || []) {
            this.addConnection(connection.from, connection.to, connection.data);
        }

        this.fit();
    }

    /**
     * Export to JSON
     */
    exportToJSON() {
        const components = {};
        this.components.forEach((component, id) => {
            components[id] = {
                type: component.type,
                name: component.name,
                config: component.config,
                position: component.position
            };
        });

        const connections = [];
        this.cy.edges().forEach(edge => {
            connections.push({
                from: edge.data('source'),
                to: edge.data('target'),
                data: edge.data()
            });
        });

        return { components, connections };
    }

    /**
     * Get selected component IDs
     */
    getSelectedComponents() {
        return this.cy.$(':selected').nodes().map(node => node.id());
    }

    /**
     * Delete selected components
     */
    deleteSelected() {
        const selected = this.cy.$(':selected');
        const ids = selected.nodes().map(node => node.id());

        selected.remove();

        ids.forEach(id => this.components.delete(id));

        return ids;
    }
}
