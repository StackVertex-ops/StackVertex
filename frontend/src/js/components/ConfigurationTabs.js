/**
 * Configuration Tabs System
 *
 * 4 Tabs: Network, Security, Data, Computing
 * Each tab shows components of that category with inline IP calculator
 */

import { FormBuilder } from './forms/FormBuilder.js';

export class ConfigurationTabs {
    constructor(containerId, onComponentUpdate, onComponentDelete) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            throw new Error(`Container ${containerId} not found`);
        }

        this.onComponentUpdate = onComponentUpdate || (() => {});
        this.onComponentDelete = onComponentDelete || (() => {});
        this.currentTab = 'network';
        this.components = {
            network: [],
            security: [],
            data: [],
            computing: []
        };

        // Make methods available globally for onclick handlers
        window.deleteComponent = (id) => this.deleteComponent(id);
        window.updateComponent = (id, field, value) => this.updateComponent(id, field, value);
        window.updateVPCCIDR = (id, cidr) => this.updateVPCCIDR(id, cidr);
        window.updateSubnetCIDR = (id, cidr) => this.updateSubnetCIDR(id, cidr);
        window.toggleIPAssignment = (id, mode) => this.toggleIPAssignment(id, mode);

        this.render();
    }

    /**
     * Komponenten hinzufügen/updaten
     * @param {Array} components - Liste aller Komponenten
     */
    setComponents(components) {
        // Kategorisiere Komponenten
        this.components = {
            network: [],
            security: [],
            data: [],
            computing: []
        };

        components.forEach(comp => {
            const category = this.getComponentCategory(comp.type);
            if (this.components[category]) {
                this.components[category].push(comp);
            }
        });

        this.renderTabContent();
    }

    /**
     * Render Hauptstruktur
     */
    render() {
        this.container.innerHTML = `
            <div class="configuration-tabs h-full flex flex-col">
                <!-- Tab Headers -->
                <div class="tab-headers flex border-b border-gray-200 bg-white">
                    <button
                        class="tab-header ${this.currentTab === 'network' ? 'active' : ''}"
                        data-tab="network"
                    >
                        🌐 Network
                    </button>
                    <button
                        class="tab-header ${this.currentTab === 'security' ? 'active' : ''}"
                        data-tab="security"
                    >
                        🔒 Security
                    </button>
                    <button
                        class="tab-header ${this.currentTab === 'data' ? 'active' : ''}"
                        data-tab="data"
                    >
                        💾 Data
                    </button>
                    <button
                        class="tab-header ${this.currentTab === 'computing' ? 'active' : ''}"
                        data-tab="computing"
                    >
                        ⚙️ Computing
                    </button>
                </div>

                <!-- Tab Content -->
                <div class="tab-content flex-1 overflow-y-auto bg-gray-50">
                    <div id="network-tab" class="tab-pane ${this.currentTab === 'network' ? 'active' : 'hidden'}">
                        <!-- Network components -->
                    </div>
                    <div id="security-tab" class="tab-pane ${this.currentTab === 'security' ? 'active' : 'hidden'}">
                        <!-- Security components -->
                    </div>
                    <div id="data-tab" class="tab-pane ${this.currentTab === 'data' ? 'active' : 'hidden'}">
                        <!-- Data components -->
                    </div>
                    <div id="computing-tab" class="tab-pane ${this.currentTab === 'computing' ? 'active' : 'hidden'}">
                        <!-- Computing components -->
                    </div>
                </div>
            </div>
        `;

        this.attachTabListeners();
        this.renderTabContent();
    }

    /**
     * Tab-Switch Listeners
     */
    attachTabListeners() {
        const headers = this.container.querySelectorAll('.tab-header');
        headers.forEach(header => {
            header.addEventListener('click', () => {
                const tabName = header.dataset.tab;
                this.switchTab(tabName);
            });
        });
    }

    /**
     * Switch zu anderem Tab
     */
    switchTab(tabName) {
        this.currentTab = tabName;

        // Update headers
        this.container.querySelectorAll('.tab-header').forEach(h => {
            h.classList.toggle('active', h.dataset.tab === tabName);
        });

        // Update content
        this.container.querySelectorAll('.tab-pane').forEach(pane => {
            pane.classList.toggle('active', pane.id === `${tabName}-tab`);
            pane.classList.toggle('hidden', pane.id !== `${tabName}-tab`);
        });
    }

    /**
     * Öffne Tab und scrolle zur Komponente
     */
    openComponent(componentId, componentType) {
        const category = this.getComponentCategory(componentType);
        this.switchTab(category);

        // Scroll to component
        setTimeout(() => {
            const element = document.getElementById(`component-${componentId}`);
            if (element) {
                element.scrollIntoView({ behavior: 'smooth', block: 'center' });
                element.classList.add('highlight');
                setTimeout(() => element.classList.remove('highlight'), 2000);
            }
        }, 100);
    }

    /**
     * Bestimme Kategorie einer Komponente
     */
    getComponentCategory(type) {
        const categories = {
            vpc: 'network',
            subnet: 'network',
            igw: 'network',
            nat: 'network',
            route_table: 'network',
            sg: 'security',
            nacl: 'security',
            iam: 'security',
            kms: 'security',
            rds: 'data',
            dynamodb: 'data',
            s3: 'data',
            elasticache: 'data',
            ec2: 'computing',
            lambda: 'computing',
            ecs: 'computing',
            alb: 'computing',
            asg: 'computing'
        };
        return categories[type] || 'network';
    }

    /**
     * Render Content für alle Tabs
     */
    renderTabContent() {
        this.renderNetworkTab();
        this.renderSecurityTab();
        this.renderDataTab();
        this.renderComputingTab();
    }

    /**
     * Network Tab
     */
    renderNetworkTab() {
        const container = document.getElementById('network-tab');
        const networkComponents = this.components.network;

        if (networkComponents.length === 0) {
            container.innerHTML = `
                <div class="flex items-center justify-center h-full p-12 text-center">
                    <div>
                        <div class="text-6xl mb-4">🌐</div>
                        <h3 class="text-lg font-semibold text-gray-900 mb-2">
                            Keine Network-Komponenten
                        </h3>
                        <p class="text-sm text-gray-500">
                            Ziehe VPC, Subnets oder andere Network-Komponenten aus der Palette
                        </p>
                    </div>
                </div>
            `;
            return;
        }

        container.innerHTML = `
            <div class="p-6 space-y-6">
                ${networkComponents.map(comp => this.renderComponentForm(comp)).join('')}
            </div>
        `;
    }

    /**
     * Security Tab
     */
    renderSecurityTab() {
        const container = document.getElementById('security-tab');
        const securityComponents = this.components.security;

        if (securityComponents.length === 0) {
            container.innerHTML = `
                <div class="flex items-center justify-center h-full p-12 text-center">
                    <div>
                        <div class="text-6xl mb-4">🔒</div>
                        <h3 class="text-lg font-semibold text-gray-900 mb-2">
                            Keine Security-Komponenten
                        </h3>
                        <p class="text-sm text-gray-500">
                            Ziehe Security Groups, NACLs oder IAM Roles aus der Palette
                        </p>
                    </div>
                </div>
            `;
            return;
        }

        container.innerHTML = `
            <div class="p-6 space-y-6">
                ${securityComponents.map(comp => this.renderComponentForm(comp)).join('')}
            </div>
        `;
    }

    /**
     * Data Tab
     */
    renderDataTab() {
        const container = document.getElementById('data-tab');
        const dataComponents = this.components.data;

        if (dataComponents.length === 0) {
            container.innerHTML = `
                <div class="flex items-center justify-center h-full p-12 text-center">
                    <div>
                        <div class="text-6xl mb-4">💾</div>
                        <h3 class="text-lg font-semibold text-gray-900 mb-2">
                            Keine Data-Komponenten
                        </h3>
                        <p class="text-sm text-gray-500">
                            Ziehe RDS, DynamoDB, S3 oder ElastiCache aus der Palette
                        </p>
                    </div>
                </div>
            `;
            return;
        }

        container.innerHTML = `
            <div class="p-6 space-y-6">
                ${dataComponents.map(comp => this.renderComponentForm(comp)).join('')}
            </div>
        `;
    }

    /**
     * Computing Tab
     */
    renderComputingTab() {
        const container = document.getElementById('computing-tab');
        const computingComponents = this.components.computing;

        if (computingComponents.length === 0) {
            container.innerHTML = `
                <div class="flex items-center justify-center h-full p-12 text-center">
                    <div>
                        <div class="text-6xl mb-4">⚙️</div>
                        <h3 class="text-lg font-semibold text-gray-900 mb-2">
                            Keine Computing-Komponenten
                        </h3>
                        <p class="text-sm text-gray-500">
                            Ziehe EC2, Lambda, ECS oder ALB aus der Palette
                        </p>
                    </div>
                </div>
            `;
            return;
        }

        container.innerHTML = `
            <div class="p-6 space-y-6">
                ${computingComponents.map(comp => this.renderComponentForm(comp)).join('')}
            </div>
        `;
    }

    /**
     * Render Component Form basierend auf Typ
     */
    renderComponentForm(component) {
        switch (component.type) {
            case 'vpc':
                return this.renderVPCForm(component);
            case 'subnet':
                return this.renderSubnetForm(component);
            case 'ec2':
                return this.renderEC2Form(component);
            case 'rds':
                return this.renderRDSForm(component);
            case 'sg':
                return this.renderSecurityGroupForm(component);
            default:
                return this.renderGenericForm(component);
        }
    }

    /**
     * VPC Form mit inline IP calculator
     */
    renderVPCForm(component) {
        const cidr = component.config?.cidr || '10.0.0.0/16';
        const ipInfo = this.calculateIPInfo(cidr);

        return `
            <div id="component-${component.id}" class="component-form bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
                <div class="flex justify-between items-start mb-6">
                    <div class="flex items-center gap-3">
                        <div class="text-3xl">🌐</div>
                        <div>
                            <h3 class="text-lg font-semibold text-gray-900">
                                ${component.name || 'VPC'}
                            </h3>
                            <p class="text-xs text-gray-500">Virtual Private Cloud</p>
                        </div>
                    </div>
                    <button
                        class="text-red-600 hover:text-red-700 text-sm font-medium px-3 py-1 rounded hover:bg-red-50 transition-colors"
                        onclick="deleteComponent('${component.id}')"
                    >
                        Löschen
                    </button>
                </div>

                <div class="space-y-5">
                    <!-- Name -->
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">
                            VPC Name
                        </label>
                        <input
                            type="text"
                            value="${component.name || ''}"
                            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                            placeholder="z.B. production-vpc"
                            onchange="updateComponent('${component.id}', 'name', this.value)"
                        />
                    </div>

                    <!-- CIDR mit inline calculator -->
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">
                            CIDR Block
                        </label>
                        <input
                            type="text"
                            value="${cidr}"
                            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent font-mono"
                            placeholder="10.0.0.0/16"
                            oninput="updateVPCCIDR('${component.id}', this.value)"
                        />
                        <!-- Inline IP Info -->
                        <div class="mt-3 p-3 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg border border-blue-200">
                            <div class="grid grid-cols-2 gap-3">
                                <div class="flex items-center gap-2">
                                    <span class="text-xs font-medium text-gray-600">Total IPs:</span>
                                    <span class="font-mono font-semibold text-blue-700">
                                        ${ipInfo.total.toLocaleString()}
                                    </span>
                                </div>
                                <div class="flex items-center gap-2">
                                    <span class="text-xs font-medium text-gray-600">Nutzbar:</span>
                                    <span class="font-mono font-semibold text-green-700">
                                        ${ipInfo.usable.toLocaleString()}
                                    </span>
                                </div>
                            </div>
                            <div class="mt-2 text-xs text-gray-600">
                                <span class="font-medium">Range:</span>
                                <span class="font-mono">${ipInfo.firstIP} - ${ipInfo.lastIP}</span>
                            </div>
                        </div>
                    </div>

                    <!-- Region -->
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">
                            AWS Region
                        </label>
                        <select
                            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                            onchange="updateComponent('${component.id}', 'region', this.value)"
                        >
                            <option value="us-east-1" ${component.config?.region === 'us-east-1' ? 'selected' : ''}>us-east-1 (N. Virginia)</option>
                            <option value="us-west-2" ${component.config?.region === 'us-west-2' ? 'selected' : ''}>us-west-2 (Oregon)</option>
                            <option value="eu-central-1" ${component.config?.region === 'eu-central-1' ? 'selected' : ''}>eu-central-1 (Frankfurt)</option>
                            <option value="eu-west-1" ${component.config?.region === 'eu-west-1' ? 'selected' : ''}>eu-west-1 (Ireland)</option>
                        </select>
                    </div>

                    <!-- DNS Settings -->
                    <div class="space-y-2">
                        <div class="flex items-center gap-3">
                            <input
                                type="checkbox"
                                id="dns-hostnames-${component.id}"
                                class="w-4 h-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500"
                                ${component.config?.enableDnsHostnames ? 'checked' : ''}
                                onchange="updateComponent('${component.id}', 'enableDnsHostnames', this.checked)"
                            />
                            <label for="dns-hostnames-${component.id}" class="text-sm text-gray-700">
                                Enable DNS hostnames
                            </label>
                        </div>
                        <div class="flex items-center gap-3">
                            <input
                                type="checkbox"
                                id="dns-support-${component.id}"
                                class="w-4 h-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500"
                                ${component.config?.enableDnsSupport !== false ? 'checked' : ''}
                                onchange="updateComponent('${component.id}', 'enableDnsSupport', this.checked)"
                            />
                            <label for="dns-support-${component.id}" class="text-sm text-gray-700">
                                Enable DNS resolution
                            </label>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Subnet Form mit inline IP calculator
     */
    renderSubnetForm(component) {
        const cidr = component.config?.cidr || '10.0.1.0/24';
        const ipInfo = this.calculateIPInfo(cidr);
        const vpcCidr = component.config?.vpcCidr || '10.0.0.0/16';
        const subnetType = component.config?.subnetType || 'public';

        return `
            <div id="component-${component.id}" class="component-form bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
                <div class="flex justify-between items-start mb-6">
                    <div class="flex items-center gap-3">
                        <div class="text-3xl">📦</div>
                        <div>
                            <h3 class="text-lg font-semibold text-gray-900">
                                ${component.name || 'Subnet'}
                            </h3>
                            <p class="text-xs text-gray-500">VPC Subnet</p>
                        </div>
                    </div>
                    <button
                        class="text-red-600 hover:text-red-700 text-sm font-medium px-3 py-1 rounded hover:bg-red-50 transition-colors"
                        onclick="deleteComponent('${component.id}')"
                    >
                        Löschen
                    </button>
                </div>

                <div class="space-y-5">
                    <!-- Name -->
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">
                            Subnet Name
                        </label>
                        <input
                            type="text"
                            value="${component.name || ''}"
                            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                            placeholder="z.B. public-subnet-1a"
                            onchange="updateComponent('${component.id}', 'name', this.value)"
                        />
                    </div>

                    <!-- VPC Auswahl -->
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">
                            VPC
                        </label>
                        <select
                            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                            onchange="updateComponent('${component.id}', 'vpc', this.value)"
                        >
                            <option value="">VPC auswählen...</option>
                            ${this.components.network
                                .filter(c => c.type === 'vpc')
                                .map(vpc => `
                                    <option value="${vpc.id}" ${component.config?.vpcId === vpc.id ? 'selected' : ''}>
                                        ${vpc.name} (${vpc.config?.cidr || ''})
                                    </option>
                                `).join('')}
                        </select>
                        <div class="mt-1 text-xs text-gray-500">
                            VPC Range: <span class="font-mono">${vpcCidr}</span>
                        </div>
                    </div>

                    <!-- CIDR mit inline calculator -->
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">
                            CIDR Block
                        </label>
                        <input
                            type="text"
                            value="${cidr}"
                            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent font-mono"
                            placeholder="10.0.1.0/24"
                            oninput="updateSubnetCIDR('${component.id}', this.value)"
                        />
                        <!-- Inline IP Info -->
                        <div class="mt-3 p-3 bg-gradient-to-r from-green-50 to-blue-50 rounded-lg border border-green-200">
                            <div class="grid grid-cols-2 gap-3 mb-2">
                                <div class="flex items-center gap-2">
                                    <span class="text-xs font-medium text-gray-600">Total IPs:</span>
                                    <span class="font-mono font-semibold text-blue-700">
                                        ${ipInfo.total}
                                    </span>
                                </div>
                                <div class="flex items-center gap-2">
                                    <span class="text-xs font-medium text-gray-600">Nutzbar:</span>
                                    <span class="font-mono font-semibold text-green-700">
                                        ${ipInfo.usable}
                                    </span>
                                </div>
                            </div>
                            <div class="text-xs text-gray-600 space-y-1">
                                <div>
                                    <span class="font-medium">IP Range:</span>
                                    <span class="font-mono">${ipInfo.firstIP} - ${ipInfo.lastIP}</span>
                                </div>
                                <div>
                                    <span class="font-medium">AWS Reserved:</span>
                                    <span class="font-mono text-red-600">${ipInfo.reserved.slice(0, 5).join(', ')}</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Subnet Type -->
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">
                            Subnet Typ
                        </label>
                        <div class="grid grid-cols-3 gap-2">
                            <button
                                class="px-4 py-2 rounded-lg border text-sm font-medium transition-colors ${subnetType === 'public' ? 'bg-blue-100 border-blue-500 text-blue-700' : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'}"
                                onclick="updateComponent('${component.id}', 'subnetType', 'public')"
                            >
                                Public
                            </button>
                            <button
                                class="px-4 py-2 rounded-lg border text-sm font-medium transition-colors ${subnetType === 'private' ? 'bg-blue-100 border-blue-500 text-blue-700' : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'}"
                                onclick="updateComponent('${component.id}', 'subnetType', 'private')"
                            >
                                Private
                            </button>
                            <button
                                class="px-4 py-2 rounded-lg border text-sm font-medium transition-colors ${subnetType === 'database' ? 'bg-blue-100 border-blue-500 text-blue-700' : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'}"
                                onclick="updateComponent('${component.id}', 'subnetType', 'database')"
                            >
                                Database
                            </button>
                        </div>
                    </div>

                    <!-- Availability Zone -->
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">
                            Availability Zone
                        </label>
                        <select
                            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                            onchange="updateComponent('${component.id}', 'az', this.value)"
                        >
                            <option value="us-east-1a" ${component.config?.az === 'us-east-1a' ? 'selected' : ''}>us-east-1a</option>
                            <option value="us-east-1b" ${component.config?.az === 'us-east-1b' ? 'selected' : ''}>us-east-1b</option>
                            <option value="us-east-1c" ${component.config?.az === 'us-east-1c' ? 'selected' : ''}>us-east-1c</option>
                        </select>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * EC2 Form mit IP assignment
     */
    renderEC2Form(component) {
        const ipMode = component.config?.ipMode || 'auto';
        const hasPublicIP = component.config?.assignPublicIP || false;

        return `
            <div id="component-${component.id}" class="component-form bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
                <div class="flex justify-between items-start mb-6">
                    <div class="flex items-center gap-3">
                        <div class="text-3xl">🖥️</div>
                        <div>
                            <h3 class="text-lg font-semibold text-gray-900">
                                ${component.name || 'EC2 Instance'}
                            </h3>
                            <p class="text-xs text-gray-500">Elastic Compute Cloud</p>
                        </div>
                    </div>
                    <button
                        class="text-red-600 hover:text-red-700 text-sm font-medium px-3 py-1 rounded hover:bg-red-50 transition-colors"
                        onclick="deleteComponent('${component.id}')"
                    >
                        Löschen
                    </button>
                </div>

                <div class="space-y-5">
                    <!-- Name -->
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">
                            Instance Name
                        </label>
                        <input
                            type="text"
                            value="${component.name || ''}"
                            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                            placeholder="z.B. web-server-1"
                            onchange="updateComponent('${component.id}', 'name', this.value)"
                        />
                    </div>

                    <!-- Instance Type -->
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">
                            Instance Type
                        </label>
                        <select
                            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                            onchange="updateComponent('${component.id}', 'instanceType', this.value)"
                        >
                            <option value="t3.micro" ${component.config?.instanceType === 't3.micro' ? 'selected' : ''}>
                                t3.micro (1 vCPU, 1GB RAM) - $0.0104/hr
                            </option>
                            <option value="t3.small" ${component.config?.instanceType === 't3.small' ? 'selected' : ''}>
                                t3.small (2 vCPU, 2GB RAM) - $0.0208/hr
                            </option>
                            <option value="t3.medium" ${component.config?.instanceType === 't3.medium' ? 'selected' : ''}>
                                t3.medium (2 vCPU, 4GB RAM) - $0.0416/hr
                            </option>
                            <option value="t3.large" ${component.config?.instanceType === 't3.large' ? 'selected' : ''}>
                                t3.large (2 vCPU, 8GB RAM) - $0.0832/hr
                            </option>
                        </select>
                    </div>

                    <!-- Subnet -->
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">
                            Subnet
                        </label>
                        <select
                            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                            onchange="updateComponent('${component.id}', 'subnet', this.value)"
                        >
                            <option value="">Subnet auswählen...</option>
                            ${this.components.network
                                .filter(c => c.type === 'subnet')
                                .map(subnet => `
                                    <option value="${subnet.id}" ${component.config?.subnetId === subnet.id ? 'selected' : ''}>
                                        ${subnet.name} (${subnet.config?.cidr || ''})
                                    </option>
                                `).join('')}
                        </select>
                        ${component.config?.subnetId ? `
                            <div class="mt-1 text-xs text-gray-500">
                                IP Range: <span class="font-mono">${this.getSubnetCIDR(component.config.subnetId)}</span>
                            </div>
                        ` : ''}
                    </div>

                    <!-- Private IP -->
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">
                            Private IP Adresse
                        </label>
                        <div class="flex items-center gap-4 mb-3">
                            <label class="flex items-center gap-2 cursor-pointer">
                                <input
                                    type="radio"
                                    name="ip-mode-${component.id}"
                                    value="auto"
                                    class="w-4 h-4 text-purple-600 border-gray-300 focus:ring-purple-500"
                                    ${ipMode === 'auto' ? 'checked' : ''}
                                    onchange="toggleIPAssignment('${component.id}', 'auto')"
                                />
                                <span class="text-sm text-gray-700">Auto-Assign</span>
                            </label>
                            <label class="flex items-center gap-2 cursor-pointer">
                                <input
                                    type="radio"
                                    name="ip-mode-${component.id}"
                                    value="manual"
                                    class="w-4 h-4 text-purple-600 border-gray-300 focus:ring-purple-500"
                                    ${ipMode === 'manual' ? 'checked' : ''}
                                    onchange="toggleIPAssignment('${component.id}', 'manual')"
                                />
                                <span class="text-sm text-gray-700">Manuell</span>
                            </label>
                        </div>
                        <input
                            type="text"
                            id="private-ip-${component.id}"
                            value="${component.config?.privateIP || ''}"
                            placeholder="10.0.1.15"
                            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent font-mono"
                            ${ipMode === 'auto' ? 'disabled' : ''}
                            onchange="updateComponent('${component.id}', 'privateIP', this.value)"
                        />
                    </div>

                    <!-- Public IP -->
                    <div class="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                        <div class="flex items-center gap-3 mb-2">
                            <input
                                type="checkbox"
                                id="public-ip-${component.id}"
                                class="w-4 h-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500"
                                ${hasPublicIP ? 'checked' : ''}
                                onchange="updateComponent('${component.id}', 'assignPublicIP', this.checked)"
                            />
                            <label for="public-ip-${component.id}" class="text-sm font-medium text-gray-700">
                                Assign Public IP
                            </label>
                        </div>
                        <div class="text-xs text-gray-600">
                            Public IP: <span class="font-mono">${hasPublicIP ? '[Assigned after deployment]' : 'None'}</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * RDS Form mit IP assignment
     */
    renderRDSForm(component) {
        return `
            <div id="component-${component.id}" class="component-form bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
                <div class="flex justify-between items-start mb-6">
                    <div class="flex items-center gap-3">
                        <div class="text-3xl">🗄️</div>
                        <div>
                            <h3 class="text-lg font-semibold text-gray-900">
                                ${component.name || 'RDS Database'}
                            </h3>
                            <p class="text-xs text-gray-500">Relational Database Service</p>
                        </div>
                    </div>
                    <button
                        class="text-red-600 hover:text-red-700 text-sm font-medium px-3 py-1 rounded hover:bg-red-50 transition-colors"
                        onclick="deleteComponent('${component.id}')"
                    >
                        Löschen
                    </button>
                </div>

                <div class="space-y-5">
                    <!-- Name -->
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">
                            DB Instance Name
                        </label>
                        <input
                            type="text"
                            value="${component.name || ''}"
                            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                            placeholder="z.B. production-db"
                            onchange="updateComponent('${component.id}', 'name', this.value)"
                        />
                    </div>

                    <!-- Engine -->
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">
                            Database Engine
                        </label>
                        <select
                            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                            onchange="updateComponent('${component.id}', 'engine', this.value)"
                        >
                            <option value="postgres" ${component.config?.engine === 'postgres' ? 'selected' : ''}>PostgreSQL</option>
                            <option value="mysql" ${component.config?.engine === 'mysql' ? 'selected' : ''}>MySQL</option>
                            <option value="mariadb" ${component.config?.engine === 'mariadb' ? 'selected' : ''}>MariaDB</option>
                            <option value="aurora-postgresql" ${component.config?.engine === 'aurora-postgresql' ? 'selected' : ''}>Aurora PostgreSQL</option>
                        </select>
                    </div>

                    <!-- Instance Class -->
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">
                            Instance Class
                        </label>
                        <select
                            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                            onchange="updateComponent('${component.id}', 'instanceClass', this.value)"
                        >
                            <option value="db.t3.micro" ${component.config?.instanceClass === 'db.t3.micro' ? 'selected' : ''}>
                                db.t3.micro (1 vCPU, 1GB RAM)
                            </option>
                            <option value="db.t3.small" ${component.config?.instanceClass === 'db.t3.small' ? 'selected' : ''}>
                                db.t3.small (2 vCPU, 2GB RAM)
                            </option>
                            <option value="db.t3.medium" ${component.config?.instanceClass === 'db.t3.medium' ? 'selected' : ''}>
                                db.t3.medium (2 vCPU, 4GB RAM)
                            </option>
                        </select>
                    </div>

                    <!-- Subnet Group -->
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">
                            Subnet Group (Multi-AZ)
                        </label>
                        <div class="space-y-2">
                            ${this.components.network
                                .filter(c => c.type === 'subnet' && c.config?.subnetType === 'database')
                                .map(subnet => `
                                    <div class="flex items-center gap-2">
                                        <input
                                            type="checkbox"
                                            id="subnet-${subnet.id}"
                                            class="w-4 h-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500"
                                            onchange="updateComponent('${component.id}', 'addSubnet', '${subnet.id}')"
                                        />
                                        <label for="subnet-${subnet.id}" class="text-sm text-gray-700">
                                            ${subnet.name} (${subnet.config?.az || ''})
                                        </label>
                                    </div>
                                `).join('')}
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Security Group Form
     */
    renderSecurityGroupForm(component) {
        return `
            <div id="component-${component.id}" class="component-form bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
                <div class="flex justify-between items-start mb-6">
                    <div class="flex items-center gap-3">
                        <div class="text-3xl">🔒</div>
                        <div>
                            <h3 class="text-lg font-semibold text-gray-900">
                                ${component.name || 'Security Group'}
                            </h3>
                            <p class="text-xs text-gray-500">Firewall Rules</p>
                        </div>
                    </div>
                    <button
                        class="text-red-600 hover:text-red-700 text-sm font-medium px-3 py-1 rounded hover:bg-red-50 transition-colors"
                        onclick="deleteComponent('${component.id}')"
                    >
                        Löschen
                    </button>
                </div>

                <div class="space-y-5">
                    <!-- Name -->
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">
                            Security Group Name
                        </label>
                        <input
                            type="text"
                            value="${component.name || ''}"
                            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                            placeholder="z.B. web-server-sg"
                            onchange="updateComponent('${component.id}', 'name', this.value)"
                        />
                    </div>

                    <!-- Inbound Rules -->
                    <div>
                        <div class="flex justify-between items-center mb-3">
                            <label class="block text-sm font-medium text-gray-700">
                                Inbound Rules
                            </label>
                            <button class="text-sm text-purple-600 hover:text-purple-700 font-medium">
                                + Add Rule
                            </button>
                        </div>
                        <div class="space-y-2 text-sm text-gray-500">
                            <div class="p-3 bg-gray-50 rounded border border-gray-200">
                                No inbound rules defined
                            </div>
                        </div>
                    </div>

                    <!-- Outbound Rules -->
                    <div>
                        <div class="flex justify-between items-center mb-3">
                            <label class="block text-sm font-medium text-gray-700">
                                Outbound Rules
                            </label>
                            <button class="text-sm text-purple-600 hover:text-purple-700 font-medium">
                                + Add Rule
                            </button>
                        </div>
                        <div class="space-y-2 text-sm text-gray-500">
                            <div class="p-3 bg-gray-50 rounded border border-gray-200">
                                All traffic allowed (default)
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Generic Form für unbekannte Komponenten
     */
    renderGenericForm(component) {
        return `
            <div id="component-${component.id}" class="component-form bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
                <div class="flex justify-between items-start mb-6">
                    <div>
                        <h3 class="text-lg font-semibold text-gray-900">
                            ${component.name || component.type}
                        </h3>
                        <p class="text-xs text-gray-500">${component.type}</p>
                    </div>
                    <button
                        class="text-red-600 hover:text-red-700 text-sm font-medium px-3 py-1 rounded hover:bg-red-50 transition-colors"
                        onclick="deleteComponent('${component.id}')"
                    >
                        Löschen
                    </button>
                </div>

                <div class="text-sm text-gray-500">
                    Configuration form coming soon...
                </div>
            </div>
        `;
    }

    /**
     * IP Info Calculator
     */
    calculateIPInfo(cidr) {
        if (!cidr || !cidr.includes('/')) {
            return { total: 0, usable: 0, firstIP: '', lastIP: '', reserved: [] };
        }

        const [ip, prefix] = cidr.split('/');
        const prefixNum = parseInt(prefix);

        if (prefixNum < 0 || prefixNum > 32) {
            return { total: 0, usable: 0, firstIP: '', lastIP: '', reserved: [] };
        }

        const total = Math.pow(2, 32 - prefixNum);
        const usable = Math.max(0, total - 5); // AWS reserves 5 IPs

        // Calculate first and last IP
        const ipParts = ip.split('.').map(Number);
        const ipNum = (ipParts[0] << 24) + (ipParts[1] << 16) + (ipParts[2] << 8) + ipParts[3];
        const lastIPNum = ipNum + total - 1;

        const firstIP = ip;
        const lastIP = [
            (lastIPNum >>> 24) & 0xFF,
            (lastIPNum >>> 16) & 0xFF,
            (lastIPNum >>> 8) & 0xFF,
            lastIPNum & 0xFF
        ].join('.');

        // AWS Reserved IPs
        const reserved = [
            ip, // Network address
            this.incrementIP(ip, 1), // VPC router
            this.incrementIP(ip, 2), // DNS server
            this.incrementIP(ip, 3), // Future use
            lastIP // Broadcast
        ];

        return { total, usable, firstIP, lastIP, reserved };
    }

    incrementIP(ip, increment) {
        const parts = ip.split('.').map(Number);
        let num = (parts[0] << 24) + (parts[1] << 16) + (parts[2] << 8) + parts[3];
        num += increment;
        return [
            (num >>> 24) & 0xFF,
            (num >>> 16) & 0xFF,
            (num >>> 8) & 0xFF,
            num & 0xFF
        ].join('.');
    }

    /**
     * Helper: Get Subnet CIDR by ID
     */
    getSubnetCIDR(subnetId) {
        const subnet = this.components.network.find(c => c.id === subnetId);
        return subnet?.config?.cidr || 'N/A';
    }

    /**
     * Component Update Handler
     */
    updateComponent(id, field, value) {
        this.onComponentUpdate(id, field, value);
        // Re-render if needed
        this.renderTabContent();
    }

    /**
     * VPC CIDR Update mit Live Calculation
     */
    updateVPCCIDR(id, cidr) {
        this.updateComponent(id, 'cidr', cidr);
    }

    /**
     * Subnet CIDR Update mit Live Calculation
     */
    updateSubnetCIDR(id, cidr) {
        this.updateComponent(id, 'cidr', cidr);
    }

    /**
     * Toggle IP Assignment Mode
     */
    toggleIPAssignment(id, mode) {
        this.updateComponent(id, 'ipMode', mode);

        const input = document.getElementById(`private-ip-${id}`);
        if (input) {
            input.disabled = mode === 'auto';
            if (mode === 'auto') {
                input.value = '';
            }
        }
    }

    /**
     * Component Delete Handler
     */
    deleteComponent(id) {
        if (confirm('Komponente wirklich löschen?')) {
            this.onComponentDelete(id);
            // Re-render
            this.renderTabContent();
        }
    }
}
