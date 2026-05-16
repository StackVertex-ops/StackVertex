/**
 * StorageSizeField - Smart Storage Size Input mit AWS Constraints
 *
 * Validiert gegen AWS Service Limits (RDS, EBS, S3)
 */

import { NumberField } from './NumberField.js';

export class StorageSizeField extends NumberField {
    /**
     * @param {Object} config
     * @param {string} config.serviceType - AWS Service (rds, ebs, s3)
     * @param {string} [config.unit] - Einheit (GB, TB) - Default: GB
     * @param {string} [config.engine] - RDS Engine (nur für RDS)
     */
    constructor(config) {
        super(config);
        this.serviceType = config.serviceType || 'rds';
        this.unit = config.unit || 'GB';
        this.engine = config.engine || 'mysql';
    }

    render() {
        const container = super.render();

        // Füge Unit-Badge zum Input hinzu
        const inputContainer = container.querySelector('.input-container');

        // Wrap input in group
        const inputGroup = document.createElement('div');
        inputGroup.className = 'input-group';

        const input = inputContainer.querySelector('.form-input');
        inputContainer.removeChild(input);

        inputGroup.appendChild(input);

        // Unit Badge
        const unitBadge = document.createElement('span');
        unitBadge.className = 'unit-badge';
        unitBadge.textContent = this.unit;

        inputGroup.appendChild(unitBadge);
        inputContainer.appendChild(inputGroup);

        return container;
    }

    async validate() {
        this.clearMessages();

        if (this.value === '' || this.value <= 0) {
            this.errors.push('Bitte gültige Storage Size eingeben');
            return false;
        }

        // Call Backend Validation API
        const result = await this.callValidationAPI('/validate-storage', {
            service: this.serviceType,
            size: this.value,
            unit: this.unit,
            engine: this.serviceType === 'rds' ? this.engine : undefined
        });

        // Update State
        this.errors = result.errors || [];
        this.warnings = result.warnings || [];
        this.suggestions = result.suggestions || [];
        this.metadata = result.metadata || {};

        return result.valid;
    }

    /**
     * Setzt RDS Engine (für RDS Storage)
     * @param {string} engine
     */
    setEngine(engine) {
        this.engine = engine;

        // Re-validate wenn bereits Wert vorhanden
        if (this.value) {
            this.validate().then(() => this.renderMessages());
        }
    }
}
