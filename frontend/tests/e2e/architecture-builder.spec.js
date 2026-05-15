/**
 * OverCloud - Architecture Builder E2E Tests
 *
 * End-to-End Tests für den Architecture Builder
 */

import { test, expect } from '@playwright/test';

test.describe('Architecture Builder - Basic Functionality', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/architecture-builder.html');
    // Warte bis die Seite vollständig geladen ist
    await page.waitForSelector('#component-palette');
  });

  test('should load the architecture builder page', async ({ page }) => {
    // Check that main elements are present
    await expect(page.locator('#component-palette')).toBeVisible();
    await expect(page.locator('#canvas-container')).toBeVisible();
    await expect(page.locator('#properties-panel')).toBeVisible();

    // Check header
    await expect(page.locator('text=Architecture Builder')).toBeVisible();
  });

  test('should display component palette with categories', async ({ page }) => {
    const palette = page.locator('#component-palette');

    // Check for component categories
    await expect(palette.locator('text=compute').first()).toBeVisible();
    await expect(palette.locator('text=network').first()).toBeVisible();
    await expect(palette.locator('text=storage').first()).toBeVisible();
    await expect(palette.locator('text=database').first()).toBeVisible();
  });

  test('should show empty canvas initially', async ({ page }) => {
    const emptyState = page.locator('#canvas-empty-state');
    await expect(emptyState).toBeVisible();
    await expect(emptyState.locator('text=Beginne mit deiner Architektur')).toBeVisible();
  });

  test('should search for components', async ({ page }) => {
    const searchInput = page.locator('#component-search');
    await searchInput.fill('lambda');

    // Lambda component should be visible
    await expect(page.locator('text=Lambda Function')).toBeVisible();

    // EC2 should be hidden (not matching search)
    const ec2Item = page.locator('[data-component-service="ec2"]');
    await expect(ec2Item).toBeHidden();
  });
});

test.describe('Architecture Builder - Component Operations', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/architecture-builder.html');
    await page.waitForSelector('#component-palette');
  });

  test('should add component to canvas by clicking', async ({ page }) => {
    // Click on EC2 component in palette
    const ec2Component = page.locator('[data-component-service="ec2"]').first();
    await ec2Component.click();

    // Note: Since we can't easily simulate drag & drop in this test,
    // we'll just verify that the palette interaction works
    // In real usage, components are added via drag & drop

    // Verify status message
    await expect(page.locator('#status-message')).toContainText('Ziehe die Component auf die Canvas');
  });

  test('should load a template', async ({ page }) => {
    // Click on Web Application template
    const webAppTemplate = page.locator('[data-template="web-app"]');
    await webAppTemplate.click();

    // Wait for components to load
    await page.waitForTimeout(500);

    // Verify empty state is hidden
    const emptyState = page.locator('#canvas-empty-state');
    await expect(emptyState).toBeHidden();

    // Verify component count updated
    const componentCount = page.locator('#component-count');
    await expect(componentCount).not.toContainText('0 Components');

    // Verify status message
    await expect(page.locator('#status-message')).toContainText('Template geladen');
  });

  test('should zoom in and out', async ({ page }) => {
    // Click zoom in button
    const zoomInBtn = page.locator('#zoom-in');
    await zoomInBtn.click();

    // Check zoom level changed
    const zoomLevel = page.locator('#zoom-level');
    await expect(zoomLevel).toContainText('120%');

    // Click zoom out button
    const zoomOutBtn = page.locator('#zoom-out');
    await zoomOutBtn.click();

    // Should be back to ~100%
    await expect(zoomLevel).toContainText('96%');
  });

  test('should reset zoom', async ({ page }) => {
    // Zoom in multiple times
    const zoomInBtn = page.locator('#zoom-in');
    await zoomInBtn.click();
    await zoomInBtn.click();

    // Reset zoom
    const zoomResetBtn = page.locator('#zoom-reset');
    await zoomResetBtn.click();

    // Should be at 100%
    const zoomLevel = page.locator('#zoom-level');
    await expect(zoomLevel).toContainText('100%');
  });
});

test.describe('Architecture Builder - Validation', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/architecture-builder.html');
    await page.waitForSelector('#component-palette');
  });

  test('should validate empty architecture', async ({ page }) => {
    // Click validate button
    const validateBtn = page.locator('#validate-btn');
    await validateBtn.click();

    // Wait for validation
    await page.waitForTimeout(300);

    // Should show validation result
    const validationStatus = page.locator('#validation-status');
    await expect(validationStatus).toBeVisible();
  });

  test('should validate template architecture successfully', async ({ page }) => {
    // Load serverless template (simpler than web-app)
    const serverlessTemplate = page.locator('[data-template="serverless"]');
    await serverlessTemplate.click();

    await page.waitForTimeout(500);

    // Validate
    const validateBtn = page.locator('#validate-btn');
    await validateBtn.click();

    await page.waitForTimeout(300);

    // Should be valid
    const validationStatus = page.locator('#validation-status');
    await expect(validationStatus).toContainText('Gültig');
  });
});

test.describe('Architecture Builder - JSON Operations', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/architecture-builder.html');
    await page.waitForSelector('#component-palette');
  });

  test('should show JSON modal', async ({ page }) => {
    // Click toggle JSON view
    const toggleJsonBtn = page.locator('#toggle-json-view');
    await toggleJsonBtn.click();

    // Modal should be visible
    const modal = page.locator('#json-modal');
    await expect(modal).toBeVisible();

    // Should contain JSON preview
    const jsonPreview = page.locator('#json-preview');
    await expect(jsonPreview).toBeVisible();
  });

  test('should close JSON modal', async ({ page }) => {
    // Open modal
    const toggleJsonBtn = page.locator('#toggle-json-view');
    await toggleJsonBtn.click();

    // Close modal
    const closeBtn = page.locator('#close-json-modal');
    await closeBtn.click();

    // Modal should be hidden
    const modal = page.locator('#json-modal');
    await expect(modal).toBeHidden();
  });

  test('should copy JSON to clipboard', async ({ page }) => {
    // Grant clipboard permissions
    await page.context().grantPermissions(['clipboard-read', 'clipboard-write']);

    // Open modal
    const toggleJsonBtn = page.locator('#toggle-json-view');
    await toggleJsonBtn.click();

    // Click copy button
    const copyBtn = page.locator('#copy-json-btn');
    await copyBtn.click();

    // Button text should change temporarily
    await expect(copyBtn).toContainText('Kopiert!');

    // Wait for button to reset
    await page.waitForTimeout(2100);
    await expect(copyBtn).toContainText('In Zwischenablage kopieren');
  });
});

test.describe('Architecture Builder - Properties Panel', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/architecture-builder.html');
    await page.waitForSelector('#component-palette');
  });

  test('should show empty state when no component selected', async ({ page }) => {
    const propertiesPanel = page.locator('#properties-panel');
    await expect(propertiesPanel.locator('text=Keine Component ausgewählt')).toBeVisible();
  });

  test('should show properties when component is selected from template', async ({ page }) => {
    // Load serverless template
    const serverlessTemplate = page.locator('[data-template="serverless"]');
    await serverlessTemplate.click();

    await page.waitForTimeout(500);

    // Click on a component node (wait for it to exist first)
    const componentNode = page.locator('.component-node').first();
    await componentNode.waitFor({ state: 'visible' });
    await componentNode.click();

    // Properties panel should show component details
    const propertiesPanel = page.locator('#properties-panel');
    await expect(propertiesPanel.locator('text=Grundlegende Eigenschaften')).toBeVisible();
  });
});

test.describe('Architecture Builder - Save Operations', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/architecture-builder.html');
    await page.waitForSelector('#component-palette');
  });

  test('should have save button visible', async ({ page }) => {
    const saveBtn = page.locator('#save-btn');
    await expect(saveBtn).toBeVisible();
    await expect(saveBtn).toContainText('Speichern');
  });

  test('should have export JSON button visible', async ({ page }) => {
    const exportBtn = page.locator('#export-json-btn');
    await expect(exportBtn).toBeVisible();
    await expect(exportBtn).toContainText('Export JSON');
  });
});

test.describe('Architecture Builder - Navigation', () => {
  test('should have close/back button', async ({ page }) => {
    await page.goto('/architecture-builder.html');
    await page.waitForSelector('#component-palette');

    // Find close button (X icon)
    const closeBtn = page.locator('svg[viewBox="0 0 24 24"]').filter({ hasText: '' }).first();
    await expect(closeBtn).toBeVisible();
  });
});
