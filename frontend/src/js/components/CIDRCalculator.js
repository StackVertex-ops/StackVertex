/**
 * Visual CIDR Calculator Component
 *
 * Interaktive VPC/Subnet-Planung mit visueller IP-Darstellung
 */

export class CIDRCalculator {
    constructor(containerId, apiBaseUrl = (import.meta.env.VITE_API_URL || 'http://localhost:8000') + '/api/v1') {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            throw new Error(`Container with id "${containerId}" not found`);
        }

        // SECURITY FIX: No hardcoded URL
        this.apiBaseUrl = apiBaseUrl;
        this.vpcCidr = '';
        this.vpcData = null;
        this.subnets = [];
        this.vpcPlan = null;
    }

    /**
     * Rendert den CIDR Calculator
     */
    render() {
        this.container.innerHTML = `
            <div class="cidr-calculator bg-white rounded-lg shadow-lg p-6">
                <!-- VPC CIDR Input -->
                <div class="mb-6">
                    <label class="block text-sm font-medium text-gray-700 mb-2">
                        VPC CIDR Block
                    </label>
                    <div class="flex gap-2">
                        <input
                            type="text"
                            id="vpcCidrInput"
                            placeholder="z.B. 10.0.0.0/16"
                            class="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                            value="${this.vpcCidr}"
                        />
                        <button
                            id="validateVpcBtn"
                            class="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors font-medium"
                        >
                            Validieren
                        </button>
                        <button
                            id="suggestSubnetsBtn"
                            class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium disabled:bg-gray-300 disabled:cursor-not-allowed"
                            disabled
                        >
                            Vorschläge
                        </button>
                    </div>
                    <div id="vpcValidationResult" class="mt-2"></div>
                </div>

                <!-- VPC Overview (after validation) -->
                <div id="vpcOverview" class="hidden mb-6 p-4 bg-gradient-to-r from-purple-50 to-indigo-50 rounded-lg border border-purple-200">
                    <!-- Filled via JS -->
                </div>

                <!-- Subnet Builder -->
                <div id="subnetBuilder" class="hidden">
                    <div class="flex justify-between items-center mb-4">
                        <h3 class="text-lg font-semibold text-gray-900">Subnets</h3>
                        <button
                            id="addSubnetBtn"
                            class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium"
                        >
                            + Subnet hinzufügen
                        </button>
                    </div>

                    <div id="subnetList" class="space-y-3 mb-4">
                        <!-- Subnets via JS -->
                    </div>

                    <button
                        id="calculatePlanBtn"
                        class="w-full px-6 py-3 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed"
                        disabled
                    >
                        VPC Plan berechnen
                    </button>
                </div>

                <!-- Visual Plan -->
                <div id="visualPlan" class="hidden mt-6">
                    <!-- Visual representation -->
                </div>
            </div>
        `;

        this.attachEventListeners();
    }

    /**
     * Event Listeners anbinden
     */
    attachEventListeners() {
        const vpcInput = document.getElementById('vpcCidrInput');
        const validateBtn = document.getElementById('validateVpcBtn');
        const suggestBtn = document.getElementById('suggestSubnetsBtn');
        const addSubnetBtn = document.getElementById('addSubnetBtn');
        const calculateBtn = document.getElementById('calculatePlanBtn');

        vpcInput?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.validateVPC();
            }
        });

        validateBtn?.addEventListener('click', () => this.validateVPC());
        suggestBtn?.addEventListener('click', () => this.showSuggestionModal());
        addSubnetBtn?.addEventListener('click', () => this.addSubnet());
        calculateBtn?.addEventListener('click', () => this.calculatePlan());
    }

    /**
     * Validiert den VPC CIDR Block
     */
    async validateVPC() {
        const input = document.getElementById('vpcCidrInput');
        this.vpcCidr = input.value.trim();

        if (!this.vpcCidr) {
            this.showValidationResult({ valid: false, error: 'Bitte CIDR Block eingeben' });
            return;
        }

        try {
            const response = await fetch(`${this.apiBaseUrl}/cidr/validate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ cidr: this.vpcCidr })
            });

            const result = await response.json();
            this.vpcData = result;
            this.showValidationResult(result);

            if (result.valid) {
                this.showVPCOverview(result);
                document.getElementById('subnetBuilder').classList.remove('hidden');
                document.getElementById('suggestSubnetsBtn').disabled = false;
                this.updateCalculateButton();
            } else {
                document.getElementById('vpcOverview').classList.add('hidden');
                document.getElementById('subnetBuilder').classList.add('hidden');
                document.getElementById('suggestSubnetsBtn').disabled = true;
            }
        } catch (error) {
            this.showError(`Fehler beim Validieren: ${error.message}`);
        }
    }

    /**
     * Zeigt Validierungsergebnis an
     */
    showValidationResult(result) {
        const container = document.getElementById('vpcValidationResult');

        if (result.valid) {
            container.innerHTML = `
                <div class="text-sm text-green-700 bg-green-50 border border-green-200 rounded px-3 py-2">
                    ✓ Gültiger CIDR Block
                    ${result.warning ? `<br><span class="text-yellow-600">${result.warning}</span>` : ''}
                </div>
            `;
        } else {
            container.innerHTML = `
                <div class="text-sm text-red-700 bg-red-50 border border-red-200 rounded px-3 py-2">
                    ⚠️ ${result.error}
                </div>
            `;
        }
    }

    /**
     * Zeigt VPC Übersicht an
     */
    showVPCOverview(result) {
        const container = document.getElementById('vpcOverview');
        container.classList.remove('hidden');
        container.innerHTML = `
            <div class="grid grid-cols-3 gap-4 text-center">
                <div>
                    <div class="text-2xl font-bold text-purple-600">${result.total_ips.toLocaleString()}</div>
                    <div class="text-sm text-gray-600">Total IPs</div>
                </div>
                <div>
                    <div class="text-2xl font-bold text-green-600">${result.usable_ips.toLocaleString()}</div>
                    <div class="text-sm text-gray-600">Usable IPs (minus 5 reserved)</div>
                </div>
                <div>
                    <div class="text-2xl font-bold text-gray-700">${this.vpcCidr}</div>
                    <div class="text-sm text-gray-600">CIDR Block</div>
                </div>
            </div>
        `;
    }

    /**
     * Zeigt Modal für Subnet-Vorschläge
     */
    async showSuggestionModal() {
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        modal.innerHTML = `
            <div class="bg-white rounded-lg shadow-xl p-6 max-w-md w-full mx-4">
                <h3 class="text-xl font-semibold mb-4">Subnet-Vorschläge generieren</h3>

                <div class="space-y-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">
                            Anzahl Availability Zones
                        </label>
                        <input
                            type="number"
                            id="numAZs"
                            min="1"
                            max="6"
                            value="3"
                            class="w-full px-4 py-2 border border-gray-300 rounded-lg"
                        />
                    </div>

                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">
                            Subnet-Typen
                        </label>
                        <div class="space-y-2">
                            <label class="flex items-center">
                                <input type="checkbox" class="subnet-type-checkbox" value="public" checked>
                                <span class="ml-2 text-sm">Public</span>
                            </label>
                            <label class="flex items-center">
                                <input type="checkbox" class="subnet-type-checkbox" value="private" checked>
                                <span class="ml-2 text-sm">Private</span>
                            </label>
                            <label class="flex items-center">
                                <input type="checkbox" class="subnet-type-checkbox" value="database" checked>
                                <span class="ml-2 text-sm">Database</span>
                            </label>
                        </div>
                    </div>
                </div>

                <div class="flex gap-3 mt-6">
                    <button
                        id="generateSuggestionsBtn"
                        class="flex-1 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 font-medium"
                    >
                        Generieren
                    </button>
                    <button
                        id="cancelSuggestionsBtn"
                        class="flex-1 px-4 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400 font-medium"
                    >
                        Abbrechen
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        modal.querySelector('#generateSuggestionsBtn').addEventListener('click', async () => {
            const numAZs = parseInt(modal.querySelector('#numAZs').value);
            const checkedTypes = Array.from(modal.querySelectorAll('.subnet-type-checkbox:checked'))
                .map(cb => cb.value);

            await this.generateSuggestions(numAZs, checkedTypes);
            document.body.removeChild(modal);
        });

        modal.querySelector('#cancelSuggestionsBtn').addEventListener('click', () => {
            document.body.removeChild(modal);
        });

        // Close on background click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                document.body.removeChild(modal);
            }
        });
    }

    /**
     * Generiert Subnet-Vorschläge
     */
    async generateSuggestions(numAZs, subnetTypes) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/cidr/suggest`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    vpc_cidr: this.vpcCidr,
                    num_azs: numAZs,
                    subnet_types: subnetTypes.length > 0 ? subnetTypes : null
                })
            });

            const result = await response.json();

            // Subnets übernehmen
            this.subnets = result.suggested_subnets;
            this.renderSubnetList();
            this.updateCalculateButton();

            this.showSuccess(`${this.subnets.length} Subnets vorgeschlagen`);
        } catch (error) {
            this.showError(`Fehler beim Generieren: ${error.message}`);
        }
    }

    /**
     * Fügt ein leeres Subnet hinzu
     */
    addSubnet() {
        this.subnets.push({
            name: `subnet-${this.subnets.length + 1}`,
            cidr: '',
            type: 'private',
            az: null
        });

        this.renderSubnetList();
        this.updateCalculateButton();
    }

    /**
     * Rendert die Subnet-Liste
     */
    renderSubnetList() {
        const container = document.getElementById('subnetList');

        if (this.subnets.length === 0) {
            container.innerHTML = `
                <div class="text-center text-gray-500 py-8">
                    Keine Subnets definiert. Klicke auf "+ Subnet hinzufügen" oder "Vorschläge".
                </div>
            `;
            return;
        }

        container.innerHTML = this.subnets.map((subnet, index) => `
            <div class="subnet-item border border-gray-300 rounded-lg p-4 bg-gray-50" data-index="${index}">
                <div class="grid grid-cols-1 md:grid-cols-4 gap-3">
                    <div>
                        <label class="block text-xs font-medium text-gray-700 mb-1">Name</label>
                        <input
                            type="text"
                            class="subnet-name w-full px-3 py-2 border border-gray-300 rounded text-sm"
                            value="${subnet.name}"
                            data-index="${index}"
                        />
                    </div>
                    <div>
                        <label class="block text-xs font-medium text-gray-700 mb-1">CIDR</label>
                        <input
                            type="text"
                            class="subnet-cidr w-full px-3 py-2 border border-gray-300 rounded text-sm"
                            value="${subnet.cidr}"
                            placeholder="z.B. 10.0.1.0/24"
                            data-index="${index}"
                        />
                    </div>
                    <div>
                        <label class="block text-xs font-medium text-gray-700 mb-1">Typ</label>
                        <select
                            class="subnet-type w-full px-3 py-2 border border-gray-300 rounded text-sm"
                            data-index="${index}"
                        >
                            <option value="public" ${subnet.type === 'public' ? 'selected' : ''}>Public</option>
                            <option value="private" ${subnet.type === 'private' ? 'selected' : ''}>Private</option>
                            <option value="database" ${subnet.type === 'database' ? 'selected' : ''}>Database</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-xs font-medium text-gray-700 mb-1">AZ</label>
                        <div class="flex gap-2">
                            <input
                                type="text"
                                class="subnet-az flex-1 px-3 py-2 border border-gray-300 rounded text-sm"
                                value="${subnet.az || ''}"
                                placeholder="Optional"
                                data-index="${index}"
                            />
                            <button
                                class="remove-subnet px-3 py-2 bg-red-600 text-white rounded hover:bg-red-700 text-sm"
                                data-index="${index}"
                            >
                                ×
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');

        // Event Listeners für Subnet-Inputs
        container.querySelectorAll('.subnet-name').forEach(input => {
            input.addEventListener('input', (e) => {
                const index = parseInt(e.target.dataset.index);
                this.subnets[index].name = e.target.value;
            });
        });

        container.querySelectorAll('.subnet-cidr').forEach(input => {
            input.addEventListener('input', (e) => {
                const index = parseInt(e.target.dataset.index);
                this.subnets[index].cidr = e.target.value;
                this.updateCalculateButton();
            });
        });

        container.querySelectorAll('.subnet-type').forEach(select => {
            select.addEventListener('change', (e) => {
                const index = parseInt(e.target.dataset.index);
                this.subnets[index].type = e.target.value;
            });
        });

        container.querySelectorAll('.subnet-az').forEach(input => {
            input.addEventListener('input', (e) => {
                const index = parseInt(e.target.dataset.index);
                this.subnets[index].az = e.target.value || null;
            });
        });

        container.querySelectorAll('.remove-subnet').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const index = parseInt(e.target.dataset.index);
                this.removeSubnet(index);
            });
        });
    }

    /**
     * Entfernt ein Subnet
     */
    removeSubnet(index) {
        this.subnets.splice(index, 1);
        this.renderSubnetList();
        this.updateCalculateButton();
    }

    /**
     * Aktualisiert den Calculate-Button
     */
    updateCalculateButton() {
        const btn = document.getElementById('calculatePlanBtn');
        if (!btn) return;

        const hasValidSubnets = this.subnets.length > 0 &&
            this.subnets.every(s => s.cidr && s.cidr.trim() !== '');

        btn.disabled = !hasValidSubnets;
    }

    /**
     * Berechnet den VPC Plan
     */
    async calculatePlan() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/cidr/plan`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    vpc_cidr: this.vpcCidr,
                    subnets: this.subnets
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Fehler beim Berechnen');
            }

            this.vpcPlan = await response.json();
            this.renderVisualPlan(this.vpcPlan);
        } catch (error) {
            this.showError(`Fehler beim Berechnen: ${error.message}`);
        }
    }

    /**
     * Rendert den visuellen VPC Plan
     */
    renderVisualPlan(plan) {
        const container = document.getElementById('visualPlan');
        container.classList.remove('hidden');

        const allocatedPercent = ((plan.total_ips - plan.unallocated_ips) / plan.total_ips * 100).toFixed(1);

        container.innerHTML = `
            <div class="bg-white border-2 border-gray-300 rounded-lg p-6">
                <h3 class="text-xl font-semibold mb-4">VPC Plan: ${plan.vpc_cidr}</h3>

                ${plan.has_overlaps ? `
                    <div class="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
                        <h4 class="font-semibold text-red-800 mb-2">⚠️ Overlaps erkannt!</h4>
                        <ul class="list-disc list-inside space-y-1 text-sm text-red-700">
                            ${plan.overlap_details.map(detail => `<li>${detail}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}

                <!-- IP Allocation Overview -->
                <div class="mb-6">
                    <div class="flex justify-between text-sm mb-2">
                        <span class="font-medium">IP Allocation</span>
                        <span class="text-gray-600">${allocatedPercent}% verwendet</span>
                    </div>
                    <div class="w-full h-6 bg-gray-200 rounded-full overflow-hidden">
                        <div
                            class="h-full ${plan.has_overlaps ? 'bg-red-500' : 'bg-green-500'}"
                            style="width: ${allocatedPercent}%"
                        ></div>
                    </div>
                    <div class="flex justify-between text-xs text-gray-600 mt-1">
                        <span>${(plan.total_ips - plan.unallocated_ips).toLocaleString()} IPs allocated</span>
                        <span>${plan.unallocated_ips.toLocaleString()} IPs frei</span>
                    </div>
                </div>

                <!-- Subnet Details -->
                <div class="space-y-3">
                    <h4 class="font-semibold text-gray-900">Subnets (${plan.subnets.length})</h4>
                    ${plan.subnets.map(subnet => this.renderSubnetCard(subnet)).join('')}
                </div>

                <!-- Summary Stats -->
                <div class="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t border-gray-200">
                    <div class="text-center">
                        <div class="text-2xl font-bold text-purple-600">${plan.subnets.length}</div>
                        <div class="text-xs text-gray-600">Subnets</div>
                    </div>
                    <div class="text-center">
                        <div class="text-2xl font-bold text-green-600">${plan.subnets.reduce((sum, s) => sum + s.usable_ips, 0).toLocaleString()}</div>
                        <div class="text-xs text-gray-600">Usable IPs</div>
                    </div>
                    <div class="text-center">
                        <div class="text-2xl font-bold text-gray-600">${plan.unallocated_ips.toLocaleString()}</div>
                        <div class="text-xs text-gray-600">Unallocated</div>
                    </div>
                    <div class="text-center">
                        <div class="text-2xl font-bold ${plan.has_overlaps ? 'text-red-600' : 'text-green-600'}">
                            ${plan.has_overlaps ? '✗' : '✓'}
                        </div>
                        <div class="text-xs text-gray-600">Status</div>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Rendert eine Subnet-Karte
     */
    renderSubnetCard(subnet) {
        const typeColors = {
            public: 'bg-blue-50 border-blue-200',
            private: 'bg-purple-50 border-purple-200',
            database: 'bg-orange-50 border-orange-200'
        };

        const typeBadgeColors = {
            public: 'bg-blue-500',
            private: 'bg-purple-500',
            database: 'bg-orange-500'
        };

        return `
            <div class="subnet-card border-2 rounded-lg p-4 ${typeColors[subnet.subnet_type] || 'bg-gray-50 border-gray-200'}">
                <div class="flex justify-between items-start mb-2">
                    <div>
                        <h5 class="font-semibold text-gray-900">${subnet.name}</h5>
                        <p class="text-sm text-gray-600 font-mono">${subnet.cidr}</p>
                    </div>
                    <span class="px-2 py-1 text-xs font-medium text-white rounded ${typeBadgeColors[subnet.subnet_type] || 'bg-gray-500'}">
                        ${subnet.subnet_type}
                    </span>
                </div>

                <div class="grid grid-cols-2 gap-3 text-sm">
                    <div>
                        <span class="text-gray-600">Total IPs:</span>
                        <span class="font-medium ml-1">${subnet.total_ips.toLocaleString()}</span>
                    </div>
                    <div>
                        <span class="text-gray-600">Usable:</span>
                        <span class="font-medium ml-1">${subnet.usable_ips.toLocaleString()}</span>
                    </div>
                    ${subnet.availability_zone ? `
                        <div class="col-span-2">
                            <span class="text-gray-600">AZ:</span>
                            <span class="font-medium ml-1">${subnet.availability_zone}</span>
                        </div>
                    ` : ''}
                </div>

                <div class="mt-3 pt-3 border-t border-gray-200">
                    <details class="text-xs">
                        <summary class="cursor-pointer text-gray-600 hover:text-gray-900">
                            Reserved IPs (${subnet.reserved_ips.length})
                        </summary>
                        <ul class="mt-2 space-y-1 font-mono text-gray-700">
                            ${subnet.reserved_ips.map((ip, idx) => {
                                const labels = ['Network', 'VPC Router', 'DNS', 'Reserved', 'Broadcast'];
                                return `<li class="text-xs">${ip} <span class="text-gray-500">(${labels[idx] || 'Reserved'})</span></li>`;
                            }).join('')}
                        </ul>
                    </details>
                </div>
            </div>
        `;
    }

    /**
     * Zeigt Erfolgsmeldung an
     */
    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    /**
     * Zeigt Fehlermeldung an
     */
    showError(message) {
        this.showNotification(message, 'error');
    }

    /**
     * Zeigt Notification an
     */
    showNotification(message, type = 'info') {
        const colors = {
            success: 'bg-green-500',
            error: 'bg-red-500',
            info: 'bg-blue-500'
        };

        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 ${colors[type]} text-white px-6 py-3 rounded-lg shadow-lg z-50 transition-opacity`;
        notification.textContent = message;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.style.opacity = '0';
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, 3000);
    }
}
