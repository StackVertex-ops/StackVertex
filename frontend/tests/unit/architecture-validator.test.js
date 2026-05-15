/**
 * OverCloud - Architecture Validator Unit Tests
 *
 * Unit Tests für den Architecture Validator
 */

import { describe, it, expect } from '@playwright/test';
import {
    validateArchitecture,
    validateJSONSyntax,
    findIsolatedComponents,
    findCircularDependencies
} from '../../src/js/lib/architecture-validator.js';

describe('Architecture Validator - Basic Validation', () => {
    it('should validate a complete architecture successfully', () => {
        const architecture = {
            version: '1.0.0',
            metadata: {
                name: 'Test Architecture',
                provider: 'aws',
                region: 'eu-central-1'
            },
            requirements: {
                functional: {
                    workload_type: 'web_application'
                }
            },
            architecture: {
                components: [
                    {
                        id: 'vpc-1',
                        type: 'network',
                        name: 'Main VPC',
                        provider_service: 'vpc'
                    },
                    {
                        id: 'ec2-1',
                        type: 'compute',
                        name: 'Web Server',
                        provider_service: 'ec2'
                    }
                ],
                relationships: [
                    {
                        from: 'ec2-1',
                        to: 'vpc-1',
                        type: 'network'
                    }
                ]
            }
        };

        const result = validateArchitecture(architecture);

        expect(result.valid).toBe(true);
        expect(result.errors).toHaveLength(0);
    });

    it('should fail validation when version is missing', () => {
        const architecture = {
            metadata: {
                name: 'Test',
                provider: 'aws'
            },
            architecture: {
                components: []
            }
        };

        const result = validateArchitecture(architecture);

        expect(result.valid).toBe(false);
        expect(result.errors).toContain('Feld "version" fehlt');
    });

    it('should fail validation when metadata is missing', () => {
        const architecture = {
            version: '1.0.0',
            architecture: {
                components: []
            }
        };

        const result = validateArchitecture(architecture);

        expect(result.valid).toBe(false);
        expect(result.errors).toContain('Feld "metadata" fehlt');
    });

    it('should fail validation when architecture is missing', () => {
        const architecture = {
            version: '1.0.0',
            metadata: {
                name: 'Test',
                provider: 'aws'
            }
        };

        const result = validateArchitecture(architecture);

        expect(result.valid).toBe(false);
        expect(result.errors).toContain('Feld "architecture" fehlt');
    });

    it('should add warnings when optional fields are missing', () => {
        const architecture = {
            version: '1.0.0',
            metadata: {
                name: 'Test',
                provider: 'aws'
            },
            architecture: {
                components: []
            }
        };

        const result = validateArchitecture(architecture);

        expect(result.warnings).toContain('Feld "requirements" fehlt - empfohlen für Dokumentation');
    });
});

describe('Architecture Validator - Component Validation', () => {
    it('should fail when component has no id', () => {
        const architecture = {
            version: '1.0.0',
            metadata: { name: 'Test', provider: 'aws' },
            architecture: {
                components: [
                    {
                        type: 'compute',
                        provider_service: 'ec2'
                    }
                ]
            }
        };

        const result = validateArchitecture(architecture);

        expect(result.valid).toBe(false);
        expect(result.errors.some(e => e.includes('Feld "id" fehlt'))).toBe(true);
    });

    it('should fail when component has duplicate id', () => {
        const architecture = {
            version: '1.0.0',
            metadata: { name: 'Test', provider: 'aws' },
            architecture: {
                components: [
                    { id: 'vpc-1', type: 'network', provider_service: 'vpc' },
                    { id: 'vpc-1', type: 'network', provider_service: 'vpc' }
                ]
            }
        };

        const result = validateArchitecture(architecture);

        expect(result.valid).toBe(false);
        expect(result.errors.some(e => e.includes('Duplicate ID'))).toBe(true);
    });

    it('should warn when component has no name', () => {
        const architecture = {
            version: '1.0.0',
            metadata: { name: 'Test', provider: 'aws' },
            architecture: {
                components: [
                    { id: 'vpc-1', type: 'network', provider_service: 'vpc' }
                ]
            }
        };

        const result = validateArchitecture(architecture);

        expect(result.warnings.some(w => w.includes('Kein "name" definiert'))).toBe(true);
    });
});

describe('Architecture Validator - Relationship Validation', () => {
    it('should fail when relationship references unknown component', () => {
        const architecture = {
            version: '1.0.0',
            metadata: { name: 'Test', provider: 'aws' },
            architecture: {
                components: [
                    { id: 'vpc-1', type: 'network', provider_service: 'vpc' }
                ],
                relationships: [
                    { from: 'vpc-1', to: 'ec2-999', type: 'network' }
                ]
            }
        };

        const result = validateArchitecture(architecture);

        expect(result.valid).toBe(false);
        expect(result.errors.some(e => e.includes('referenziert unbekannte Component'))).toBe(true);
    });

    it('should fail when relationship has no from field', () => {
        const architecture = {
            version: '1.0.0',
            metadata: { name: 'Test', provider: 'aws' },
            architecture: {
                components: [
                    { id: 'vpc-1', type: 'network', provider_service: 'vpc' }
                ],
                relationships: [
                    { to: 'vpc-1', type: 'network' }
                ]
            }
        };

        const result = validateArchitecture(architecture);

        expect(result.valid).toBe(false);
        expect(result.errors.some(e => e.includes('Feld "from" fehlt'))).toBe(true);
    });
});

describe('JSON Syntax Validator', () => {
    it('should validate valid JSON', () => {
        const jsonString = '{"version": "1.0.0", "metadata": {"name": "Test"}}';
        const result = validateJSONSyntax(jsonString);

        expect(result.valid).toBe(true);
        expect(result.json).toBeDefined();
        expect(result.json.version).toBe('1.0.0');
    });

    it('should fail on invalid JSON', () => {
        const jsonString = '{"version": "1.0.0", "metadata": {';
        const result = validateJSONSyntax(jsonString);

        expect(result.valid).toBe(false);
        expect(result.error).toBeDefined();
    });

    it('should fail on malformed JSON', () => {
        const jsonString = '{"version": 1.0.0}'; // Missing quotes
        const result = validateJSONSyntax(jsonString);

        expect(result.valid).toBe(false);
    });
});

describe('Isolated Components Finder', () => {
    it('should find components with no relationships', () => {
        const architecture = {
            architecture: {
                components: [
                    { id: 'vpc-1', type: 'network', provider_service: 'vpc' },
                    { id: 'ec2-1', type: 'compute', provider_service: 'ec2' },
                    { id: 's3-1', type: 'storage', provider_service: 's3' }
                ],
                relationships: [
                    { from: 'ec2-1', to: 'vpc-1', type: 'network' }
                ]
            }
        };

        const isolated = findIsolatedComponents(architecture);

        expect(isolated).toHaveLength(1);
        expect(isolated).toContain('s3-1');
    });

    it('should return empty array when all components are connected', () => {
        const architecture = {
            architecture: {
                components: [
                    { id: 'vpc-1', type: 'network', provider_service: 'vpc' },
                    { id: 'ec2-1', type: 'compute', provider_service: 'ec2' }
                ],
                relationships: [
                    { from: 'ec2-1', to: 'vpc-1', type: 'network' }
                ]
            }
        };

        const isolated = findIsolatedComponents(architecture);

        expect(isolated).toHaveLength(0);
    });

    it('should handle architecture with no relationships', () => {
        const architecture = {
            architecture: {
                components: [
                    { id: 'vpc-1', type: 'network', provider_service: 'vpc' }
                ]
            }
        };

        const isolated = findIsolatedComponents(architecture);

        expect(isolated).toHaveLength(1);
        expect(isolated).toContain('vpc-1');
    });
});

describe('Circular Dependencies Finder', () => {
    it('should detect simple circular dependency', () => {
        const architecture = {
            architecture: {
                relationships: [
                    { from: 'a', to: 'b', type: 'depends' },
                    { from: 'b', to: 'a', type: 'depends' }
                ]
            }
        };

        const circles = findCircularDependencies(architecture);

        expect(circles.length).toBeGreaterThan(0);
    });

    it('should detect complex circular dependency', () => {
        const architecture = {
            architecture: {
                relationships: [
                    { from: 'a', to: 'b', type: 'depends' },
                    { from: 'b', to: 'c', type: 'depends' },
                    { from: 'c', to: 'a', type: 'depends' }
                ]
            }
        };

        const circles = findCircularDependencies(architecture);

        expect(circles.length).toBeGreaterThan(0);
    });

    it('should return empty for acyclic graph', () => {
        const architecture = {
            architecture: {
                relationships: [
                    { from: 'a', to: 'b', type: 'depends' },
                    { from: 'b', to: 'c', type: 'depends' }
                ]
            }
        };

        const circles = findCircularDependencies(architecture);

        expect(circles).toHaveLength(0);
    });
});
