/**
 * OverCloud - Infrastructure Canvas Unit Tests
 *
 * Tests für die Cytoscape-basierte Canvas-Komponente
 */

import { describe, it, expect, beforeEach, vi } from '@playwright/test';

// Mock Cytoscape
const mockCytoscape = vi.fn(() => ({
    add: vi.fn(),
    remove: vi.fn(),
    getElementById: vi.fn((id) => ({
        data: vi.fn(),
        position: vi.fn(),
        remove: vi.fn()
    })),
    nodes: vi.fn(() => []),
    edges: vi.fn(() => []),
    json: vi.fn(() => ({})),
    layout: vi.fn(() => ({
        run: vi.fn()
    })),
    on: vi.fn(),
    fit: vi.fn(),
    zoom: vi.fn(),
    center: vi.fn()
}));

vi.mock('cytoscape', () => ({
    default: mockCytoscape
}));

// Import after mocking
const { InfrastructureCanvas } = await import('../../src/js/components/InfrastructureCanvas.js');

describe('InfrastructureCanvas - Initialization', () => {
    let container;

    beforeEach(() => {
        // Setup DOM container
        container = document.createElement('div');
        container.id = 'test-canvas';
        document.body.appendChild(container);
        mockCytoscape.mockClear();
    });

    it('should initialize with container element', () => {
        const canvas = new InfrastructureCanvas('test-canvas');

        expect(canvas.container).toBe(container);
        expect(canvas.cy).toBeDefined();
        expect(mockCytoscape).toHaveBeenCalledWith(
            expect.objectContaining({
                container: container
            })
        );
    });

    it('should register node click handler', () => {
        const onNodeClick = vi.fn();
        const canvas = new InfrastructureCanvas('test-canvas', onNodeClick);

        expect(canvas.onNodeClick).toBe(onNodeClick);
    });

    it('should register edge click handler', () => {
        const onEdgeClick = vi.fn();
        const canvas = new InfrastructureCanvas('test-canvas', null, onEdgeClick);

        expect(canvas.onEdgeClick).toBe(onEdgeClick);
    });

    it('should initialize empty components map', () => {
        const canvas = new InfrastructureCanvas('test-canvas');

        expect(canvas.components).toBeInstanceOf(Map);
        expect(canvas.components.size).toBe(0);
    });
});

describe('InfrastructureCanvas - Component Management', () => {
    let canvas;

    beforeEach(() => {
        const container = document.createElement('div');
        container.id = 'test-canvas';
        document.body.appendChild(container);
        canvas = new InfrastructureCanvas('test-canvas');
    });

    it('should add VPC component', () => {
        const component = {
            id: 'vpc-1',
            type: 'vpc',
            name: 'Main VPC',
            config: {
                cidr: '10.0.0.0/16'
            }
        };

        canvas.addComponent(component);

        expect(canvas.components.has('vpc-1')).toBe(true);
        expect(canvas.cy.add).toHaveBeenCalled();
    });

    it('should add EC2 component', () => {
        const component = {
            id: 'ec2-1',
            type: 'ec2',
            name: 'Web Server',
            config: {
                instance_type: 't3.micro'
            }
        };

        canvas.addComponent(component);

        expect(canvas.components.has('ec2-1')).toBe(true);
        expect(canvas.cy.add).toHaveBeenCalled();
    });

    it('should update component configuration', () => {
        const component = {
            id: 'vpc-1',
            type: 'vpc',
            name: 'Main VPC',
            config: {
                cidr: '10.0.0.0/16'
            }
        };

        canvas.addComponent(component);

        const updatedConfig = {
            cidr: '10.1.0.0/16',
            enable_dns: true
        };

        canvas.updateComponent('vpc-1', updatedConfig);

        const storedComponent = canvas.components.get('vpc-1');
        expect(storedComponent.config.cidr).toBe('10.1.0.0/16');
        expect(storedComponent.config.enable_dns).toBe(true);
    });

    it('should remove component', () => {
        const component = {
            id: 'vpc-1',
            type: 'vpc',
            name: 'Main VPC',
            config: {}
        };

        canvas.addComponent(component);
        canvas.removeComponent('vpc-1');

        expect(canvas.components.has('vpc-1')).toBe(false);
    });

    it('should get component by id', () => {
        const component = {
            id: 'vpc-1',
            type: 'vpc',
            name: 'Main VPC',
            config: {}
        };

        canvas.addComponent(component);
        const retrieved = canvas.getComponent('vpc-1');

        expect(retrieved).toBeDefined();
        expect(retrieved.id).toBe('vpc-1');
        expect(retrieved.type).toBe('vpc');
    });

    it('should return null for non-existent component', () => {
        const retrieved = canvas.getComponent('non-existent');

        expect(retrieved).toBeNull();
    });
});

describe('InfrastructureCanvas - Connections', () => {
    let canvas;

    beforeEach(() => {
        const container = document.createElement('div');
        container.id = 'test-canvas';
        document.body.appendChild(container);
        canvas = new InfrastructureCanvas('test-canvas');
    });

    it('should add connection between components', () => {
        canvas.addComponent({
            id: 'vpc-1',
            type: 'vpc',
            name: 'VPC',
            config: {}
        });

        canvas.addComponent({
            id: 'ec2-1',
            type: 'ec2',
            name: 'Server',
            config: {}
        });

        canvas.addConnection({
            id: 'conn-1',
            from: 'ec2-1',
            to: 'vpc-1',
            type: 'network'
        });

        expect(canvas.cy.add).toHaveBeenCalledWith(
            expect.objectContaining({
                group: 'edges',
                data: expect.objectContaining({
                    id: 'conn-1',
                    source: 'ec2-1',
                    target: 'vpc-1'
                })
            })
        );
    });

    it('should remove connection', () => {
        canvas.addConnection({
            id: 'conn-1',
            from: 'ec2-1',
            to: 'vpc-1',
            type: 'network'
        });

        canvas.removeConnection('conn-1');

        expect(canvas.cy.getElementById).toHaveBeenCalledWith('conn-1');
    });
});

describe('InfrastructureCanvas - Layout', () => {
    let canvas;

    beforeEach(() => {
        const container = document.createElement('div');
        container.id = 'test-canvas';
        document.body.appendChild(container);
        canvas = new InfrastructureCanvas('test-canvas');
    });

    it('should run auto-layout', () => {
        canvas.addComponent({
            id: 'vpc-1',
            type: 'vpc',
            name: 'VPC',
            config: {}
        });

        canvas.runLayout('breadthfirst');

        expect(canvas.cy.layout).toHaveBeenCalledWith(
            expect.objectContaining({
                name: 'breadthfirst'
            })
        );
    });

    it('should fit canvas to content', () => {
        canvas.fit();

        expect(canvas.cy.fit).toHaveBeenCalled();
    });

    it('should center canvas', () => {
        canvas.center();

        expect(canvas.cy.center).toHaveBeenCalled();
    });

    it('should zoom to specific level', () => {
        canvas.zoom(1.5);

        expect(canvas.cy.zoom).toHaveBeenCalledWith(1.5);
    });
});

describe('InfrastructureCanvas - Export/Import', () => {
    let canvas;

    beforeEach(() => {
        const container = document.createElement('div');
        container.id = 'test-canvas';
        document.body.appendChild(container);
        canvas = new InfrastructureCanvas('test-canvas');
    });

    it('should export architecture JSON', () => {
        canvas.addComponent({
            id: 'vpc-1',
            type: 'vpc',
            name: 'Main VPC',
            config: { cidr: '10.0.0.0/16' }
        });

        const exported = canvas.exportJSON();

        expect(exported).toHaveProperty('version');
        expect(exported.architecture.components).toHaveLength(1);
        expect(exported.architecture.components[0].id).toBe('vpc-1');
    });

    it('should import architecture JSON', () => {
        const architectureJson = {
            version: '1.0.0',
            metadata: {
                name: 'Test Architecture',
                provider: 'aws'
            },
            architecture: {
                components: [
                    {
                        id: 'vpc-1',
                        type: 'vpc',
                        name: 'Main VPC',
                        config: { cidr: '10.0.0.0/16' }
                    }
                ],
                relationships: []
            }
        };

        canvas.importJSON(architectureJson);

        expect(canvas.components.size).toBe(1);
        expect(canvas.components.has('vpc-1')).toBe(true);
    });

    it('should clear all components on import', () => {
        canvas.addComponent({
            id: 'old-component',
            type: 'vpc',
            name: 'Old',
            config: {}
        });

        const newJson = {
            version: '1.0.0',
            metadata: { name: 'New', provider: 'aws' },
            architecture: {
                components: [],
                relationships: []
            }
        };

        canvas.importJSON(newJson);

        expect(canvas.components.has('old-component')).toBe(false);
    });
});
