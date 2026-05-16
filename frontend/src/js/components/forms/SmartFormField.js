/**
 * SmartFormField - Base Class für intelligente Form Fields
 *
 * Features:
 * - Live Validation gegen Backend
 * - AWS Constraint Checking
 * - Errors, Warnings, Suggestions
 * - Cost Impact Anzeige
 */

const API_BASE_URL = '/api/v1';

export class SmartFormField {
    /**
     * @param {Object} config - Field Configuration
     * @param {string} config.name - Field Name
     * @param {string} config.label - Display Label
     * @param {string} config.type - Field Type (text, number, etc.)
     * @param {*} config.default - Default Value
     * @param {string} [config.description] - Help Text
     * @param {Object} [config.validation] - Validation Rules
     */
    constructor(config) {
        this.config = config;
        this.value = config.default !== undefined ? config.default : '';
        this.errors = [];
        this.warnings = [];
        this.suggestions = [];
        this.metadata = {};
        this.isValidating = false;
        this.element = null;
        this.inputElement = null;
    }

    /**
     * Validiert den aktuellen Wert gegen Backend
     * @returns {Promise<boolean>} True wenn valide
     */
    async validate() {
        // Basis-Implementierung - überschreiben in Subclasses
        return true;
    }

    /**
     * Rendert das Form Field
     * @returns {HTMLElement} Field Element
     */
    render() {
        const container = document.createElement('div');
        container.className = 'form-field';
        container.dataset.fieldName = this.config.name;

        // Label
        const label = document.createElement('label');
        label.className = 'form-label';
        label.textContent = this.config.label;
        label.htmlFor = `field-${this.config.name}`;
        container.appendChild(label);

        // Input Container
        const inputContainer = document.createElement('div');
        inputContainer.className = 'input-container';

        // Input Element
        const input = this.createInputElement();
        input.id = `field-${this.config.name}`;
        input.className = 'form-input';
        input.value = this.value;

        // Event Listeners
        input.addEventListener('input', (e) => this.handleInput(e));
        input.addEventListener('blur', () => this.handleBlur());

        inputContainer.appendChild(input);
        container.appendChild(inputContainer);

        // Messages Container
        const messagesContainer = document.createElement('div');
        messagesContainer.className = 'field-messages';
        container.appendChild(messagesContainer);

        // Description/Hint
        if (this.config.description) {
            const hint = document.createElement('p');
            hint.className = 'field-hint';
            hint.textContent = this.config.description;
            container.appendChild(hint);
        }

        this.element = container;
        this.inputElement = input;

        return container;
    }

    /**
     * Erstellt das Input-Element (überschreiben in Subclasses)
     * @returns {HTMLElement}
     */
    createInputElement() {
        const input = document.createElement('input');
        input.type = this.config.type || 'text';
        return input;
    }

    /**
     * Handler für Input-Event
     * @param {Event} e
     */
    handleInput(e) {
        this.value = e.target.value;
        this.clearMessages();
    }

    /**
     * Handler für Blur-Event (Validierung)
     */
    async handleBlur() {
        if (this.value) {
            await this.validate();
            this.renderMessages();
        }
    }

    /**
     * Löscht alle Nachrichten
     */
    clearMessages() {
        this.errors = [];
        this.warnings = [];
        this.suggestions = [];
        this.metadata = {};

        if (this.element) {
            const messagesContainer = this.element.querySelector('.field-messages');
            if (messagesContainer) {
                messagesContainer.innerHTML = '';
            }

            // Remove error state
            this.inputElement?.classList.remove('has-error');
        }
    }

    /**
     * Rendert Errors, Warnings, Suggestions
     */
    renderMessages() {
        if (!this.element) return;

        const messagesContainer = this.element.querySelector('.field-messages');
        if (!messagesContainer) return;

        messagesContainer.innerHTML = '';

        // Errors
        if (this.errors.length > 0) {
            this.inputElement.classList.add('has-error');

            this.errors.forEach(error => {
                const errorDiv = document.createElement('div');
                errorDiv.className = 'error-message';
                errorDiv.innerHTML = `
                    <svg class="message-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                    </svg>
                    <span>${error}</span>
                `;
                messagesContainer.appendChild(errorDiv);
            });
        } else {
            this.inputElement.classList.remove('has-error');
        }

        // Warnings
        this.warnings.forEach(warning => {
            const warningDiv = document.createElement('div');
            warningDiv.className = 'warning-message';
            warningDiv.innerHTML = `
                <svg class="message-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
                </svg>
                <span>${warning}</span>
            `;
            messagesContainer.appendChild(warningDiv);
        });

        // Suggestions
        this.suggestions.forEach(suggestion => {
            const suggestionDiv = document.createElement('div');
            suggestionDiv.className = 'suggestion-message';
            suggestionDiv.innerHTML = `
                <svg class="message-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
                <span>${suggestion}</span>
            `;
            messagesContainer.appendChild(suggestionDiv);
        });

        // Metadata (z.B. Cost)
        if (this.metadata.estimated_monthly_cost_usd !== undefined) {
            const costDiv = document.createElement('div');
            costDiv.className = 'cost-indicator';
            costDiv.innerHTML = `
                <svg class="message-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
                <span>Ca. $${this.metadata.estimated_monthly_cost_usd}/Monat</span>
            `;
            messagesContainer.appendChild(costDiv);
        }
    }

    /**
     * Gibt aktuellen Wert zurück
     * @returns {*}
     */
    getValue() {
        return this.value;
    }

    /**
     * Setzt neuen Wert
     * @param {*} value
     */
    setValue(value) {
        this.value = value;
        if (this.inputElement) {
            this.inputElement.value = value;
        }
    }

    /**
     * Prüft ob Field valide ist
     * @returns {boolean}
     */
    isValid() {
        return this.errors.length === 0;
    }

    /**
     * Hilfsfunktion für API Calls
     * @param {string} endpoint
     * @param {Object} data
     * @returns {Promise<Object>}
     */
    async callValidationAPI(endpoint, data) {
        this.isValidating = true;

        try {
            const response = await fetch(`${API_BASE_URL}${endpoint}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                throw new Error(`Validation API error: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Validation API call failed:', error);
            return {
                valid: false,
                errors: ['Validierung fehlgeschlagen - bitte später erneut versuchen'],
                warnings: [],
                suggestions: [],
                metadata: {}
            };
        } finally {
            this.isValidating = false;
        }
    }
}
