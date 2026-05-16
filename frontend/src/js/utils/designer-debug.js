/**
 * Designer Debug Helper
 *
 * Development-only utilities für schnelles Testen im Browser
 * Verfügbar via `window.designer` in der Console
 */

export function setupDebugHelpers(designerInstance) {
    if (import.meta.env.PROD) {
        return; // Nur in Development
    }

    window.designer = {
        // Referenzen zu allen Komponenten
        instance: designerInstance,
        canvas: designerInstance.canvas,
        palette: designerInstance.palette,
        tabs: designerInstance.tabs,
        state: designerInstance.architectureState,

        // Helper: VPC hinzufügen
        addVPC: (name = 'Test VPC', cidr = '10.0.0.0/16') => {
            const component = {
                id: `vpc-${Date.now()}`,
                type: 'vpc',
                name,
                config: {
                    cidr,
                    enableDnsHostnames: true,
                    enableDnsSupport: true
                },
                position: { x: 400, y: 200 }
            };
            designerInstance.canvas.addComponent(component);
            designerInstance.architectureState.components[component.id] = component;
            window.dispatchEvent(new CustomEvent('component-added', {
                detail: { component }
            }));
            return component.id;
        },

        // Helper: EC2 Instance hinzufügen
        addEC2: (name = 'Test EC2', instanceType = 't3.small') => {
            const component = {
                id: `ec2-${Date.now()}`,
                type: 'ec2',
                name,
                config: {
                    instanceType,
                    ami: 'ami-0c55b159cbfafe1f0',
                    hasPublicIp: false,
                    privateIp: null
                },
                position: { x: 400, y: 350 }
            };
            designerInstance.canvas.addComponent(component);
            designerInstance.architectureState.components[component.id] = component;
            window.dispatchEvent(new CustomEvent('component-added', {
                detail: { component }
            }));
            return component.id;
        },

        // Helper: RDS Database hinzufügen
        addRDS: (name = 'Test DB', engine = 'postgres') => {
            const component = {
                id: `rds-${Date.now()}`,
                type: 'rds',
                name,
                config: {
                    engine,
                    engineVersion: '14.7',
                    instanceClass: 'db.t3.micro',
                    privateIp: null
                },
                position: { x: 600, y: 350 }
            };
            designerInstance.canvas.addComponent(component);
            designerInstance.architectureState.components[component.id] = component;
            window.dispatchEvent(new CustomEvent('component-added', {
                detail: { component }
            }));
            return component.id;
        },

        // Helper: S3 Bucket hinzufügen
        addS3: (name = 'Test Bucket') => {
            const component = {
                id: `s3-${Date.now()}`,
                type: 's3',
                name,
                config: {
                    versioning: false,
                    encryption: true,
                    publicAccess: false
                },
                position: { x: 200, y: 200 }
            };
            designerInstance.canvas.addComponent(component);
            designerInstance.architectureState.components[component.id] = component;
            window.dispatchEvent(new CustomEvent('component-added', {
                detail: { component }
            }));
            return component.id;
        },

        // Helper: Verbindung zwischen zwei Komponenten
        connect: (fromId, toId, label = 'connects') => {
            designerInstance.canvas.addConnection(fromId, toId, { label });
        },

        // Helper: Aktuellen State als JSON exportieren
        exportJSON: () => {
            const json = JSON.stringify(designerInstance.architectureState, null, 2);
            console.log(json);
            return designerInstance.architectureState;
        },

        // Helper: JSON kopieren in Zwischenablage
        copyJSON: async () => {
            const json = JSON.stringify(designerInstance.architectureState, null, 2);
            await navigator.clipboard.writeText(json);
            console.log('✓ JSON copied to clipboard');
            return json;
        },

        // Helper: Canvas leeren
        clear: () => {
            if (!confirm('Clear all components?')) return;

            designerInstance.architectureState.components = {};
            designerInstance.architectureState.connections = [];
            designerInstance.canvas.cy.elements().remove();
            designerInstance.tabs.tabs.forEach((_, tabId) => {
                designerInstance.tabs.closeTab(tabId);
            });
            console.log('✓ Canvas cleared');
        },

        // Helper: Alle Components auflisten
        listComponents: () => {
            const components = Object.values(designerInstance.architectureState.components);
            console.table(components.map(c => ({
                id: c.id,
                type: c.type,
                name: c.name,
                position: `${c.position.x},${c.position.y}`
            })));
            return components;
        },

        // Helper: Komponente nach ID finden
        getComponent: (id) => {
            return designerInstance.architectureState.components[id];
        },

        // Helper: Auto Layout anwenden
        autoLayout: () => {
            designerInstance.canvas.autoLayout();
            console.log('✓ Auto layout applied');
        },

        // Helper: Fit to view
        fit: () => {
            designerInstance.canvas.fit();
            console.log('✓ Fit to view');
        },

        // Helper: Beispiel-Architektur erstellen (VPC + EC2 + RDS)
        createExampleArchitecture: () => {
            const vpcId = window.designer.addVPC('Example VPC', '10.0.0.0/16');
            setTimeout(() => {
                const ec2Id = window.designer.addEC2('Web Server', 't3.small');
                setTimeout(() => {
                    const rdsId = window.designer.addRDS('Database', 'postgres');
                    setTimeout(() => {
                        window.designer.connect(ec2Id, rdsId, 'PostgreSQL:5432');
                        window.designer.autoLayout();
                        console.log('✓ Example architecture created');
                    }, 100);
                }, 100);
            }, 100);
        },

        // Helper: Demo-Architektur laden
        loadDemo: () => {
            window.location.href = '/infrastructure-designer.html?id=demo';
        }
    };

    console.log('%c🎨 Designer Debug Mode Active', 'font-size: 14px; font-weight: bold; color: #667eea;');
    console.log('%cTry these commands:', 'color: #888;');
    console.log('  designer.addVPC()           - Add a VPC');
    console.log('  designer.addEC2()           - Add an EC2 instance');
    console.log('  designer.addRDS()           - Add an RDS database');
    console.log('  designer.addS3()            - Add an S3 bucket');
    console.log('  designer.connect(a, b)      - Connect two components');
    console.log('  designer.exportJSON()       - Export current state');
    console.log('  designer.copyJSON()         - Copy JSON to clipboard');
    console.log('  designer.listComponents()   - List all components');
    console.log('  designer.clear()            - Clear canvas');
    console.log('  designer.createExampleArchitecture() - Create example');
    console.log('  designer.loadDemo()         - Load demo architecture');
}
