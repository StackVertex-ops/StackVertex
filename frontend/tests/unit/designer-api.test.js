/**
 * OverCloud - Designer API Unit Tests
 *
 * Tests für die Designer API Client Module
 */

import { describe, it, expect, beforeEach, vi } from '@playwright/test';

// Mock APIClient
class MockAPIClient {
    constructor() {
        this.get = vi.fn();
        this.post = vi.fn();
    }
}

// Mock the api-client module
vi.mock('../../src/js/lib/api-client.js', () => ({
    APIClient: MockAPIClient
}));

// Import after mocking
const {
    saveDesignerArchitecture,
    loadDesignerArchitecture,
    generateTerraform,
    validateArchitecture,
    downloadTerraformZip,
    triggerTerraformDownload
} = await import('../../src/js/api/designer.js');

describe('Designer API - Save Architecture', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('should save architecture with correct endpoint', async () => {
        const mockResponse = {
            success: true,
            architecture_id: 'arch-123'
        };

        MockAPIClient.prototype.post.mockResolvedValue(mockResponse);

        const data = {
            name: 'Test Architecture',
            description: 'Test description',
            architecture_json: {
                version: '1.0.0',
                architecture: {
                    components: []
                }
            }
        };

        const result = await saveDesignerArchitecture(data);

        expect(MockAPIClient.prototype.post).toHaveBeenCalledWith(
            '/api/v1/designer/save',
            data
        );
        expect(result.architecture_id).toBe('arch-123');
    });

    it('should handle save errors', async () => {
        MockAPIClient.prototype.post.mockRejectedValue(
            new Error('Network error')
        );

        const data = {
            name: 'Test',
            architecture_json: {}
        };

        await expect(saveDesignerArchitecture(data)).rejects.toThrow('Network error');
    });

    it('should include owner if provided', async () => {
        MockAPIClient.prototype.post.mockResolvedValue({ success: true });

        const data = {
            name: 'Test',
            description: 'Desc',
            architecture_json: {},
            owner: 'user-123'
        };

        await saveDesignerArchitecture(data);

        expect(MockAPIClient.prototype.post).toHaveBeenCalledWith(
            '/api/v1/designer/save',
            expect.objectContaining({
                owner: 'user-123'
            })
        );
    });
});

describe('Designer API - Load Architecture', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('should load architecture by id', async () => {
        const mockArchitecture = {
            version: '1.0.0',
            metadata: {
                name: 'Test Architecture',
                provider: 'aws'
            },
            architecture: {
                components: [
                    { id: 'vpc-1', type: 'vpc', name: 'VPC' }
                ]
            }
        };

        MockAPIClient.prototype.get.mockResolvedValue(mockArchitecture);

        const result = await loadDesignerArchitecture('arch-123');

        expect(MockAPIClient.prototype.get).toHaveBeenCalledWith(
            '/api/v1/designer/load/arch-123'
        );
        expect(result.architecture.components).toHaveLength(1);
    });

    it('should handle load errors', async () => {
        MockAPIClient.prototype.get.mockRejectedValue(
            new Error('Architecture not found')
        );

        await expect(
            loadDesignerArchitecture('non-existent')
        ).rejects.toThrow('Architecture not found');
    });
});

describe('Designer API - Generate Terraform', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('should generate terraform from architecture', async () => {
        const mockResponse = {
            files: {
                'main.tf': 'resource "aws_vpc" "main" { ... }',
                'variables.tf': 'variable "region" { ... }'
            },
            component_count: 5,
            warnings: []
        };

        MockAPIClient.prototype.post.mockResolvedValue(mockResponse);

        const architectureJson = {
            version: '1.0.0',
            architecture: {
                components: [
                    { id: 'vpc-1', type: 'vpc', name: 'VPC' }
                ]
            }
        };

        const result = await generateTerraform(architectureJson);

        expect(MockAPIClient.prototype.post).toHaveBeenCalledWith(
            '/api/v1/designer/generate-terraform',
            { architecture_json: architectureJson }
        );
        expect(result.files).toHaveProperty('main.tf');
        expect(result.component_count).toBe(5);
    });

    it('should handle generation errors', async () => {
        MockAPIClient.prototype.post.mockRejectedValue(
            new Error('Generation failed')
        );

        await expect(
            generateTerraform({})
        ).rejects.toThrow('Generation failed');
    });

    it('should return warnings if present', async () => {
        const mockResponse = {
            files: { 'main.tf': '...' },
            component_count: 1,
            warnings: ['No S3 bucket encryption specified']
        };

        MockAPIClient.prototype.post.mockResolvedValue(mockResponse);

        const result = await generateTerraform({});

        expect(result.warnings).toHaveLength(1);
        expect(result.warnings[0]).toContain('encryption');
    });
});

describe('Designer API - Validate Architecture', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('should validate valid architecture', async () => {
        const mockResponse = {
            valid: true,
            errors: [],
            warnings: [],
            component_count: 3,
            connection_count: 2
        };

        MockAPIClient.prototype.post.mockResolvedValue(mockResponse);

        const architectureJson = {
            version: '1.0.0',
            architecture: {
                components: [
                    { id: 'vpc-1', type: 'vpc', name: 'VPC' }
                ]
            }
        };

        const result = await validateArchitecture(architectureJson);

        expect(result.valid).toBe(true);
        expect(result.errors).toHaveLength(0);
        expect(result.component_count).toBe(3);
    });

    it('should return validation errors for invalid architecture', async () => {
        const mockResponse = {
            valid: false,
            errors: [
                'Component vpc-1 missing required field: cidr',
                'Relationship references unknown component: ec2-999'
            ],
            warnings: [],
            component_count: 2,
            connection_count: 1
        };

        MockAPIClient.prototype.post.mockResolvedValue(mockResponse);

        const result = await validateArchitecture({});

        expect(result.valid).toBe(false);
        expect(result.errors).toHaveLength(2);
        expect(result.errors[0]).toContain('cidr');
    });

    it('should return warnings for suboptimal configuration', async () => {
        const mockResponse = {
            valid: true,
            errors: [],
            warnings: [
                'S3 bucket public access not explicitly disabled',
                'No backup policy configured for RDS'
            ],
            component_count: 2,
            connection_count: 0
        };

        MockAPIClient.prototype.post.mockResolvedValue(mockResponse);

        const result = await validateArchitecture({});

        expect(result.valid).toBe(true);
        expect(result.warnings).toHaveLength(2);
    });

    it('should handle validation errors', async () => {
        MockAPIClient.prototype.post.mockRejectedValue(
            new Error('Validation service unavailable')
        );

        await expect(
            validateArchitecture({})
        ).rejects.toThrow('Validation service unavailable');
    });
});

describe('Designer API - Download Terraform', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        global.JSZip = class {
            constructor() {
                this.files = {};
            }
            file(name, content) {
                this.files[name] = content;
            }
            async generateAsync() {
                return new Blob(['mock-zip'], { type: 'application/zip' });
            }
        };
    });

    it('should create ZIP from terraform files', async () => {
        const mockTerraformResponse = {
            files: {
                'main.tf': 'resource "aws_vpc" "main" { ... }',
                'variables.tf': 'variable "region" { ... }'
            },
            component_count: 2,
            warnings: []
        };

        MockAPIClient.prototype.post.mockResolvedValue(mockTerraformResponse);

        const architectureJson = { version: '1.0.0' };
        const blob = await downloadTerraformZip(architectureJson);

        expect(blob).toBeInstanceOf(Blob);
        expect(blob.type).toBe('application/zip');
    });

    it('should throw error if JSZip not loaded', async () => {
        delete global.JSZip;

        const mockTerraformResponse = {
            files: { 'main.tf': '...' }
        };

        MockAPIClient.prototype.post.mockResolvedValue(mockTerraformResponse);

        await expect(
            downloadTerraformZip({})
        ).rejects.toThrow('JSZip library not loaded');
    });

    it('should trigger browser download', async () => {
        const mockBlob = new Blob(['test'], { type: 'application/zip' });

        // Mock URL.createObjectURL
        global.URL.createObjectURL = vi.fn(() => 'blob:mock-url');
        global.URL.revokeObjectURL = vi.fn();

        // Mock document.createElement
        const mockLink = {
            href: '',
            download: '',
            click: vi.fn()
        };
        const originalCreateElement = document.createElement;
        document.createElement = vi.fn((tag) => {
            if (tag === 'a') return mockLink;
            return originalCreateElement.call(document, tag);
        });

        // Mock appendChild/removeChild
        document.body.appendChild = vi.fn();
        document.body.removeChild = vi.fn();

        const mockTerraformResponse = {
            files: { 'main.tf': '...' }
        };
        MockAPIClient.prototype.post.mockResolvedValue(mockTerraformResponse);

        await triggerTerraformDownload({}, 'my-terraform.zip');

        expect(mockLink.download).toBe('my-terraform.zip');
        expect(mockLink.click).toHaveBeenCalled();
        expect(global.URL.revokeObjectURL).toHaveBeenCalledWith('blob:mock-url');
    });

    it('should use default filename if not provided', async () => {
        const mockLink = {
            href: '',
            download: '',
            click: vi.fn()
        };
        document.createElement = vi.fn(() => mockLink);
        document.body.appendChild = vi.fn();
        document.body.removeChild = vi.fn();
        global.URL.createObjectURL = vi.fn(() => 'blob:mock');
        global.URL.revokeObjectURL = vi.fn();

        const mockTerraformResponse = {
            files: { 'main.tf': '...' }
        };
        MockAPIClient.prototype.post.mockResolvedValue(mockTerraformResponse);

        await triggerTerraformDownload({});

        expect(mockLink.download).toBe('terraform.zip');
    });
});
