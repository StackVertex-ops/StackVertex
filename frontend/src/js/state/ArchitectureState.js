/**
 * Central State Manager
 *
 * Single source of truth für die Architektur
 * Alle Components, Connections und Settings werden im JSON State gespeichert
 */

export class ArchitectureState {
    constructor() {
        this.state = {
            version: '1.0.0',
            metadata: {
                name: 'Unbenannte Architektur',
                description: '',
                createdAt: new Date().toISOString(),
                updatedAt: new Date().toISOString()
            },
            components: {},
            connections: [],
            ipAllocations: {} // Verfolge IP-Zuweisungen
        };

        this.listeners = [];
        this.history = []; // Für Undo/Redo
        this.historyIndex = -1;
    }

    /**
     * Abonniere State-Änderungen
     */
    subscribe(listener) {
        this.listeners.push(listener);
        return () => {
            this.listeners = this.listeners.filter(l => l !== listener);
        };
    }

    /**
     * Benachrichtige alle Listeners über State-Änderung
     */
    notify(changeType, payload) {
        this.listeners.forEach(listener => {
            listener(changeType, payload, this.state);
        });
    }

    /**
     * Füge Component hinzu
     */
    addComponent(type, name, config = {}, position = null) {
        const id = this.generateId(type);

        const component = {
            id,
            type,
            name,
            config: {
                ...config,
                createdAt: new Date().toISOString()
            },
            position: position || this.getDefaultPosition(type)
        };

        this.state.components[id] = component;
        this.saveToHistory();
        this.notify('component-added', { component });

        return id;
    }

    /**
     * Aktualisiere Component
     */
    updateComponent(componentId, updates) {
        const component = this.state.components[componentId];
        if (!component) return;

        // Merge updates
        if (updates.name !== undefined) {
            component.name = updates.name;
        }
        if (updates.config) {
            Object.assign(component.config, updates.config);
        }
        if (updates.position) {
            component.position = updates.position;
        }

        this.state.metadata.updatedAt = new Date().toISOString();
        this.saveToHistory();
        this.notify('component-updated', { componentId, component });
    }

    /**
     * Lösche Component
     */
    deleteComponent(componentId) {
        const component = this.state.components[componentId];
        if (!component) return;

        // Entferne Component
        delete this.state.components[componentId];

        // Entferne Connections, die diese Component betreffen
        this.state.connections = this.state.connections.filter(
            conn => conn.from !== componentId && conn.to !== componentId
        );

        this.saveToHistory();
        this.notify('component-deleted', { componentId, component });
    }

    /**
     * Füge Connection hinzu
     */
    addConnection(fromId, toId, connectionData = {}) {
        const connection = {
            id: `${fromId}-${toId}`,
            from: fromId,
            to: toId,
            data: connectionData
        };

        this.state.connections.push(connection);
        this.saveToHistory();
        this.notify('connection-added', { connection });

        return connection.id;
    }

    /**
     * Lösche Connection
     */
    deleteConnection(connectionId) {
        const index = this.state.connections.findIndex(c => c.id === connectionId);
        if (index === -1) return;

        const connection = this.state.connections[index];
        this.state.connections.splice(index, 1);

        this.saveToHistory();
        this.notify('connection-deleted', { connectionId, connection });
    }

    /**
     * Allokiere private IP aus Subnet-Range
     */
    allocatePrivateIP(componentId, subnetId) {
        const subnet = this.state.components[subnetId];
        if (!subnet || subnet.type !== 'subnet') return null;

        const cidr = subnet.config.cidr;
        const [ip, prefix] = cidr.split('/');
        const ipParts = ip.split('.').map(Number);

        // Starte bei .10 (AWS reserviert .0-.9 für System-Nutzung)
        let offset = 10;
        const allocated = Object.values(this.state.ipAllocations)
            .filter(alloc => alloc.subnetId === subnetId)
            .map(alloc => alloc.ip);

        // Finde nächste verfügbare IP
        while (true) {
            const candidateIP = `${ipParts[0]}.${ipParts[1]}.${ipParts[2]}.${ipParts[3] + offset}`;
            if (!allocated.includes(candidateIP)) {
                this.state.ipAllocations[componentId] = {
                    ip: candidateIP,
                    subnetId: subnetId,
                    allocatedAt: new Date().toISOString()
                };
                return candidateIP;
            }
            offset++;
        }
    }

    /**
     * Hole Component nach ID
     */
    getComponent(componentId) {
        return this.state.components[componentId];
    }

    /**
     * Hole Components nach Typ
     */
    getComponentsByType(type) {
        return Object.values(this.state.components).filter(c => c.type === type);
    }

    /**
     * Hole Components nach Kategorie
     */
    getComponentsByCategory(category) {
        const typeMap = {
            network: ['vpc', 'subnet', 'igw', 'nat', 'routetable'],
            security: ['sg', 'nacl', 'iam', 'kms'],
            data: ['rds', 'dynamodb', 's3', 'elasticache', 'efs'],
            computing: ['ec2', 'lambda', 'ecs', 'alb', 'nlb']
        };

        const types = typeMap[category] || [];
        return Object.values(this.state.components).filter(c => types.includes(c.type));
    }

    /**
     * Exportiere nach JSON
     */
    export() {
        return JSON.stringify(this.state, null, 2);
    }

    /**
     * Importiere von JSON
     */
    import(jsonString) {
        try {
            const imported = JSON.parse(jsonString);
            this.state = imported;
            this.saveToHistory();
            this.notify('state-imported', { state: this.state });
        } catch (error) {
            console.error('Fehler beim Importieren von JSON:', error);
        }
    }

    /**
     * Undo
     */
    undo() {
        if (this.historyIndex > 0) {
            this.historyIndex--;
            this.state = JSON.parse(JSON.stringify(this.history[this.historyIndex]));
            this.notify('state-changed', { action: 'undo' });
        }
    }

    /**
     * Redo
     */
    redo() {
        if (this.historyIndex < this.history.length - 1) {
            this.historyIndex++;
            this.state = JSON.parse(JSON.stringify(this.history[this.historyIndex]));
            this.notify('state-changed', { action: 'redo' });
        }
    }

    /**
     * Speichere in History (für Undo/Redo)
     */
    saveToHistory() {
        // Entferne History nach aktuellem Index
        this.history = this.history.slice(0, this.historyIndex + 1);

        // Füge aktuellen State hinzu
        this.history.push(JSON.parse(JSON.stringify(this.state)));
        this.historyIndex++;

        // Begrenze History-Größe
        if (this.history.length > 50) {
            this.history.shift();
            this.historyIndex--;
        }
    }

    /**
     * Generiere eindeutige ID
     */
    generateId(type) {
        const timestamp = Date.now().toString(36);
        const random = Math.random().toString(36).substr(2, 5);
        return `${type}-${timestamp}-${random}`;
    }

    /**
     * Hole Default-Position für Component-Typ
     */
    getDefaultPosition(type) {
        // Intelligente Positionierung basierend auf Typ
        const positions = {
            vpc: { x: 400, y: 200 },
            subnet: { x: 450, y: 300 },
            ec2: { x: 500, y: 400 },
            rds: { x: 700, y: 400 },
            alb: { x: 350, y: 400 },
            lambda: { x: 600, y: 400 },
            s3: { x: 800, y: 300 },
            dynamodb: { x: 750, y: 500 },
            igw: { x: 300, y: 200 },
            nat: { x: 500, y: 250 },
            sg: { x: 550, y: 350 },
            nacl: { x: 600, y: 350 },
            iam: { x: 650, y: 200 }
        };

        return positions[type] || { x: 300, y: 300 };
    }

    /**
     * Hole alle Components
     */
    getAllComponents() {
        return Object.values(this.state.components);
    }

    /**
     * Hole alle Connections
     */
    getAllConnections() {
        return this.state.connections;
    }

    /**
     * Prüfe ob Component existiert
     */
    hasComponent(componentId) {
        return componentId in this.state.components;
    }

    /**
     * Prüfe ob Connection existiert
     */
    hasConnection(fromId, toId) {
        return this.state.connections.some(
            conn => conn.from === fromId && conn.to === toId
        );
    }

    /**
     * Hole Metadata
     */
    getMetadata() {
        return this.state.metadata;
    }

    /**
     * Update Metadata
     */
    updateMetadata(updates) {
        Object.assign(this.state.metadata, updates);
        this.state.metadata.updatedAt = new Date().toISOString();
        this.saveToHistory();
        this.notify('metadata-updated', { metadata: this.state.metadata });
    }

    /**
     * Clear State (für neue Architektur)
     */
    clear() {
        this.state = {
            version: '1.0.0',
            metadata: {
                name: 'Unbenannte Architektur',
                description: '',
                createdAt: new Date().toISOString(),
                updatedAt: new Date().toISOString()
            },
            components: {},
            connections: [],
            ipAllocations: {}
        };

        this.history = [];
        this.historyIndex = -1;
        this.saveToHistory();
        this.notify('state-cleared', {});
    }

    /**
     * Validiere State
     */
    validate() {
        const errors = [];

        // Prüfe ob alle Connections gültige Components referenzieren
        this.state.connections.forEach(conn => {
            if (!this.hasComponent(conn.from)) {
                errors.push(`Connection ${conn.id} referenziert nicht-existente Component: ${conn.from}`);
            }
            if (!this.hasComponent(conn.to)) {
                errors.push(`Connection ${conn.id} referenziert nicht-existente Component: ${conn.to}`);
            }
        });

        // Prüfe CIDR-Überlappungen bei Subnets
        const subnets = this.getComponentsByType('subnet');
        for (let i = 0; i < subnets.length; i++) {
            for (let j = i + 1; j < subnets.length; j++) {
                if (this.cidrOverlap(subnets[i].config.cidr, subnets[j].config.cidr)) {
                    errors.push(`Subnet CIDR Überlappung: ${subnets[i].name} (${subnets[i].config.cidr}) und ${subnets[j].name} (${subnets[j].config.cidr})`);
                }
            }
        }

        return errors;
    }

    /**
     * Prüfe CIDR-Überlappung
     */
    cidrOverlap(cidr1, cidr2) {
        // Vereinfachte Überlappungsprüfung
        // In Production würde man eine richtige CIDR-Library verwenden
        const [ip1] = cidr1.split('/');
        const [ip2] = cidr2.split('/');

        return ip1 === ip2;
    }
}
