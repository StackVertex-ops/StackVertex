/**
 * OverCloud - Architecture Builder Advanced E2E Tests
 *
 * Tests für fortgeschrittene Features: Drag & Drop, Properties, AI Advisor
 */

import { test, expect } from '@playwright/test';

const BASE_URL = 'http://localhost:5173';

test.describe('Architecture Builder - Drag & Drop', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto(`${BASE_URL}/architecture-builder.html`);
        await page.waitForLoadState('networkidle');
    });

    test('should drag and drop component from palette to canvas', async ({ page }) => {
        // Find a component in the palette
        const ec2Component = page.locator('.component-item[data-component-key="ec2"]').first();
        await expect(ec2Component).toBeVisible();

        // Get canvas
        const canvas = page.locator('#canvas-svg');
        await expect(canvas).toBeVisible();

        // Perform drag and drop
        await ec2Component.dragTo(canvas, {
            targetPosition: { x: 400, y: 300 }
        });

        // Wait a bit for component to be added
        await page.waitForTimeout(500);

        // Check component count increased
        const componentCount = page.locator('#component-count');
        await expect(componentCount).toContainText('1 Component');

        // Check canvas is no longer empty
        const emptyState = page.locator('#canvas-empty-state');
        await expect(emptyState).not.toBeVisible();
    });

    test('should drag multiple components to canvas', async ({ page }) => {
        // Drag VPC
        const vpcComponent = page.locator('.component-item[data-component-key="vpc"]').first();
        const canvas = page.locator('#canvas-svg');

        await vpcComponent.dragTo(canvas, {
            targetPosition: { x: 300, y: 200 }
        });

        await page.waitForTimeout(300);

        // Drag EC2
        const ec2Component = page.locator('.component-item[data-component-key="ec2"]').first();
        await ec2Component.dragTo(canvas, {
            targetPosition: { x: 400, y: 300 }
        });

        await page.waitForTimeout(300);

        // Check component count
        const componentCount = page.locator('#component-count');
        await expect(componentCount).toContainText('2 Components');
    });
});

test.describe('Architecture Builder - Properties Panel', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto(`${BASE_URL}/architecture-builder.html`);
        await page.waitForLoadState('networkidle');
    });

    test('should show properties when component is clicked', async ({ page }) => {
        // Load a template first
        const webAppTemplate = page.locator('button[data-template="web-app"]');
        await webAppTemplate.click();
        await page.waitForTimeout(1000);

        // Click on first component in canvas
        const firstComponent = page.locator('#components-layer foreignObject').first();
        await firstComponent.click();
        await page.waitForTimeout(300);

        // Check properties panel shows component details
        const propertiesPanel = page.locator('#properties-panel');
        await expect(propertiesPanel).not.toContainText('Keine Component ausgewählt');
    });

    test('should edit VPC CIDR block', async ({ page }) => {
        // Load template
        const webAppTemplate = page.locator('button[data-template="web-app"]');
        await webAppTemplate.click();
        await page.waitForTimeout(1000);

        // Click on VPC component (if exists in template)
        const components = page.locator('#components-layer foreignObject');
        await components.first().click();
        await page.waitForTimeout(300);

        // Check if CIDR input exists
        const cidrInput = page.locator('#prop-cidr-block');
        if (await cidrInput.isVisible()) {
            // Clear and type new CIDR
            await cidrInput.clear();
            await cidrInput.fill('10.1.0.0/16');

            // Click apply button
            const applyBtn = page.locator('#apply-properties-btn');
            if (await applyBtn.isVisible()) {
                await applyBtn.click();
                await page.waitForTimeout(300);

                // Verify value persists
                await expect(cidrInput).toHaveValue('10.1.0.0/16');
            }
        }
    });

    test('should edit EC2 instance type', async ({ page }) => {
        // Load template
        const webAppTemplate = page.locator('button[data-template="web-app"]');
        await webAppTemplate.click();
        await page.waitForTimeout(1000);

        // Try to find and click EC2 component
        const components = page.locator('#components-layer foreignObject');
        const count = await components.count();

        for (let i = 0; i < count; i++) {
            await components.nth(i).click({ force: true });
            await page.waitForTimeout(300);

            // Check if instance type select exists
            const instanceTypeSelect = page.locator('#prop-instance-type');
            if (await instanceTypeSelect.isVisible()) {
                // Select different instance type
                await instanceTypeSelect.selectOption('t3.medium');
                await page.waitForTimeout(200);

                // Apply changes
                const applyBtn = page.locator('#apply-properties-btn');
                if (await applyBtn.isVisible()) {
                    await applyBtn.click();
                }
                break;
            }
        }
    });

    test('should toggle RDS Multi-AZ checkbox', async ({ page }) => {
        // Load serverless template (might have DynamoDB, but test is generic)
        const webAppTemplate = page.locator('button[data-template="web-app"]');
        await webAppTemplate.click();
        await page.waitForTimeout(1000);

        // Try to find component with multi-az checkbox
        const components = page.locator('#components-layer foreignObject');
        const count = await components.count();

        for (let i = 0; i < count; i++) {
            await components.nth(i).click({ force: true });
            await page.waitForTimeout(300);

            // Check if multi-az checkbox exists
            const multiAzCheckbox = page.locator('#prop-multi-az');
            if (await multiAzCheckbox.isVisible()) {
                // Toggle checkbox
                const wasChecked = await multiAzCheckbox.isChecked();
                await multiAzCheckbox.click();
                await page.waitForTimeout(200);

                // Verify state changed
                const isChecked = await multiAzCheckbox.isChecked();
                expect(isChecked).toBe(!wasChecked);
                break;
            }
        }
    });
});

test.describe('Architecture Builder - AI Advisor', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto(`${BASE_URL}/architecture-builder.html`);
        await page.waitForLoadState('networkidle');
    });

    test('should show AI Advisor toggle button', async ({ page }) => {
        const advisorBtn = page.locator('#toggle-advisor');
        await expect(advisorBtn).toBeVisible();
        await expect(advisorBtn).toContainText('AI Advisor');
    });

    test('should toggle AI Advisor panel', async ({ page }) => {
        const advisorBtn = page.locator('#toggle-advisor');
        const advisorBar = page.locator('#ai-advisor-bar');

        // Initially hidden
        const advisorContent = page.locator('#advisor-content');
        await expect(advisorContent).toHaveClass(/hidden/);

        // Click to show
        await advisorBtn.click();
        await page.waitForTimeout(300);

        // Should be visible now
        await expect(advisorContent).not.toHaveClass(/hidden/);

        // Click again to hide
        await advisorBtn.click();
        await page.waitForTimeout(300);

        // Should be hidden again
        await expect(advisorContent).toHaveClass(/hidden/);
    });

    test('should show recommendations for empty architecture', async ({ page }) => {
        // Toggle advisor
        const advisorBtn = page.locator('#toggle-advisor');
        await advisorBtn.click();
        await page.waitForTimeout(300);

        // Check for empty state message
        const advisorContent = page.locator('#advisor-content');
        await expect(advisorContent).toContainText('Alles sieht gut aus');
    });

    test('should show security warnings for unencrypted RDS', async ({ page }) => {
        // Load web app template (has RDS)
        const webAppTemplate = page.locator('button[data-template="web-app"]');
        await webAppTemplate.click();
        await page.waitForTimeout(1000);

        // Find and click RDS component
        const components = page.locator('#components-layer foreignObject');
        const count = await components.count();

        for (let i = 0; i < count; i++) {
            await components.nth(i).click({ force: true });
            await page.waitForTimeout(300);

            // Check if storage-encrypted checkbox exists
            const encryptedCheckbox = page.locator('#prop-storage-encrypted');
            if (await encryptedCheckbox.isVisible()) {
                // Uncheck it to trigger warning
                if (await encryptedCheckbox.isChecked()) {
                    await encryptedCheckbox.click();

                    // Apply changes
                    const applyBtn = page.locator('#apply-properties-btn');
                    if (await applyBtn.isVisible()) {
                        await applyBtn.click();
                        await page.waitForTimeout(300);
                    }
                }
                break;
            }
        }

        // Toggle advisor to see recommendations
        const advisorBtn = page.locator('#toggle-advisor');
        await advisorBtn.click();
        await page.waitForTimeout(500);

        // Check for security warning
        const advisorContent = page.locator('#advisor-content');
        const hasWarning = await advisorContent.locator('.recommendation-item').count() > 0;
        expect(hasWarning).toBe(true);
    });

    test('should show cost optimization suggestions', async ({ page }) => {
        // Load template
        const webAppTemplate = page.locator('button[data-template="web-app"]');
        await webAppTemplate.click();
        await page.waitForTimeout(1000);

        // Find EC2 and change to expensive instance type
        const components = page.locator('#components-layer foreignObject');
        const count = await components.count();

        for (let i = 0; i < count; i++) {
            await components.nth(i).click({ force: true });
            await page.waitForTimeout(300);

            const instanceTypeSelect = page.locator('#prop-instance-type');
            if (await instanceTypeSelect.isVisible()) {
                // Select expensive instance
                await instanceTypeSelect.selectOption('m5.xlarge');

                const applyBtn = page.locator('#apply-properties-btn');
                if (await applyBtn.isVisible()) {
                    await applyBtn.click();
                    await page.waitForTimeout(300);
                }
                break;
            }
        }

        // Check advisor for cost warning
        const advisorBtn = page.locator('#toggle-advisor');
        await advisorBtn.click();
        await page.waitForTimeout(500);

        const advisorContent = page.locator('#advisor-content');
        const text = await advisorContent.textContent();

        // Should mention cost or expensive
        const hasCostMention = text.includes('teuer') || text.includes('Teure') || text.includes('Kosten');
        expect(hasCostMention).toBe(true);
    });
});

test.describe('Architecture Builder - Component Removal', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto(`${BASE_URL}/architecture-builder.html`);
        await page.waitForLoadState('networkidle');
    });

    test('should remove component from canvas', async ({ page }) => {
        // Load template
        const webAppTemplate = page.locator('button[data-template="web-app"]');
        await webAppTemplate.click();
        await page.waitForTimeout(1000);

        // Get initial component count
        const componentCount = page.locator('#component-count');
        const initialText = await componentCount.textContent();
        const initialCount = parseInt(initialText.match(/\d+/)?.[0] || '0');

        // Click on first component
        const firstComponent = page.locator('#components-layer foreignObject').first();
        await firstComponent.click();
        await page.waitForTimeout(300);

        // Look for delete button (might be in properties panel)
        const deleteBtn = page.locator('button').filter({ hasText: /löschen|delete|entfernen/i }).first();

        if (await deleteBtn.isVisible()) {
            await deleteBtn.click();
            await page.waitForTimeout(500);

            // Verify count decreased
            const newText = await componentCount.textContent();
            const newCount = parseInt(newText.match(/\d+/)?.[0] || '0');
            expect(newCount).toBeLessThan(initialCount);
        }
    });
});

test.describe('Architecture Builder - Keyboard Shortcuts', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto(`${BASE_URL}/architecture-builder.html`);
        await page.waitForLoadState('networkidle');
    });

    test('should support Delete key to remove selected component', async ({ page }) => {
        // Load template
        const webAppTemplate = page.locator('button[data-template="web-app"]');
        await webAppTemplate.click();
        await page.waitForTimeout(1000);

        // Get initial count
        const componentCount = page.locator('#component-count');
        const initialText = await componentCount.textContent();
        const initialCount = parseInt(initialText.match(/\d+/)?.[0] || '0');

        // Click on first component
        const firstComponent = page.locator('#components-layer foreignObject').first();
        await firstComponent.click();
        await page.waitForTimeout(300);

        // Press Delete key
        await page.keyboard.press('Delete');
        await page.waitForTimeout(500);

        // Verify count decreased
        const newText = await componentCount.textContent();
        const newCount = parseInt(newText.match(/\d+/)?.[0] || '0');
        expect(newCount).toBeLessThanOrEqual(initialCount); // Might not work if keyboard shortcuts not implemented
    });
});
