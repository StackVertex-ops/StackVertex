/**
 * CIDRField - Smart CIDR Block Input für VPC/Subnets
 *
 * Features:
 * - Validiert CIDR Format
 * - Prüft AWS VPC Constraints (/16 - /28)
 * - Berechnet Total IPs und Usable IPs
 * - Zeigt AWS Reserved IPs
 */

import { SmartFormField } from './SmartFormField.js';

export class CIDRField extends SmartFormField {
    constructor(config) {
        super(config);
    }

    createInputElement() {
        const input = document.createElement('input');
        input.type = 'text';
        input.placeholder = 'z.B. 10.0.0.0/16';
        return input;
    }

    async validate() {
        this.clearMessages();

        if (!this.value) {
            return true;
        }

        // Call Backend Validation API
        const result = await this.callValidationAPI('/validate-cidr', {
            cidr: this.value
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

        // Zeige CIDR Details wenn valide
        if (this.isValid() && this.metadata.total_ips) {
            const messagesContainer = this.element.querySelector('.field-messages');

            const detailsDiv = document.createElement('div');
            detailsDiv.className = 'cidr-details';
            detailsDiv.innerHTML = `
                <div class="detail-grid">
                    <div class="detail-item">
                        <span class="detail-label">Total IPs:</span>
                        <span class="detail-value">${this.metadata.total_ips.toLocaleString()}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Nutzbare IPs:</span>
                        <span class="detail-value">${this.metadata.usable_ips.toLocaleString()}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">AWS Reserviert:</span>
                        <span class="detail-value">${this.metadata.aws_reserved_ips}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Prefix:</span>
                        <span class="detail-value">/${this.metadata.prefix}</span>
                    </div>
                </div>
                <div class="cidr-info">
                    <p class="text-sm text-gray-600 mt-2">
                        AWS reserviert in jedem Subnet die ersten 4 IPs und die letzte IP für interne Zwecke.
                    </p>
                </div>
            `;

            messagesContainer.appendChild(detailsDiv);
        }
    }
}
