/**
 * FormBuilder - Orchestrator für Smart Forms
 *
 * Erstellt Form Fields aus Blueprint Schema und koordiniert Validation
 */

import { SmartFormField } from './SmartFormField.js';
import { NumberField } from './NumberField.js';
import { StorageSizeField } from './StorageSizeField.js';
import { InstanceTypeField } from './InstanceTypeField.js';
import { CIDRField } from './CIDRField.js';
import { LiveCostPanel } from '../LiveCostPanel.js';

export class FormBuilder {
    /**
     * @param {Object} blueprint - Blueprint mit form_schema
     * @param {Array} blueprint.form_schema - Array von Field Configs
     */
    constructor(blueprint) {
        this.blueprint = blueprint;
        this.fields = [];
        this.fieldMap = new Map(); // name -> field
        this.onChangeCallbacks = [];
        this.costPanel = null; // Wird initialisiert wenn Blueprint ID vorhanden

        // Initialize Cost Panel wenn Blueprint metadata vorhanden
        if (blueprint.metadata && blueprint.metadata.id) {
            this.costPanel = new LiveCostPanel(blueprint.metadata.id);
        }

        this.initFields();
    }

    /**
     * Initialisiert alle Form Fields aus Blueprint Schema
     */
    initFields() {
        if (!this.blueprint.form_schema || !Array.isArray(this.blueprint.form_schema)) {
            console.warn('Blueprint hat kein form_schema');
            return;
        }

        this.blueprint.form_schema.forEach(fieldConfig => {
            const field = this.createField(fieldConfig);

            if (field) {
                this.fields.push(field);
                this.fieldMap.set(fieldConfig.name, field);
            }
        });
    }

    /**
     * Erstellt passendes Field basierend auf Type
     * @param {Object} config - Field Config
     * @returns {SmartFormField|null}
     */
    createField(config) {
        let field;

        switch (config.type) {
            case 'storage':
                field = new StorageSizeField(config);
                break;

            case 'instance_type':
                field = new InstanceTypeField(config);
                break;

            case 'cidr':
                field = new CIDRField(config);
                break;

            case 'number':
                field = new NumberField(config);
                break;

            case 'text':
            case 'email':
            case 'url':
                field = new SmartFormField(config);
                break;

            case 'select':
                field = this.createSelectField(config);
                break;

            default:
                console.warn(`Unbekannter Field Type: ${config.type}`);
                field = new SmartFormField(config);
        }

        return field;
    }

    /**
     * Erstellt Select/Dropdown Field
     * @param {Object} config
     * @returns {SmartFormField}
     */
    createSelectField(config) {
        const field = new SmartFormField(config);

        // Override createInputElement für Select
        field.createInputElement = function () {
            const select = document.createElement('select');
            select.className = 'form-select';

            // Default Option
            if (config.placeholder) {
                const defaultOption = document.createElement('option');
                defaultOption.value = '';
                defaultOption.textContent = config.placeholder;
                select.appendChild(defaultOption);
            }

            // Options
            if (config.options && Array.isArray(config.options)) {
                config.options.forEach(option => {
                    const opt = document.createElement('option');
                    opt.value = option.value;
                    opt.textContent = option.label || option.value;
                    select.appendChild(opt);
                });
            }

            return select;
        };

        return field;
    }

    /**
     * Validiert alle Fields
     * @returns {Promise<boolean>} True wenn alle valide
     */
    async validateAll() {
        const results = await Promise.all(
            this.fields.map(field => field.validate())
        );

        // Render messages for all fields
        this.fields.forEach(field => field.renderMessages());

        return results.every(result => result === true);
    }

    /**
     * Gibt Form-Daten als Object zurück
     * @returns {Object} Field name -> value
     */
    getData() {
        const data = {};

        this.fields.forEach(field => {
            data[field.config.name] = field.getValue();
        });

        return data;
    }

    /**
     * Setzt Form-Daten
     * @param {Object} data - Field name -> value
     */
    setData(data) {
        Object.entries(data).forEach(([name, value]) => {
            const field = this.fieldMap.get(name);
            if (field) {
                field.setValue(value);
            }
        });
    }

    /**
     * Rendert das komplette Form
     * @returns {HTMLElement}
     */
    render() {
        const container = document.createElement('div');
        container.className = 'blueprint-form';

        // Group Fields by Section (optional)
        const sections = this.groupFieldsBySections();

        if (sections.length > 1) {
            // Render with sections
            sections.forEach(section => {
                const sectionElement = this.renderSection(section);
                container.appendChild(sectionElement);
            });
        } else {
            // Render flat
            this.fields.forEach(field => {
                const fieldElement = field.render();

                // Listen to changes
                fieldElement.addEventListener('change', () => {
                    this.handleFieldChange(field);
                });

                container.appendChild(fieldElement);
            });
        }

        return container;
    }

    /**
     * Gruppiert Fields nach Sections (falls vorhanden)
     * @returns {Array<{title: string, fields: Array}>}
     */
    groupFieldsBySections() {
        const sections = [];
        let currentSection = {
            title: null,
            fields: []
        };

        this.fields.forEach(field => {
            if (field.config.section) {
                // Neue Section
                if (currentSection.fields.length > 0) {
                    sections.push(currentSection);
                }

                currentSection = {
                    title: field.config.section,
                    fields: [field]
                };
            } else {
                currentSection.fields.push(field);
            }
        });

        if (currentSection.fields.length > 0) {
            sections.push(currentSection);
        }

        return sections;
    }

    /**
     * Rendert eine Form Section
     * @param {Object} section
     * @returns {HTMLElement}
     */
    renderSection(section) {
        const sectionElement = document.createElement('div');
        sectionElement.className = 'form-section';

        if (section.title) {
            const title = document.createElement('h3');
            title.className = 'form-section-title';
            title.textContent = section.title;
            sectionElement.appendChild(title);
        }

        section.fields.forEach(field => {
            const fieldElement = field.render();

            // Listen to changes
            fieldElement.addEventListener('change', () => {
                this.handleFieldChange(field);
            });

            sectionElement.appendChild(fieldElement);
        });

        return sectionElement;
    }

    /**
     * Handler wenn Field sich ändert
     * @param {SmartFormField} field
     */
    handleFieldChange(field) {
        // Trigger callbacks
        this.onChangeCallbacks.forEach(callback => {
            callback(field, this.getData());
        });

        // Handle field dependencies
        this.handleFieldDependencies(field);

        // Update live cost estimation
        this.updateLiveCost();
    }

    /**
     * Updated Live Cost Estimation basierend auf aktuellen Form-Daten
     */
    updateLiveCost() {
        if (!this.costPanel) {
            return;
        }

        const formData = this.getData();
        this.costPanel.updateCost(formData);
    }

    /**
     * Handle Field Dependencies (z.B. RDS Engine -> Storage)
     * @param {SmartFormField} changedField
     */
    handleFieldDependencies(changedField) {
        const fieldName = changedField.config.name;

        // Example: Wenn RDS Engine sich ändert, update Storage Field
        if (fieldName === 'rds_engine') {
            const storageField = this.fieldMap.get('storage_size');

            if (storageField && storageField instanceof StorageSizeField) {
                storageField.setEngine(changedField.getValue());
            }
        }

        // Example: Wenn Use Case sich ändert, update Instance Type Field
        if (fieldName === 'use_case') {
            const instanceField = this.fieldMap.get('instance_type');

            if (instanceField && instanceField instanceof InstanceTypeField) {
                instanceField.setUseCase(changedField.getValue());
            }
        }
    }

    /**
     * Registriert Callback für Field Changes
     * @param {Function} callback - (field, allData) => void
     */
    onChange(callback) {
        this.onChangeCallbacks.push(callback);
    }

    /**
     * Holt ein Field by Name
     * @param {string} name
     * @returns {SmartFormField|undefined}
     */
    getField(name) {
        return this.fieldMap.get(name);
    }

    /**
     * Prüft ob Form valide ist
     * @returns {boolean}
     */
    isValid() {
        return this.fields.every(field => field.isValid());
    }

    /**
     * Returned alle Errors aus allen Fields
     * @returns {Array<{field: string, errors: Array<string>}>}
     */
    getAllErrors() {
        return this.fields
            .filter(field => !field.isValid())
            .map(field => ({
                field: field.config.name,
                label: field.config.label,
                errors: field.errors
            }));
    }

    /**
     * Reset Form zu Default Values
     */
    reset() {
        this.fields.forEach(field => {
            field.setValue(field.config.default || '');
            field.clearMessages();
            field.renderMessages();
        });

        // Reset cost panel
        if (this.costPanel) {
            this.costPanel.reset();
        }
    }

    /**
     * Gibt Cost Panel zurück (für externe Verwendung)
     * @returns {LiveCostPanel|null}
     */
    getCostPanel() {
        return this.costPanel;
    }

    /**
     * Rendert Cost Panel initial (muss manuell aufgerufen werden)
     * Trigger initial cost calculation mit Default Values
     */
    renderCostPanel() {
        if (this.costPanel) {
            this.costPanel.render();
            // Trigger initial calculation
            this.updateLiveCost();
        }
    }

    /**
     * Zeigt Validation Errors für alle Fields
     */
    async showValidation() {
        await this.validateAll();

        // Scroll to first error
        const firstInvalidField = this.fields.find(field => !field.isValid());

        if (firstInvalidField && firstInvalidField.element) {
            firstInvalidField.element.scrollIntoView({
                behavior: 'smooth',
                block: 'center'
            });
        }
    }
}
