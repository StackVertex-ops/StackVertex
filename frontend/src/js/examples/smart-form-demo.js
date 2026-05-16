/**
 * Smart Form Demo / Integration Example
 *
 * Zeigt wie man Smart Forms in Blueprints integriert
 */

import { FormBuilder } from '../components/forms/FormBuilder.js';

/**
 * Beispiel: RDS Database Blueprint Form
 *
 * Demonstriert alle Features:
 * - Storage Size Validation (AWS RDS Limits)
 * - Instance Type Selection
 * - CIDR Validation
 * - Live Cost Calculation
 * - Field Dependencies
 */
export async function renderRDSBlueprintForm(container) {
    // Blueprint-Definition (normalerweise von Backend)
    const blueprint = {
        id: 'rds-mysql',
        name: 'RDS MySQL Database',
        description: 'Managed MySQL Database mit AWS RDS',
        form_schema: [
            {
                name: 'database_name',
                label: 'Database Name',
                type: 'text',
                default: 'mydb',
                description: 'Name der Datenbank (alphanumerisch, 3-63 Zeichen)',
                validation: {
                    required: true,
                    pattern: '^[a-z0-9-]+$',
                    minLength: 3,
                    maxLength: 63
                }
            },
            {
                name: 'rds_engine',
                label: 'Database Engine',
                type: 'select',
                default: 'mysql',
                description: 'Welche Database Engine soll verwendet werden?',
                options: [
                    { value: 'mysql', label: 'MySQL 8.0' },
                    { value: 'postgres', label: 'PostgreSQL 15' },
                    { value: 'mariadb', label: 'MariaDB 10.11' },
                    { value: 'aurora-mysql', label: 'Aurora MySQL (Serverless)' },
                    { value: 'aurora-postgresql', label: 'Aurora PostgreSQL (Serverless)' }
                ]
            },
            {
                name: 'instance_type',
                label: 'RDS Instance Class',
                type: 'instance_type',
                default: 'db.t3.micro',
                description: 'Instance-Typ für die Datenbank',
                useCase: 'database'
            },
            {
                name: 'storage_size',
                label: 'Storage Size',
                type: 'storage',
                serviceType: 'rds',
                unit: 'GB',
                default: 20,
                description: 'Wie viel Storage benötigen Sie?',
                validation: {
                    min: 20,
                    max: 1000
                }
            },
            {
                name: 'vpc_cidr',
                label: 'VPC CIDR Block',
                type: 'cidr',
                default: '10.0.0.0/16',
                description: 'CIDR Block für das VPC',
                section: 'Netzwerk'
            },
            {
                name: 'subnet_cidr',
                label: 'Subnet CIDR Block',
                type: 'cidr',
                default: '10.0.1.0/24',
                description: 'CIDR Block für das Subnet',
                section: 'Netzwerk'
            },
            {
                name: 'multi_az',
                label: 'Multi-AZ Deployment',
                type: 'select',
                default: 'false',
                description: 'Hochverfügbarkeit über mehrere Availability Zones?',
                section: 'Hochverfügbarkeit',
                options: [
                    { value: 'false', label: 'Nein (Single-AZ)' },
                    { value: 'true', label: 'Ja (Multi-AZ, höhere Kosten)' }
                ]
            },
            {
                name: 'backup_retention_days',
                label: 'Backup Retention',
                type: 'number',
                default: 7,
                description: 'Wie lange sollen Backups aufbewahrt werden? (Tage)',
                section: 'Backup & Recovery',
                validation: {
                    min: 0,
                    max: 35
                },
                step: 1
            }
        ]
    };

    // FormBuilder initialisieren
    const formBuilder = new FormBuilder(blueprint);

    // Render Form
    const formElement = formBuilder.render();

    // Live Cost Calculation
    formBuilder.onChange((field, allData) => {
        console.log(`Field ${field.config.name} changed:`, field.getValue());
        console.log('All Data:', allData);

        // Update Cost Estimate (simplified)
        updateCostEstimate(formBuilder, allData);
    });

    // Submit Handler
    const submitButton = document.createElement('button');
    submitButton.className = 'mt-6 w-full bg-purple-600 text-white font-semibold py-3 px-6 rounded-lg hover:bg-purple-700 transition-colors';
    submitButton.textContent = 'Architektur erstellen';

    submitButton.addEventListener('click', async () => {
        const isValid = await formBuilder.validateAll();

        if (isValid) {
            const data = formBuilder.getData();
            console.log('Form submitted:', data);

            // Hier würde man normalerweise Architecture erstellen
            alert('Architektur würde jetzt erstellt werden!\n\n' + JSON.stringify(data, null, 2));
        } else {
            const errors = formBuilder.getAllErrors();
            console.error('Form has errors:', errors);

            alert('Bitte behebe zunächst die Validierungsfehler:\n\n' +
                errors.map(e => `${e.label}: ${e.errors.join(', ')}`).join('\n')
            );

            // Scroll to first error
            formBuilder.showValidation();
        }
    });

    // Build Layout
    container.innerHTML = '';

    const pageHeader = document.createElement('div');
    pageHeader.className = 'mb-6';
    pageHeader.innerHTML = `
        <h1 class="text-3xl font-bold text-gray-900 mb-2">
            ${blueprint.name}
        </h1>
        <p class="text-gray-600">
            ${blueprint.description}
        </p>
    `;

    const formCard = document.createElement('div');
    formCard.className = 'bg-white rounded-lg shadow-md p-6';
    formCard.appendChild(formElement);
    formCard.appendChild(submitButton);

    // Cost Estimate Panel
    const costPanel = document.createElement('div');
    costPanel.id = 'cost-estimate-panel';
    costPanel.className = 'bg-blue-50 border border-blue-200 rounded-lg p-4 mt-4';
    costPanel.innerHTML = `
        <h3 class="font-semibold text-blue-900 mb-2">Geschätzte monatliche Kosten</h3>
        <div class="text-2xl font-bold text-blue-700">$0.00</div>
        <p class="text-sm text-blue-600 mt-1">Kosten können je nach Nutzung variieren</p>
    `;

    formCard.appendChild(costPanel);

    container.appendChild(pageHeader);
    container.appendChild(formCard);

    return formBuilder;
}

/**
 * Update Cost Estimate (simplified demo)
 */
function updateCostEstimate(formBuilder, data) {
    const costPanel = document.getElementById('cost-estimate-panel');
    if (!costPanel) return;

    // Get metadata from fields
    const instanceField = formBuilder.getField('instance_type');
    const storageField = formBuilder.getField('storage_size');

    let totalCost = 0;

    // Instance Cost
    if (instanceField && instanceField.metadata.estimated_monthly_cost_usd) {
        totalCost += instanceField.metadata.estimated_monthly_cost_usd;
    }

    // Storage Cost
    if (storageField && storageField.metadata.estimated_monthly_cost_usd) {
        totalCost += storageField.metadata.estimated_monthly_cost_usd;
    }

    // Multi-AZ doubles instance cost
    if (data.multi_az === 'true' && instanceField?.metadata.estimated_monthly_cost_usd) {
        totalCost += instanceField.metadata.estimated_monthly_cost_usd;
    }

    // Update UI
    const costValue = costPanel.querySelector('.text-2xl');
    if (costValue) {
        costValue.textContent = `$${totalCost.toFixed(2)}`;
    }
}

/**
 * Beispiel: Lambda Function Blueprint Form
 */
export async function renderLambdaBlueprintForm(container) {
    const blueprint = {
        id: 'lambda-function',
        name: 'AWS Lambda Function',
        description: 'Serverless Function auf AWS Lambda',
        form_schema: [
            {
                name: 'function_name',
                label: 'Function Name',
                type: 'text',
                default: 'my-function',
                description: 'Name der Lambda Function',
                validation: {
                    required: true,
                    pattern: '^[a-zA-Z0-9-_]+$'
                }
            },
            {
                name: 'runtime',
                label: 'Runtime',
                type: 'select',
                default: 'python3.11',
                options: [
                    { value: 'python3.11', label: 'Python 3.11' },
                    { value: 'python3.10', label: 'Python 3.10' },
                    { value: 'nodejs20.x', label: 'Node.js 20' },
                    { value: 'nodejs18.x', label: 'Node.js 18' },
                    { value: 'java17', label: 'Java 17' },
                    { value: 'go1.x', label: 'Go 1.x' }
                ]
            },
            {
                name: 'memory',
                label: 'Memory (MB)',
                type: 'number',
                default: 128,
                description: 'Memory-Allocation für die Function',
                validation: {
                    min: 128,
                    max: 10240
                },
                step: 64
            },
            {
                name: 'timeout',
                label: 'Timeout (Sekunden)',
                type: 'number',
                default: 30,
                description: 'Maximum Execution Time',
                validation: {
                    min: 1,
                    max: 900
                }
            }
        ]
    };

    const formBuilder = new FormBuilder(blueprint);
    const formElement = formBuilder.render();

    container.innerHTML = `
        <div class="mb-6">
            <h1 class="text-3xl font-bold text-gray-900 mb-2">
                ${blueprint.name}
            </h1>
            <p class="text-gray-600">
                ${blueprint.description}
            </p>
        </div>
    `;

    const formCard = document.createElement('div');
    formCard.className = 'bg-white rounded-lg shadow-md p-6';
    formCard.appendChild(formElement);

    container.appendChild(formCard);

    return formBuilder;
}
