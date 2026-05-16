/**
 * Sync Coordinator
 *
 * Koordiniert Synchronisation zwischen Canvas, Tabs und State
 * Event-driven Architecture für bidirektionale Updates
 */

export class SyncCoordinator {
    constructor(state, canvas, tabs) {
        this.state = state;
        this.canvas = canvas;
        this.tabs = tabs;

        this.setupListeners();
    }

    /**
     * Setup Event Listeners für alle Komponenten
     */
    setupListeners() {
        // State changes → Update Canvas & Tabs
        this.state.subscribe((changeType, payload, state) => {
            this.handleStateChange(changeType, payload);
        });

        // Canvas clicks → Open tabs
        if (this.canvas.onNodeClick) {
            const originalHandler = this.canvas.onNodeClick;
            this.canvas.onNodeClick = (componentId, componentType) => {
                const component = this.state.getComponent(componentId);
                if (component) {
                    this.tabs.openComponent(componentId, component);
                }
                if (originalHandler) {
                    originalHandler(componentId, componentType);
                }
            };
        } else {
            this.canvas.onNodeClick = (componentId, componentType) => {
                const component = this.state.getComponent(componentId);
                if (component) {
                    this.tabs.openComponent(componentId, component);
                }
            };
        }

        // Canvas position changes → Update State
        window.addEventListener('component-position-changed', (e) => {
            const { componentId, position } = e.detail;
            this.state.updateComponent(componentId, { position });
        });

        // Tab updates → Update State
        window.addEventListener('component-updated', (e) => {
            const { componentId, field, value } = e.detail;
            if (field === 'name') {
                this.state.updateComponent(componentId, { name: value });
            } else {
                this.state.updateComponent(componentId, {
                    config: { [field]: value }
                });
            }
        });

        // Tab delete → Delete from State
        window.addEventListener('component-deleted', (e) => {
            const { componentId } = e.detail;
            this.state.deleteComponent(componentId);
        });

        // Component added from canvas → Add to State
        window.addEventListener('component-added', (e) => {
            const { component } = e.detail;
            // Add to state if not already there
            if (!this.state.hasComponent(component.id)) {
                this.state.addComponent(
                    component.type,
                    component.name,
                    component.config,
                    component.position
                );
            }
        });
    }

    /**
     * Handle State Changes
     */
    handleStateChange(changeType, payload) {
        switch (changeType) {
            case 'component-added':
                this.handleComponentAdded(payload);
                break;

            case 'component-updated':
                this.handleComponentUpdated(payload);
                break;

            case 'component-deleted':
                this.handleComponentDeleted(payload);
                break;

            case 'connection-added':
                this.handleConnectionAdded(payload);
                break;

            case 'connection-deleted':
                this.handleConnectionDeleted(payload);
                break;

            case 'state-imported':
                this.handleStateImported(payload);
                break;

            case 'state-cleared':
                this.handleStateCleared();
                break;

            case 'state-changed':
                this.handleStateChanged(payload);
                break;

            default:
                console.log('Unhandled state change:', changeType, payload);
        }
    }

    /**
     * Handle Component Added
     */
    handleComponentAdded(payload) {
        const { component } = payload;

        // Add to canvas (wenn noch nicht vorhanden)
        if (!this.canvas.components.has(component.id)) {
            this.canvas.addComponent(component);
        }

        // Tabs werden nur geöffnet wenn User klickt
    }

    /**
     * Handle Component Updated
     */
    handleComponentUpdated(payload) {
        const { componentId, component } = payload;

        // Update canvas
        this.canvas.updateComponent(componentId, component.config);

        // Update tabs (wenn offen)
        this.tabs.updateComponent(componentId, component);
    }

    /**
     * Handle Component Deleted
     */
    handleComponentDeleted(payload) {
        const { componentId } = payload;

        // Remove from canvas
        this.canvas.removeComponent(componentId);

        // Remove from tabs
        this.tabs.removeComponent(componentId);
    }

    /**
     * Handle Connection Added
     */
    handleConnectionAdded(payload) {
        const { connection } = payload;

        // Add to canvas
        this.canvas.addConnection(
            connection.from,
            connection.to,
            connection.data
        );
    }

    /**
     * Handle Connection Deleted
     */
    handleConnectionDeleted(payload) {
        const { connectionId } = payload;

        // Remove from canvas
        this.canvas.removeConnection(connectionId);
    }

    /**
     * Handle State Imported
     */
    handleStateImported(payload) {
        const { state } = payload;

        // Load into canvas
        this.canvas.loadFromJSON(state);

        // Clear tabs
        this.tabs.loadFromJSON(state);
    }

    /**
     * Handle State Cleared
     */
    handleStateCleared() {
        // Clear canvas
        this.canvas.cy.elements().remove();
        this.canvas.components.clear();

        // Clear tabs
        this.tabs.activeComponents.clear();
        this.tabs.activeTab = null;
        this.tabs.renderTabHeaders();
    }

    /**
     * Handle State Changed (Undo/Redo)
     */
    handleStateChanged(payload) {
        const { action } = payload;

        // Reload entire state into canvas and tabs
        this.canvas.loadFromJSON(this.state.state);
        this.tabs.loadFromJSON(this.state.state);

        console.log(`State ${action === 'undo' ? 'rückgängig gemacht' : 'wiederhergestellt'}`);
    }

    /**
     * Handle Component Drop (from palette)
     */
    handleComponentDrop(type, position) {
        const name = this.generateDefaultName(type);
        const config = this.getDefaultConfig(type);

        // Add to state (triggers canvas + tabs update)
        this.state.addComponent(type, name, config, position);
    }

    /**
     * Generate Default Name
     */
    generateDefaultName(type) {
        const existing = this.state.getComponentsByType(type);
        const count = existing.length + 1;

        const names = {
            vpc: 'VPC',
            subnet: 'Subnet',
            ec2: 'Web Server',
            rds: 'Database',
            s3: 'Bucket',
            lambda: 'Function',
            alb: 'Load Balancer',
            ecs: 'Container Service',
            dynamodb: 'Table',
            elasticache: 'Cache',
            igw: 'Internet Gateway',
            nat: 'NAT Gateway',
            sg: 'Security Group',
            nacl: 'Network ACL',
            iam: 'IAM Role'
        };

        return `${names[type] || type} ${count}`;
    }

    /**
     * Get Default Config
     */
    getDefaultConfig(type) {
        const defaults = {
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
                hasPublicIp: false
            },
            rds: {
                engine: 'postgres',
                engineVersion: '14.7',
                instanceClass: 'db.t3.micro',
                allocatedStorage: 20
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

        return defaults[type] || {};
    }

    /**
     * Create Connection (z.B. von Canvas aus)
     */
    createConnection(fromId, toId, connectionData = {}) {
        // Validate components exist
        if (!this.state.hasComponent(fromId) || !this.state.hasComponent(toId)) {
            console.error('Cannot create connection: Component not found');
            return;
        }

        // Add to state (triggers canvas update)
        this.state.addConnection(fromId, toId, connectionData);
    }

    /**
     * Delete Connection
     */
    deleteConnection(connectionId) {
        this.state.deleteConnection(connectionId);
    }

    /**
     * Auto-assign IPs for components
     */
    autoAssignIPs() {
        // Finde alle EC2/RDS Komponenten ohne IP
        const components = this.state.getAllComponents();
        const subnets = this.state.getComponentsByType('subnet');

        if (subnets.length === 0) {
            alert('Erstelle zuerst ein Subnet, um IPs zuzuweisen');
            return;
        }

        const defaultSubnet = subnets[0];

        components.forEach(comp => {
            if ((comp.type === 'ec2' || comp.type === 'rds') && !comp.config.privateIp) {
                const ip = this.state.allocatePrivateIP(comp.id, defaultSubnet.id);
                this.state.updateComponent(comp.id, {
                    config: { privateIp: ip }
                });
            }
        });
    }

    /**
     * Export architecture to JSON
     */
    exportJSON() {
        const json = this.state.export();
        const blob = new Blob([json], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.download = `architecture-${Date.now()}.json`;
        link.href = url;
        link.click();
        URL.revokeObjectURL(url);
    }

    /**
     * Import architecture from JSON file
     */
    async importJSON(file) {
        try {
            const text = await file.text();
            this.state.import(text);
            console.log('Architektur erfolgreich importiert');
        } catch (error) {
            console.error('Fehler beim Importieren:', error);
            alert('Fehler beim Importieren der Architektur');
        }
    }

    /**
     * Save to localStorage
     */
    saveToLocalStorage(key = 'architecture-autosave') {
        const json = this.state.export();
        localStorage.setItem(key, json);
        console.log('Architektur in LocalStorage gespeichert');
    }

    /**
     * Load from localStorage
     */
    loadFromLocalStorage(key = 'architecture-autosave') {
        const json = localStorage.getItem(key);
        if (json) {
            this.state.import(json);
            console.log('Architektur aus LocalStorage geladen');
            return true;
        }
        return false;
    }

    /**
     * Validate architecture
     */
    validate() {
        const errors = this.state.validate();
        if (errors.length > 0) {
            console.warn('Validation Errors:', errors);
            alert(`Validierungsfehler gefunden:\n\n${errors.join('\n')}`);
            return false;
        }
        return true;
    }

    /**
     * Get statistics
     */
    getStats() {
        const components = this.state.getAllComponents();
        const connections = this.state.getAllConnections();

        const stats = {
            totalComponents: components.length,
            totalConnections: connections.length,
            componentsByType: {},
            ipAllocations: Object.keys(this.state.state.ipAllocations).length
        };

        components.forEach(comp => {
            stats.componentsByType[comp.type] = (stats.componentsByType[comp.type] || 0) + 1;
        });

        return stats;
    }
}
