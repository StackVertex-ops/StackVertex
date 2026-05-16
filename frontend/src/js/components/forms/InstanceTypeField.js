/**
 * InstanceTypeField - Smart EC2 Instance Type Selector
 *
 * Features:
 * - Autocomplete/Dropdown mit allen Instance Types
 * - Zeigt vCPUs, RAM, Network, Preis
 * - Filterable nach Familie (t3, m5, c5, r5)
 * - Use-Case basierte Empfehlungen
 */

import { SmartFormField } from './SmartFormField.js';

export class InstanceTypeField extends SmartFormField {
    /**
     * @param {Object} config
     * @param {string} [config.useCase] - Use Case für Empfehlungen
     */
    constructor(config) {
        super(config);
        this.useCase = config.useCase || '';
        this.instanceTypes = null;
        this.filteredTypes = null;
        this.selectedType = null;
        this.dropdownOpen = false;
    }

    async loadInstanceTypes() {
        if (this.instanceTypes) {
            return;
        }

        try {
            const response = await fetch('/api/v1/instance-types');
            const data = await response.json();
            this.instanceTypes = data.instance_types || {};
            this.filteredTypes = this.instanceTypes;
        } catch (error) {
            console.error('Failed to load instance types:', error);
            this.instanceTypes = {};
            this.filteredTypes = {};
        }
    }

    render() {
        const container = document.createElement('div');
        container.className = 'form-field instance-type-field';
        container.dataset.fieldName = this.config.name;

        // Label
        const label = document.createElement('label');
        label.className = 'form-label';
        label.textContent = this.config.label;
        container.appendChild(label);

        // Input Container (Autocomplete-Style)
        const inputContainer = document.createElement('div');
        inputContainer.className = 'input-container autocomplete-container';

        // Input
        const input = document.createElement('input');
        input.type = 'text';
        input.className = 'form-input';
        input.placeholder = 'z.B. t3.micro, m5.large...';
        input.value = this.value;
        input.autocomplete = 'off';

        // Event Listeners
        input.addEventListener('input', (e) => this.handleInput(e));
        input.addEventListener('focus', () => this.showDropdown());
        input.addEventListener('blur', () => {
            // Delay to allow click on dropdown
            setTimeout(() => this.hideDropdown(), 200);
            this.handleBlur();
        });

        inputContainer.appendChild(input);

        // Dropdown für Instance Types
        const dropdown = document.createElement('div');
        dropdown.className = 'instance-dropdown hidden';
        inputContainer.appendChild(dropdown);

        container.appendChild(inputContainer);

        // Messages Container
        const messagesContainer = document.createElement('div');
        messagesContainer.className = 'field-messages';
        container.appendChild(messagesContainer);

        // Description
        if (this.config.description) {
            const hint = document.createElement('p');
            hint.className = 'field-hint';
            hint.textContent = this.config.description;
            container.appendChild(hint);
        }

        this.element = container;
        this.inputElement = input;

        // Load instance types
        this.loadInstanceTypes().then(() => {
            if (this.value) {
                this.validate().then(() => this.renderMessages());
            }
        });

        return container;
    }

    handleInput(e) {
        this.value = e.target.value;
        this.clearMessages();
        this.filterInstanceTypes(this.value);
        this.renderDropdown();
        this.showDropdown();
    }

    filterInstanceTypes(query) {
        if (!this.instanceTypes) {
            this.filteredTypes = {};
            return;
        }

        const lowerQuery = query.toLowerCase();

        if (!lowerQuery) {
            this.filteredTypes = this.instanceTypes;
            return;
        }

        this.filteredTypes = {};

        Object.entries(this.instanceTypes).forEach(([name, type]) => {
            if (name.toLowerCase().includes(lowerQuery)) {
                this.filteredTypes[name] = type;
            }
        });
    }

    showDropdown() {
        const dropdown = this.element.querySelector('.instance-dropdown');
        if (dropdown) {
            dropdown.classList.remove('hidden');
            this.dropdownOpen = true;
            this.renderDropdown();
        }
    }

    hideDropdown() {
        const dropdown = this.element.querySelector('.instance-dropdown');
        if (dropdown) {
            dropdown.classList.add('hidden');
            this.dropdownOpen = false;
        }
    }

    renderDropdown() {
        const dropdown = this.element.querySelector('.instance-dropdown');
        if (!dropdown || !this.filteredTypes) return;

        dropdown.innerHTML = '';

        const typeEntries = Object.entries(this.filteredTypes);

        if (typeEntries.length === 0) {
            dropdown.innerHTML = '<div class="dropdown-empty">Keine Instance Types gefunden</div>';
            return;
        }

        // Limit to first 10
        const displayTypes = typeEntries.slice(0, 10);

        displayTypes.forEach(([name, type]) => {
            const item = document.createElement('div');
            item.className = 'instance-dropdown-item';

            item.innerHTML = `
                <div class="instance-name">${name}</div>
                <div class="instance-specs">
                    ${type.vcpus} vCPUs • ${type.memory_gb} GB RAM • $${type.price_per_hour_usd}/h
                </div>
                <div class="instance-use-cases">${type.use_cases.slice(0, 2).join(', ')}</div>
            `;

            item.addEventListener('click', () => {
                this.selectInstanceType(name, type);
            });

            dropdown.appendChild(item);
        });

        if (typeEntries.length > 10) {
            const more = document.createElement('div');
            more.className = 'dropdown-info';
            more.textContent = `${typeEntries.length - 10} weitere...`;
            dropdown.appendChild(more);
        }
    }

    selectInstanceType(name, type) {
        this.value = name;
        this.selectedType = type;
        this.inputElement.value = name;

        this.hideDropdown();

        // Validate
        this.validate().then(() => this.renderMessages());
    }

    async validate() {
        this.clearMessages();

        if (!this.value) {
            return true;
        }

        // Call Backend Validation API
        const result = await this.callValidationAPI('/validate-instance-type', {
            instance_type: this.value,
            use_case: this.useCase
        });

        // Update State
        this.errors = result.errors || [];
        this.warnings = result.warnings || [];
        this.suggestions = result.suggestions || [];
        this.metadata = result.metadata || {};

        return result.valid;
    }

    renderMessages() {
        super.renderMessages();

        // Zeige zusätzliche Instance Details wenn valide
        if (this.isValid() && this.metadata.vcpus) {
            const messagesContainer = this.element.querySelector('.field-messages');

            const detailsDiv = document.createElement('div');
            detailsDiv.className = 'instance-details';
            detailsDiv.innerHTML = `
                <div class="detail-grid">
                    <div class="detail-item">
                        <span class="detail-label">vCPUs:</span>
                        <span class="detail-value">${this.metadata.vcpus}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Memory:</span>
                        <span class="detail-value">${this.metadata.memory_gb} GB</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Network:</span>
                        <span class="detail-value">${this.metadata.network_performance}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Kosten:</span>
                        <span class="detail-value">$${this.metadata.price_per_hour_usd}/h (~$${this.metadata.estimated_monthly_cost_usd}/Monat)</span>
                    </div>
                </div>
            `;

            messagesContainer.appendChild(detailsDiv);
        }
    }

    /**
     * Setzt Use Case (triggert Re-Validation)
     * @param {string} useCase
     */
    setUseCase(useCase) {
        this.useCase = useCase;

        if (this.value) {
            this.validate().then(() => this.renderMessages());
        }
    }
}
