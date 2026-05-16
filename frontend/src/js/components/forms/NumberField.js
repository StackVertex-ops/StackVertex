/**
 * NumberField - Smart Number Input mit Min/Max Validation
 */

import { SmartFormField } from './SmartFormField.js';

export class NumberField extends SmartFormField {
    /**
     * @param {Object} config
     * @param {number} [config.min] - Minimum Value
     * @param {number} [config.max] - Maximum Value
     * @param {number} [config.step] - Step Size
     */
    constructor(config) {
        super(config);

        // Parse value als Number
        if (this.value !== '') {
            this.value = parseFloat(this.value);
        }
    }

    createInputElement() {
        const input = document.createElement('input');
        input.type = 'number';

        if (this.config.validation?.min !== undefined) {
            input.min = this.config.validation.min;
        }

        if (this.config.validation?.max !== undefined) {
            input.max = this.config.validation.max;
        }

        if (this.config.step !== undefined) {
            input.step = this.config.step;
        }

        return input;
    }

    handleInput(e) {
        const numValue = parseFloat(e.target.value);
        this.value = isNaN(numValue) ? '' : numValue;
        this.clearMessages();
    }

    async validate() {
        this.clearMessages();

        if (this.value === '') {
            return true;
        }

        // Client-Side Validation
        if (this.config.validation?.min !== undefined && this.value < this.config.validation.min) {
            this.errors.push(`Wert muss mindestens ${this.config.validation.min} sein`);
            return false;
        }

        if (this.config.validation?.max !== undefined && this.value > this.config.validation.max) {
            this.errors.push(`Wert darf maximal ${this.config.validation.max} sein`);
            return false;
        }

        return true;
    }
}
