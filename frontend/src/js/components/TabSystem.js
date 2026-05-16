/**
 * Tab System Component
 *
 * Verwaltet Tabs für Komponenten-Konfiguration im Infrastructure Designer
 */

export class TabSystem {
    constructor(headerContainerId, contentContainerId, onTabChange, onTabClose) {
        this.headerContainer = document.getElementById(headerContainerId);
        this.contentContainer = document.getElementById(contentContainerId);
        this.onTabChange = onTabChange;
        this.onTabClose = onTabClose;

        this.tabs = new Map(); // tabId -> { component, config }
        this.activeTabId = null;
    }

    /**
     * Open tab for component (or switch to it if already open)
     */
    openTab(component) {
        const tabId = component.id;

        // If tab already exists, just activate it
        if (this.tabs.has(tabId)) {
            this.activateTab(tabId);
            return;
        }

        // Create new tab
        this.tabs.set(tabId, component);
        this.renderTab(component);
        this.activateTab(tabId);
    }

    renderTab(component) {
        const tabId = component.id;

        // Create tab header
        const tabHeader = document.createElement('button');
        tabHeader.id = `tab-header-${tabId}`;
        tabHeader.className = 'tab-header px-4 py-2 text-sm font-medium rounded-t-lg border border-b-0 border-gray-300 bg-white text-gray-700 hover:bg-gray-50 transition';
        tabHeader.dataset.tabId = tabId;

        tabHeader.innerHTML = `
            <span class="mr-2">${this.getComponentIcon(component.type)}</span>
            <span>${component.name}</span>
            <button class="ml-2 text-gray-400 hover:text-gray-600" data-action="close">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
            </button>
        `;

        // Tab click handler
        tabHeader.addEventListener('click', (e) => {
            if (e.target.closest('[data-action="close"]')) {
                this.closeTab(tabId);
            } else {
                this.activateTab(tabId);
            }
        });

        this.headerContainer.appendChild(tabHeader);
    }

    activateTab(tabId) {
        if (this.activeTabId === tabId) return;

        // Deactivate all tabs
        this.headerContainer.querySelectorAll('.tab-header').forEach(header => {
            header.classList.remove('border-primary-500', 'text-primary-700', 'bg-white');
            header.classList.add('border-gray-300', 'text-gray-700', 'bg-gray-50');
        });

        // Activate selected tab
        const activeHeader = document.getElementById(`tab-header-${tabId}`);
        if (activeHeader) {
            activeHeader.classList.remove('border-gray-300', 'text-gray-700', 'bg-gray-50');
            activeHeader.classList.add('border-primary-500', 'text-primary-700', 'bg-white');
        }

        this.activeTabId = tabId;

        // Render tab content
        const component = this.tabs.get(tabId);
        if (component) {
            this.renderTabContent(component);
        }

        if (this.onTabChange) {
            this.onTabChange(tabId, component);
        }
    }

    closeTab(tabId) {
        const header = document.getElementById(`tab-header-${tabId}`);
        if (header) {
            header.remove();
        }

        this.tabs.delete(tabId);

        // If closed tab was active, activate another tab
        if (this.activeTabId === tabId) {
            const remainingTabs = Array.from(this.tabs.keys());
            if (remainingTabs.length > 0) {
                this.activateTab(remainingTabs[0]);
            } else {
                this.activeTabId = null;
                this.renderEmptyState();
            }
        }

        if (this.onTabClose) {
            this.onTabClose(tabId);
        }
    }

    renderTabContent(component) {
        this.contentContainer.innerHTML = `
            <div class="max-w-4xl mx-auto">
                <div class="bg-white rounded-lg shadow-md p-6">
                    <!-- Component Header -->
                    <div class="flex items-center justify-between mb-6">
                        <div class="flex items-center gap-3">
                            <div class="text-3xl">${this.getComponentIcon(component.type)}</div>
                            <div>
                                <h2 class="text-2xl font-bold text-gray-900">${component.name}</h2>
                                <p class="text-sm text-gray-500">${this.getComponentTypeLabel(component.type)}</p>
                            </div>
                        </div>
                        <button class="btn btn-secondary text-sm" data-action="duplicate">
                            <svg class="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                            </svg>
                            Duplicate
                        </button>
                    </div>

                    <!-- Component Configuration Form -->
                    <div id="component-config-form">
                        ${this.renderConfigForm(component)}
                    </div>
                </div>
            </div>
        `;

        this.attachFormListeners(component);
    }

    renderConfigForm(component) {
        const { type, config } = component;

        // Common fields for all components
        let formHtml = `
            <div class="space-y-6">
                <!-- Name -->
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">Name</label>
                    <input type="text" name="name" value="${component.name}" class="input" placeholder="Component Name">
                </div>
        `;

        // Type-specific fields
        switch (type) {
            case 'vpc':
                formHtml += `
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">CIDR Block</label>
                        <input type="text" name="cidr" value="${config.cidr || ''}" class="input" placeholder="10.0.0.0/16">
                    </div>
                    <div class="flex items-center gap-4">
                        <label class="flex items-center">
                            <input type="checkbox" name="enableDnsHostnames" ${config.enableDnsHostnames ? 'checked' : ''} class="mr-2">
                            <span class="text-sm text-gray-700">Enable DNS Hostnames</span>
                        </label>
                        <label class="flex items-center">
                            <input type="checkbox" name="enableDnsSupport" ${config.enableDnsSupport ? 'checked' : ''} class="mr-2">
                            <span class="text-sm text-gray-700">Enable DNS Support</span>
                        </label>
                    </div>
                `;
                break;

            case 'subnet':
                formHtml += `
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">CIDR Block</label>
                        <input type="text" name="cidr" value="${config.cidr || ''}" class="input" placeholder="10.0.1.0/24">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Subnet Type</label>
                        <select name="subnetType" class="input">
                            <option value="public" ${config.subnetType === 'public' ? 'selected' : ''}>Public</option>
                            <option value="private" ${config.subnetType === 'private' ? 'selected' : ''}>Private</option>
                            <option value="database" ${config.subnetType === 'database' ? 'selected' : ''}>Database</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Availability Zone</label>
                        <input type="text" name="availabilityZone" value="${config.availabilityZone || ''}" class="input" placeholder="us-east-1a">
                    </div>
                `;
                break;

            case 'ec2':
                formHtml += `
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Instance Type</label>
                        <select name="instanceType" class="input">
                            <option value="t3.micro" ${config.instanceType === 't3.micro' ? 'selected' : ''}>t3.micro</option>
                            <option value="t3.small" ${config.instanceType === 't3.small' ? 'selected' : ''}>t3.small</option>
                            <option value="t3.medium" ${config.instanceType === 't3.medium' ? 'selected' : ''}>t3.medium</option>
                            <option value="t3.large" ${config.instanceType === 't3.large' ? 'selected' : ''}>t3.large</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">AMI</label>
                        <input type="text" name="ami" value="${config.ami || ''}" class="input" placeholder="ami-xxxxx">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Private IP</label>
                        <input type="text" name="privateIp" value="${config.privateIp || ''}" class="input" placeholder="10.0.1.10">
                    </div>
                    <div>
                        <label class="flex items-center">
                            <input type="checkbox" name="hasPublicIp" ${config.hasPublicIp ? 'checked' : ''} class="mr-2">
                            <span class="text-sm text-gray-700">Assign Public IP</span>
                        </label>
                    </div>
                `;
                break;

            case 'rds':
                formHtml += `
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Engine</label>
                        <select name="engine" class="input">
                            <option value="postgres" ${config.engine === 'postgres' ? 'selected' : ''}>PostgreSQL</option>
                            <option value="mysql" ${config.engine === 'mysql' ? 'selected' : ''}>MySQL</option>
                            <option value="mariadb" ${config.engine === 'mariadb' ? 'selected' : ''}>MariaDB</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Engine Version</label>
                        <input type="text" name="engineVersion" value="${config.engineVersion || ''}" class="input" placeholder="14.7">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Instance Class</label>
                        <input type="text" name="instanceClass" value="${config.instanceClass || ''}" class="input" placeholder="db.t3.micro">
                    </div>
                `;
                break;

            case 's3':
                formHtml += `
                    <div class="flex items-center gap-4">
                        <label class="flex items-center">
                            <input type="checkbox" name="versioning" ${config.versioning ? 'checked' : ''} class="mr-2">
                            <span class="text-sm text-gray-700">Enable Versioning</span>
                        </label>
                        <label class="flex items-center">
                            <input type="checkbox" name="encryption" ${config.encryption ? 'checked' : ''} class="mr-2">
                            <span class="text-sm text-gray-700">Enable Encryption</span>
                        </label>
                        <label class="flex items-center">
                            <input type="checkbox" name="publicAccess" ${config.publicAccess ? 'checked' : ''} class="mr-2">
                            <span class="text-sm text-gray-700">Public Access</span>
                        </label>
                    </div>
                `;
                break;

            default:
                formHtml += `<p class="text-gray-500">Configuration for ${type} coming soon...</p>`;
        }

        formHtml += `
            </div>
            <div class="mt-6 flex justify-end gap-3">
                <button class="btn btn-secondary" data-action="cancel">Cancel</button>
                <button class="btn btn-primary" data-action="save">Save Changes</button>
            </div>
        `;

        return formHtml;
    }

    attachFormListeners(component) {
        const form = this.contentContainer.querySelector('#component-config-form');
        if (!form) return;

        // Save button
        const saveBtn = form.querySelector('[data-action="save"]');
        saveBtn?.addEventListener('click', () => {
            const formData = new FormData(form.querySelector('form') || form);
            const updates = {};

            // Get all input values
            form.querySelectorAll('input, select').forEach(input => {
                const name = input.name;
                if (!name) return;

                if (input.type === 'checkbox') {
                    updates[name] = input.checked;
                } else {
                    updates[name] = input.value;
                }
            });

            // Update component name separately
            if (updates.name) {
                component.name = updates.name;
                delete updates.name;
            }

            // Merge into config
            Object.assign(component.config, updates);

            // Trigger update event
            window.dispatchEvent(new CustomEvent('component-updated', {
                detail: { componentId: component.id, updates: { name: component.name, ...updates } }
            }));

            // Show feedback
            this.showSaveMessage();
        });

        // Cancel button
        const cancelBtn = form.querySelector('[data-action="cancel"]');
        cancelBtn?.addEventListener('click', () => {
            this.renderTabContent(component); // Reset form
        });
    }

    showSaveMessage() {
        const message = document.createElement('div');
        message.className = 'fixed bottom-4 right-4 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg';
        message.textContent = 'Changes saved successfully!';
        document.body.appendChild(message);

        setTimeout(() => {
            message.remove();
        }, 2000);
    }

    renderEmptyState() {
        this.contentContainer.innerHTML = `
            <div class="max-w-4xl mx-auto">
                <div class="text-center text-gray-500 py-12">
                    <svg class="w-16 h-16 mx-auto mb-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <p class="text-lg font-medium mb-2">Keine Komponente ausgewählt</p>
                    <p class="text-sm">Klicke auf eine Komponente im Canvas oder ziehe eine neue aus der Palette</p>
                </div>
            </div>
        `;
    }

    getComponentIcon(type) {
        const icons = {
            vpc: '🌐',
            subnet: '📦',
            ec2: '🖥️',
            rds: '💾',
            s3: '📁',
            lambda: 'λ',
            alb: '⚖️',
            ecs: '🐳',
            dynamodb: '⚡',
            elasticache: '🔄',
            igw: '🌍',
            nat: '🔀',
            sg: '🛡️',
            nacl: '🔒',
            iam: '👤'
        };
        return icons[type] || '📦';
    }

    getComponentTypeLabel(type) {
        const labels = {
            vpc: 'Virtual Private Cloud',
            subnet: 'Subnet',
            ec2: 'EC2 Instance',
            rds: 'RDS Database',
            s3: 'S3 Bucket',
            lambda: 'Lambda Function',
            alb: 'Application Load Balancer',
            ecs: 'ECS Service',
            dynamodb: 'DynamoDB Table',
            elasticache: 'ElastiCache Cluster',
            igw: 'Internet Gateway',
            nat: 'NAT Gateway',
            sg: 'Security Group',
            nacl: 'Network ACL',
            iam: 'IAM Role'
        };
        return labels[type] || type.toUpperCase();
    }

    /**
     * Update tab when component name changes
     */
    updateTab(componentId, updates) {
        const component = this.tabs.get(componentId);
        if (!component) return;

        Object.assign(component, updates);

        // Update tab header label
        const header = document.getElementById(`tab-header-${componentId}`);
        if (header) {
            const nameSpan = header.querySelector('span:nth-of-type(2)');
            if (nameSpan && updates.name) {
                nameSpan.textContent = updates.name;
            }
        }

        // If this is the active tab, re-render content
        if (this.activeTabId === componentId) {
            this.renderTabContent(component);
        }
    }
}
