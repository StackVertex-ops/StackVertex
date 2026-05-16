/**
 * OverCloud - Infrastructure Designer E2E Tests
 *
 * Integration Tests für den kompletten Designer-Flow
 */

import { test, expect } from '@playwright/test';

test.describe('Infrastructure Designer - Full Flow', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('http://localhost:5173/infrastructure-designer.html');
        await page.waitForLoadState('networkidle');
    });

    test('should load designer page with all components', async ({ page }) => {
        // Check page title
        await expect(page).toHaveTitle(/Infrastructure Designer/);

        // Check main canvas exists
        const canvas = page.locator('#infrastructure-canvas');
        await expect(canvas).toBeVisible();

        // Check component palette exists
        const palette = page.locator('#component-palette');
        await expect(palette).toBeVisible();

        // Check tab system exists
        const tabContainer = page.locator('#tab-headers');
        await expect(tabContainer).toBeVisible();
    });

    test('should display component palette with AWS resources', async ({ page }) => {
        // Check VPC component
        const vpcComponent = page.locator('[data-component-type="vpc"]');
        await expect(vpcComponent).toBeVisible();
        await expect(vpcComponent).toContainText('VPC');

        // Check EC2 component
        const ec2Component = page.locator('[data-component-type="ec2"]');
        await expect(ec2Component).toBeVisible();
        await expect(ec2Component).toContainText('EC2');

        // Check RDS component
        const rdsComponent = page.locator('[data-component-type="rds"]');
        await expect(rdsComponent).toBeVisible();
        await expect(rdsComponent).toContainText('RDS');

        // Check S3 component
        const s3Component = page.locator('[data-component-type="s3"]');
        await expect(s3Component).toBeVisible();
        await expect(s3Component).toContainText('S3');
    });

    test('should add VPC component to canvas', async ({ page }) => {
        // Drag VPC from palette to canvas
        const vpcComponent = page.locator('[data-component-type="vpc"]');
        const canvas = page.locator('#infrastructure-canvas');

        await vpcComponent.dragTo(canvas, {
            targetPosition: { x: 200, y: 150 }
        });

        // Wait for component to be added
        await page.waitForTimeout(500);

        // Check if component appears in canvas
        const canvasNode = page.locator('#infrastructure-canvas [data-id^="vpc-"]');
        await expect(canvasNode).toBeVisible();
    });

    test('should open tab when component is added', async ({ page }) => {
        // Add VPC component
        const vpcComponent = page.locator('[data-component-type="vpc"]');
        const canvas = page.locator('#infrastructure-canvas');

        await vpcComponent.dragTo(canvas);
        await page.waitForTimeout(500);

        // Check if tab opened
        const tab = page.locator('#tab-headers [data-tab-id^="vpc-"]');
        await expect(tab).toBeVisible();
        await expect(tab).toContainText('VPC');
    });

    test('should display configuration form in tab', async ({ page }) => {
        // Add VPC component
        const vpcComponent = page.locator('[data-component-type="vpc"]');
        const canvas = page.locator('#infrastructure-canvas');
        await vpcComponent.dragTo(canvas);
        await page.waitForTimeout(500);

        // Check configuration form
        const configForm = page.locator('#tab-content form');
        await expect(configForm).toBeVisible();

        // Check VPC-specific fields
        await expect(page.locator('input[name="name"]')).toBeVisible();
        await expect(page.locator('input[name="cidr"]')).toBeVisible();
        await expect(page.locator('select[name="region"]')).toBeVisible();
    });

    test('should update component configuration', async ({ page }) => {
        // Add VPC component
        const vpcComponent = page.locator('[data-component-type="vpc"]');
        const canvas = page.locator('#infrastructure-canvas');
        await vpcComponent.dragTo(canvas);
        await page.waitForTimeout(500);

        // Fill in configuration
        await page.fill('input[name="name"]', 'Production VPC');
        await page.fill('input[name="cidr"]', '10.0.0.0/16');
        await page.selectOption('select[name="region"]', 'eu-central-1');

        // Wait for auto-save or click save button
        const saveButton = page.locator('button:has-text("Save")');
        if (await saveButton.isVisible()) {
            await saveButton.click();
        }

        await page.waitForTimeout(500);

        // Verify configuration saved (check canvas node label)
        const canvasNode = page.locator('#infrastructure-canvas [data-id^="vpc-"]');
        await expect(canvasNode).toContainText('Production VPC');
    });

    test('should add multiple components', async ({ page }) => {
        const canvas = page.locator('#infrastructure-canvas');

        // Add VPC
        const vpcComponent = page.locator('[data-component-type="vpc"]');
        await vpcComponent.dragTo(canvas, {
            targetPosition: { x: 200, y: 150 }
        });
        await page.waitForTimeout(300);

        // Add EC2
        const ec2Component = page.locator('[data-component-type="ec2"]');
        await ec2Component.dragTo(canvas, {
            targetPosition: { x: 400, y: 200 }
        });
        await page.waitForTimeout(300);

        // Add RDS
        const rdsComponent = page.locator('[data-component-type="rds"]');
        await rdsComponent.dragTo(canvas, {
            targetPosition: { x: 600, y: 250 }
        });
        await page.waitForTimeout(300);

        // Check all components present
        await expect(page.locator('#infrastructure-canvas [data-id^="vpc-"]')).toBeVisible();
        await expect(page.locator('#infrastructure-canvas [data-id^="ec2-"]')).toBeVisible();
        await expect(page.locator('#infrastructure-canvas [data-id^="rds-"]')).toBeVisible();

        // Check all tabs opened
        await expect(page.locator('#tab-headers [data-tab-id^="vpc-"]')).toBeVisible();
        await expect(page.locator('#tab-headers [data-tab-id^="ec2-"]')).toBeVisible();
        await expect(page.locator('#tab-headers [data-tab-id^="rds-"]')).toBeVisible();
    });

    test('should switch between tabs', async ({ page }) => {
        const canvas = page.locator('#infrastructure-canvas');

        // Add VPC and EC2
        await page.locator('[data-component-type="vpc"]').dragTo(canvas);
        await page.waitForTimeout(300);
        await page.locator('[data-component-type="ec2"]').dragTo(canvas);
        await page.waitForTimeout(300);

        // Click on VPC tab
        const vpcTab = page.locator('#tab-headers [data-tab-id^="vpc-"]');
        await vpcTab.click();

        // Verify VPC configuration shown
        await expect(page.locator('#tab-content')).toContainText('VPC');
        await expect(page.locator('input[name="cidr"]')).toBeVisible();

        // Click on EC2 tab
        const ec2Tab = page.locator('#tab-headers [data-tab-id^="ec2-"]');
        await ec2Tab.click();

        // Verify EC2 configuration shown
        await expect(page.locator('#tab-content')).toContainText('EC2');
        await expect(page.locator('select[name="instance_type"]')).toBeVisible();
    });

    test('should close tab', async ({ page }) => {
        const canvas = page.locator('#infrastructure-canvas');

        // Add VPC
        await page.locator('[data-component-type="vpc"]').dragTo(canvas);
        await page.waitForTimeout(500);

        // Click close button on tab
        const closeButton = page.locator('#tab-headers [data-tab-id^="vpc-"] [data-action="close"]');
        await closeButton.click();

        // Verify tab removed
        await expect(page.locator('#tab-headers [data-tab-id^="vpc-"]')).not.toBeVisible();

        // Note: Component may or may not be removed from canvas depending on design decision
    });

    test('should click canvas node to open tab', async ({ page }) => {
        const canvas = page.locator('#infrastructure-canvas');

        // Add VPC and EC2
        await page.locator('[data-component-type="vpc"]').dragTo(canvas);
        await page.waitForTimeout(300);
        await page.locator('[data-component-type="ec2"]').dragTo(canvas);
        await page.waitForTimeout(300);

        // Close EC2 tab
        const ec2TabClose = page.locator('#tab-headers [data-tab-id^="ec2-"] [data-action="close"]');
        await ec2TabClose.click();
        await page.waitForTimeout(200);

        // Click on EC2 node in canvas
        const ec2Node = page.locator('#infrastructure-canvas [data-id^="ec2-"]');
        await ec2Node.click();

        // Verify tab reopened
        await expect(page.locator('#tab-headers [data-tab-id^="ec2-"]')).toBeVisible();
    });

    test('should create connection between components', async ({ page }) => {
        const canvas = page.locator('#infrastructure-canvas');

        // Add VPC and EC2
        await page.locator('[data-component-type="vpc"]').dragTo(canvas, {
            targetPosition: { x: 200, y: 150 }
        });
        await page.waitForTimeout(300);

        await page.locator('[data-component-type="ec2"]').dragTo(canvas, {
            targetPosition: { x: 400, y: 200 }
        });
        await page.waitForTimeout(300);

        // Click connection mode button (if exists)
        const connectionModeButton = page.locator('button:has-text("Connect")');
        if (await connectionModeButton.isVisible()) {
            await connectionModeButton.click();
        }

        // Click EC2 node then VPC node to create connection
        await page.locator('#infrastructure-canvas [data-id^="ec2-"]').click();
        await page.locator('#infrastructure-canvas [data-id^="vpc-"]').click();

        // Wait for connection to be created
        await page.waitForTimeout(500);

        // Check if edge/connection appears
        const edge = page.locator('#infrastructure-canvas [data-id^="conn-"]');
        await expect(edge).toBeVisible();
    });

    test('should save architecture', async ({ page }) => {
        const canvas = page.locator('#infrastructure-canvas');

        // Add components
        await page.locator('[data-component-type="vpc"]').dragTo(canvas);
        await page.waitForTimeout(300);
        await page.locator('[data-component-type="ec2"]').dragTo(canvas);
        await page.waitForTimeout(300);

        // Configure VPC
        await page.fill('input[name="name"]', 'Production VPC');
        await page.fill('input[name="cidr"]', '10.0.0.0/16');

        // Click save button
        const saveButton = page.locator('button:has-text("Save Architecture")');
        await saveButton.click();

        // Fill save dialog
        await page.fill('input[name="architecture_name"]', 'My Architecture');
        await page.fill('textarea[name="architecture_description"]', 'Test architecture');

        // Confirm save
        const confirmButton = page.locator('button:has-text("Confirm")');
        await confirmButton.click();

        // Wait for success message
        await expect(page.locator('.success-message')).toBeVisible();
        await expect(page.locator('.success-message')).toContainText('saved successfully');
    });

    test('should validate architecture', async ({ page }) => {
        const canvas = page.locator('#infrastructure-canvas');

        // Add VPC without required configuration
        await page.locator('[data-component-type="vpc"]').dragTo(canvas);
        await page.waitForTimeout(300);

        // Click validate button
        const validateButton = page.locator('button:has-text("Validate")');
        await validateButton.click();

        // Wait for validation results
        await page.waitForTimeout(500);

        // Check validation panel appears
        const validationPanel = page.locator('#validation-results');
        await expect(validationPanel).toBeVisible();
    });

    test('should generate Terraform code', async ({ page }) => {
        const canvas = page.locator('#infrastructure-canvas');

        // Add and configure VPC
        await page.locator('[data-component-type="vpc"]').dragTo(canvas);
        await page.waitForTimeout(300);

        await page.fill('input[name="name"]', 'prod-vpc');
        await page.fill('input[name="cidr"]', '10.0.0.0/16');
        await page.selectOption('select[name="region"]', 'eu-central-1');

        // Click generate Terraform button
        const generateButton = page.locator('button:has-text("Generate Terraform")');
        await generateButton.click();

        // Wait for code generation
        await page.waitForTimeout(1000);

        // Check Terraform code panel
        const codePanel = page.locator('#terraform-code');
        await expect(codePanel).toBeVisible();

        // Verify code contains VPC resource
        const codeContent = await codePanel.textContent();
        expect(codeContent).toContain('resource "aws_vpc"');
        expect(codeContent).toContain('10.0.0.0/16');
    });

    test('should export Terraform as ZIP', async ({ page }) => {
        const canvas = page.locator('#infrastructure-canvas');

        // Add VPC
        await page.locator('[data-component-type="vpc"]').dragTo(canvas);
        await page.waitForTimeout(300);

        await page.fill('input[name="name"]', 'test-vpc');
        await page.fill('input[name="cidr"]', '10.0.0.0/16');

        // Listen for download event
        const downloadPromise = page.waitForEvent('download');

        // Click export button
        const exportButton = page.locator('button:has-text("Export Terraform")');
        await exportButton.click();

        // Wait for download
        const download = await downloadPromise;
        expect(download.suggestedFilename()).toMatch(/terraform.*\.zip/);
    });

    test('should load existing architecture', async ({ page }) => {
        // Click load button
        const loadButton = page.locator('button:has-text("Load Architecture")');
        await loadButton.click();

        // Select architecture from list (assuming there's a test architecture)
        const architectureItem = page.locator('[data-architecture-id="test-arch-1"]');
        if (await architectureItem.isVisible()) {
            await architectureItem.click();

            // Confirm load
            const confirmButton = page.locator('button:has-text("Load")');
            await confirmButton.click();

            // Wait for architecture to load
            await page.waitForTimeout(1000);

            // Verify components loaded
            const nodes = page.locator('#infrastructure-canvas [data-id]');
            await expect(nodes.first()).toBeVisible();
        }
    });

    test('should handle errors gracefully', async ({ page }) => {
        // Simulate network error by intercepting API call
        await page.route('**/api/v1/designer/save', route => {
            route.abort('failed');
        });

        const canvas = page.locator('#infrastructure-canvas');

        // Add VPC
        await page.locator('[data-component-type="vpc"]').dragTo(canvas);
        await page.waitForTimeout(300);

        // Try to save
        const saveButton = page.locator('button:has-text("Save Architecture")');
        await saveButton.click();

        await page.fill('input[name="architecture_name"]', 'Test');
        const confirmButton = page.locator('button:has-text("Confirm")');
        await confirmButton.click();

        // Check error message
        await expect(page.locator('.error-message')).toBeVisible();
        await expect(page.locator('.error-message')).toContainText('error');
    });
});

test.describe('Infrastructure Designer - Advanced Features', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('http://localhost:5173/infrastructure-designer.html');
        await page.waitForLoadState('networkidle');
    });

    test('should apply auto-layout', async ({ page }) => {
        const canvas = page.locator('#infrastructure-canvas');

        // Add multiple components
        await page.locator('[data-component-type="vpc"]').dragTo(canvas);
        await page.waitForTimeout(200);
        await page.locator('[data-component-type="ec2"]').dragTo(canvas);
        await page.waitForTimeout(200);
        await page.locator('[data-component-type="rds"]').dragTo(canvas);
        await page.waitForTimeout(200);

        // Click auto-layout button
        const layoutButton = page.locator('button:has-text("Auto Layout")');
        await layoutButton.click();

        await page.waitForTimeout(500);

        // Components should be positioned automatically
        // (Visual verification would be needed here)
    });

    test('should zoom and pan canvas', async ({ page }) => {
        const canvas = page.locator('#infrastructure-canvas');

        // Add component
        await page.locator('[data-component-type="vpc"]').dragTo(canvas);

        // Zoom in
        const zoomInButton = page.locator('button[data-action="zoom-in"]');
        if (await zoomInButton.isVisible()) {
            await zoomInButton.click();
            await page.waitForTimeout(200);
        }

        // Zoom out
        const zoomOutButton = page.locator('button[data-action="zoom-out"]');
        if (await zoomOutButton.isVisible()) {
            await zoomOutButton.click();
            await page.waitForTimeout(200);
        }

        // Fit to screen
        const fitButton = page.locator('button[data-action="fit"]');
        if (await fitButton.isVisible()) {
            await fitButton.click();
            await page.waitForTimeout(200);
        }
    });

    test('should search/filter components in palette', async ({ page }) => {
        // Type in search box
        const searchInput = page.locator('input[placeholder*="Search"]');
        if (await searchInput.isVisible()) {
            await searchInput.fill('ec2');

            // Only EC2 components should be visible
            await expect(page.locator('[data-component-type="ec2"]')).toBeVisible();
            await expect(page.locator('[data-component-type="s3"]')).not.toBeVisible();

            // Clear search
            await searchInput.clear();
            await expect(page.locator('[data-component-type="s3"]')).toBeVisible();
        }
    });

    test('should show component properties on hover', async ({ page }) => {
        const vpcComponent = page.locator('[data-component-type="vpc"]');

        // Hover over component
        await vpcComponent.hover();

        // Tooltip should appear
        const tooltip = page.locator('.component-tooltip');
        if (await tooltip.isVisible()) {
            await expect(tooltip).toContainText('VPC');
            await expect(tooltip).toContainText('Virtual Private Cloud');
        }
    });

    test('should undo/redo actions', async ({ page }) => {
        const canvas = page.locator('#infrastructure-canvas');

        // Add VPC
        await page.locator('[data-component-type="vpc"]').dragTo(canvas);
        await page.waitForTimeout(300);

        // Undo
        const undoButton = page.locator('button[data-action="undo"]');
        if (await undoButton.isVisible()) {
            await undoButton.click();
            await page.waitForTimeout(300);

            // Component should be removed
            await expect(page.locator('#infrastructure-canvas [data-id^="vpc-"]')).not.toBeVisible();

            // Redo
            const redoButton = page.locator('button[data-action="redo"]');
            await redoButton.click();
            await page.waitForTimeout(300);

            // Component should reappear
            await expect(page.locator('#infrastructure-canvas [data-id^="vpc-"]')).toBeVisible();
        }
    });
});
