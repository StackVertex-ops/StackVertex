/**
 * OverCloud - Tab System Unit Tests
 *
 * Tests für die Tab-Management-Komponente des Infrastructure Designers
 */

import { describe, it, expect, beforeEach, vi } from '@playwright/test';
import { TabSystem } from '../../src/js/components/TabSystem.js';

describe('TabSystem - Initialization', () => {
    let headerContainer, contentContainer;

    beforeEach(() => {
        headerContainer = document.createElement('div');
        headerContainer.id = 'tab-headers';
        document.body.appendChild(headerContainer);

        contentContainer = document.createElement('div');
        contentContainer.id = 'tab-content';
        document.body.appendChild(contentContainer);
    });

    it('should initialize with container elements', () => {
        const tabSystem = new TabSystem('tab-headers', 'tab-content');

        expect(tabSystem.headerContainer).toBe(headerContainer);
        expect(tabSystem.contentContainer).toBe(contentContainer);
        expect(tabSystem.tabs).toBeInstanceOf(Map);
        expect(tabSystem.activeTabId).toBeNull();
    });

    it('should register tab change callback', () => {
        const onTabChange = vi.fn();
        const tabSystem = new TabSystem('tab-headers', 'tab-content', onTabChange);

        expect(tabSystem.onTabChange).toBe(onTabChange);
    });

    it('should register tab close callback', () => {
        const onTabClose = vi.fn();
        const tabSystem = new TabSystem('tab-headers', 'tab-content', null, onTabClose);

        expect(tabSystem.onTabClose).toBe(onTabClose);
    });
});

describe('TabSystem - Tab Management', () => {
    let tabSystem, onTabChange, onTabClose;

    beforeEach(() => {
        const headerContainer = document.createElement('div');
        headerContainer.id = 'tab-headers';
        document.body.appendChild(headerContainer);

        const contentContainer = document.createElement('div');
        contentContainer.id = 'tab-content';
        document.body.appendChild(contentContainer);

        onTabChange = vi.fn();
        onTabClose = vi.fn();
        tabSystem = new TabSystem('tab-headers', 'tab-content', onTabChange, onTabClose);
    });

    it('should open new tab for component', () => {
        const component = {
            id: 'vpc-1',
            type: 'vpc',
            name: 'Main VPC',
            config: {}
        };

        tabSystem.openTab(component);

        expect(tabSystem.tabs.has('vpc-1')).toBe(true);
        expect(tabSystem.activeTabId).toBe('vpc-1');
        expect(onTabChange).toHaveBeenCalledWith('vpc-1', component);
    });

    it('should not create duplicate tab', () => {
        const component = {
            id: 'vpc-1',
            type: 'vpc',
            name: 'Main VPC',
            config: {}
        };

        tabSystem.openTab(component);
        tabSystem.openTab(component);

        expect(tabSystem.tabs.size).toBe(1);
    });

    it('should activate existing tab when opened again', () => {
        const component1 = {
            id: 'vpc-1',
            type: 'vpc',
            name: 'VPC 1',
            config: {}
        };

        const component2 = {
            id: 'ec2-1',
            type: 'ec2',
            name: 'Server',
            config: {}
        };

        tabSystem.openTab(component1);
        tabSystem.openTab(component2);
        tabSystem.openTab(component1); // Reopen first tab

        expect(tabSystem.activeTabId).toBe('vpc-1');
        expect(onTabChange).toHaveBeenCalledTimes(3);
    });

    it('should close tab and remove from DOM', () => {
        const component = {
            id: 'vpc-1',
            type: 'vpc',
            name: 'Main VPC',
            config: {}
        };

        tabSystem.openTab(component);
        tabSystem.closeTab('vpc-1');

        expect(tabSystem.tabs.has('vpc-1')).toBe(false);
        expect(document.getElementById('tab-header-vpc-1')).toBeNull();
    });

    it('should trigger close callback on tab close', () => {
        const component = {
            id: 'vpc-1',
            type: 'vpc',
            name: 'Main VPC',
            config: {}
        };

        tabSystem.openTab(component);
        tabSystem.closeTab('vpc-1');

        expect(onTabClose).toHaveBeenCalledWith('vpc-1');
    });

    it('should activate next tab when closing active tab', () => {
        const component1 = {
            id: 'vpc-1',
            type: 'vpc',
            name: 'VPC 1',
            config: {}
        };

        const component2 = {
            id: 'ec2-1',
            type: 'ec2',
            name: 'Server',
            config: {}
        };

        tabSystem.openTab(component1);
        tabSystem.openTab(component2);
        tabSystem.closeTab('ec2-1');

        expect(tabSystem.activeTabId).toBe('vpc-1');
    });

    it('should clear active tab when last tab closed', () => {
        const component = {
            id: 'vpc-1',
            type: 'vpc',
            name: 'Main VPC',
            config: {}
        };

        tabSystem.openTab(component);
        tabSystem.closeTab('vpc-1');

        expect(tabSystem.activeTabId).toBeNull();
    });
});

describe('TabSystem - Tab Content Rendering', () => {
    let tabSystem;

    beforeEach(() => {
        const headerContainer = document.createElement('div');
        headerContainer.id = 'tab-headers';
        document.body.appendChild(headerContainer);

        const contentContainer = document.createElement('div');
        contentContainer.id = 'tab-content';
        document.body.appendChild(contentContainer);

        tabSystem = new TabSystem('tab-headers', 'tab-content');
    });

    it('should render VPC configuration form', () => {
        const component = {
            id: 'vpc-1',
            type: 'vpc',
            name: 'Main VPC',
            config: {
                cidr: '10.0.0.0/16'
            }
        };

        tabSystem.openTab(component);

        const content = tabSystem.contentContainer.innerHTML;
        expect(content).toContain('vpc');
        expect(content).toContain('10.0.0.0/16');
    });

    it('should render EC2 configuration form', () => {
        const component = {
            id: 'ec2-1',
            type: 'ec2',
            name: 'Web Server',
            config: {
                instance_type: 't3.micro'
            }
        };

        tabSystem.openTab(component);

        const content = tabSystem.contentContainer.innerHTML;
        expect(content).toContain('ec2');
        expect(content).toContain('t3.micro');
    });

    it('should update content when switching tabs', () => {
        const component1 = {
            id: 'vpc-1',
            type: 'vpc',
            name: 'VPC',
            config: {}
        };

        const component2 = {
            id: 'ec2-1',
            type: 'ec2',
            name: 'Server',
            config: {}
        };

        tabSystem.openTab(component1);
        tabSystem.openTab(component2);

        const content = tabSystem.contentContainer.innerHTML;
        expect(content).toContain('ec2');
    });
});

describe('TabSystem - Visual State', () => {
    let tabSystem;

    beforeEach(() => {
        const headerContainer = document.createElement('div');
        headerContainer.id = 'tab-headers';
        document.body.appendChild(headerContainer);

        const contentContainer = document.createElement('div');
        contentContainer.id = 'tab-content';
        document.body.appendChild(contentContainer);

        tabSystem = new TabSystem('tab-headers', 'tab-content');
    });

    it('should apply active styles to current tab', () => {
        const component = {
            id: 'vpc-1',
            type: 'vpc',
            name: 'Main VPC',
            config: {}
        };

        tabSystem.openTab(component);

        const header = document.getElementById('tab-header-vpc-1');
        expect(header.classList.contains('border-primary-500')).toBe(true);
        expect(header.classList.contains('text-primary-700')).toBe(true);
    });

    it('should remove active styles from inactive tabs', () => {
        const component1 = {
            id: 'vpc-1',
            type: 'vpc',
            name: 'VPC',
            config: {}
        };

        const component2 = {
            id: 'ec2-1',
            type: 'ec2',
            name: 'Server',
            config: {}
        };

        tabSystem.openTab(component1);
        tabSystem.openTab(component2);

        const header1 = document.getElementById('tab-header-vpc-1');
        expect(header1.classList.contains('border-primary-500')).toBe(false);
        expect(header1.classList.contains('text-gray-700')).toBe(true);
    });

    it('should show component icon in tab header', () => {
        const component = {
            id: 'vpc-1',
            type: 'vpc',
            name: 'Main VPC',
            config: {}
        };

        tabSystem.openTab(component);

        const header = document.getElementById('tab-header-vpc-1');
        expect(header.innerHTML).toContain('Main VPC');
    });

    it('should show close button in tab header', () => {
        const component = {
            id: 'vpc-1',
            type: 'vpc',
            name: 'Main VPC',
            config: {}
        };

        tabSystem.openTab(component);

        const header = document.getElementById('tab-header-vpc-1');
        const closeButton = header.querySelector('[data-action="close"]');
        expect(closeButton).toBeDefined();
    });
});

describe('TabSystem - Multiple Tabs', () => {
    let tabSystem;

    beforeEach(() => {
        const headerContainer = document.createElement('div');
        headerContainer.id = 'tab-headers';
        document.body.appendChild(headerContainer);

        const contentContainer = document.createElement('div');
        contentContainer.id = 'tab-content';
        document.body.appendChild(contentContainer);

        tabSystem = new TabSystem('tab-headers', 'tab-content');
    });

    it('should handle multiple open tabs', () => {
        const components = [
            { id: 'vpc-1', type: 'vpc', name: 'VPC', config: {} },
            { id: 'ec2-1', type: 'ec2', name: 'Server 1', config: {} },
            { id: 'ec2-2', type: 'ec2', name: 'Server 2', config: {} },
            { id: 'rds-1', type: 'rds', name: 'Database', config: {} }
        ];

        components.forEach(comp => tabSystem.openTab(comp));

        expect(tabSystem.tabs.size).toBe(4);
        expect(tabSystem.headerContainer.children.length).toBe(4);
    });

    it('should switch between multiple tabs', () => {
        const components = [
            { id: 'vpc-1', type: 'vpc', name: 'VPC', config: {} },
            { id: 'ec2-1', type: 'ec2', name: 'Server', config: {} }
        ];

        components.forEach(comp => tabSystem.openTab(comp));

        tabSystem.activateTab('vpc-1');
        expect(tabSystem.activeTabId).toBe('vpc-1');

        tabSystem.activateTab('ec2-1');
        expect(tabSystem.activeTabId).toBe('ec2-1');
    });

    it('should close tabs independently', () => {
        const components = [
            { id: 'vpc-1', type: 'vpc', name: 'VPC', config: {} },
            { id: 'ec2-1', type: 'ec2', name: 'Server', config: {} }
        ];

        components.forEach(comp => tabSystem.openTab(comp));

        tabSystem.closeTab('vpc-1');

        expect(tabSystem.tabs.has('vpc-1')).toBe(false);
        expect(tabSystem.tabs.has('ec2-1')).toBe(true);
    });
});
