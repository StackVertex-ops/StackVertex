/**
 * StackVertex - Properties Panel
 *
 * Rechtes Panel für Konfiguration von Component-Properties
 */

/**
 * Rendert das Properties Panel
 * @param {HTMLElement} container - Container-Element
 * @param {Object} component - Selektierte Component (oder null)
 * @param {Function} onPropertyChange - Callback wenn Property sich ändert
 */
export function renderPropertiesPanel(container, component = null, onPropertyChange) {
    if (!component) {
        // No component selected
        container.innerHTML = renderEmptyState();
        return;
    }

    container.innerHTML = `
        <div class="flex flex-col h-full">
            <!-- Header -->
            <div class="p-4 border-b border-gray-200 dark:border-gray-700">
                <div class="flex items-center space-x-2 mb-2">
                    <span class="text-2xl">${component.icon}</span>
                    <h2 class="text-lg font-semibold text-gray-900 dark:text-white">
                        ${component.name}
                    </h2>
                </div>
                <div class="text-xs text-gray-500 dark:text-gray-400">
                    ${component.provider_service} • ${component.type}
                </div>
            </div>

            <!-- Properties Form -->
            <div class="flex-1 overflow-y-auto p-4">
                ${renderPropertiesForm(component)}
            </div>

            <!-- Actions -->
            <div class="p-4 border-t border-gray-200 dark:border-gray-700">
                <button
                    id="apply-properties-btn"
                    class="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                >
                    Änderungen übernehmen
                </button>
            </div>
        </div>
    `;

    // Setup Event Handlers
    setupPropertiesHandlers(container, component, onPropertyChange);
}

/**
 * Rendert Empty State
 */
function renderEmptyState() {
    return `
        <div class="flex items-center justify-center h-full p-6 text-center">
            <div>
                <div class="text-4xl mb-3">⚙️</div>
                <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                    Keine Component ausgewählt
                </h3>
                <p class="text-sm text-gray-600 dark:text-gray-400">
                    Wähle eine Component aus der Canvas, um ihre Properties zu bearbeiten
                </p>
            </div>
        </div>
    `;
}

/**
 * Rendert Properties Form basierend auf Component-Typ
 */
function renderPropertiesForm(component) {
    // Basic Properties (immer vorhanden)
    const basicFields = `
        <div class="space-y-4">
            <h3 class="text-sm font-medium text-gray-700 dark:text-gray-300 border-b border-gray-200 dark:border-gray-700 pb-2">
                Grundlegende Eigenschaften
            </h3>

            <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Component ID
                </label>
                <input
                    type="text"
                    id="prop-id"
                    value="${component.id}"
                    readonly
                    class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-gray-50 dark:bg-gray-900 text-gray-500 dark:text-gray-400 text-sm cursor-not-allowed"
                />
            </div>

            <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Display Name
                </label>
                <input
                    type="text"
                    id="prop-name"
                    value="${component.name || ''}"
                    class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500"
                    placeholder="z.B. Main Database"
                />
            </div>
        </div>
    `;

    // Service-specific Properties
    const serviceFields = renderServiceSpecificFields(component);

    return basicFields + serviceFields;
}

/**
 * Rendert Service-spezifische Fields
 */
function renderServiceSpecificFields(component) {
    const config = component.configuration || {};

    switch (component.provider_service) {
        case 'vpc':
            return renderVPCFields(config);
        case 'ec2':
            return renderEC2Fields(config);
        case 'rds':
            return renderRDSFields(config);
        case 's3':
            return renderS3Fields(config);
        case 'lambda':
            return renderLambdaFields(config);
        case 'alb':
            return renderALBFields(config);
        case 'dynamodb':
            return renderDynamoDBFields(config);
        default:
            return renderGenericFields(config);
    }
}

/**
 * VPC Fields
 */
function renderVPCFields(config) {
    return `
        <div class="space-y-4 mt-6">
            <h3 class="text-sm font-medium text-gray-700 dark:text-gray-300 border-b border-gray-200 dark:border-gray-700 pb-2">
                VPC Konfiguration
            </h3>

            <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    CIDR Block
                </label>
                <input
                    type="text"
                    id="prop-cidr-block"
                    value="${config.cidr_block || '10.0.0.0/16'}"
                    class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500"
                    placeholder="10.0.0.0/16"
                />
            </div>

            <div>
                <label class="flex items-center">
                    <input
                        type="checkbox"
                        id="prop-enable-dns"
                        ${config.enable_dns_hostnames ? 'checked' : ''}
                        class="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    />
                    <span class="ml-2 text-sm text-gray-700 dark:text-gray-300">DNS Hostnames aktivieren</span>
                </label>
            </div>
        </div>
    `;
}

/**
 * EC2 Fields
 */
function renderEC2Fields(config) {
    return `
        <div class="space-y-4 mt-6">
            <h3 class="text-sm font-medium text-gray-700 dark:text-gray-300 border-b border-gray-200 dark:border-gray-700 pb-2">
                EC2 Konfiguration
            </h3>

            <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Instance Type
                </label>
                <select
                    id="prop-instance-type"
                    class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500"
                >
                    <option value="t3.micro" ${config.instance_type === 't3.micro' ? 'selected' : ''}>t3.micro (1 vCPU, 1 GB RAM)</option>
                    <option value="t3.small" ${config.instance_type === 't3.small' ? 'selected' : ''}>t3.small (2 vCPU, 2 GB RAM)</option>
                    <option value="t3.medium" ${config.instance_type === 't3.medium' ? 'selected' : ''}>t3.medium (2 vCPU, 4 GB RAM)</option>
                    <option value="t3.large" ${config.instance_type === 't3.large' ? 'selected' : ''}>t3.large (2 vCPU, 8 GB RAM)</option>
                    <option value="m5.large" ${config.instance_type === 'm5.large' ? 'selected' : ''}>m5.large (2 vCPU, 8 GB RAM)</option>
                    <option value="m5.xlarge" ${config.instance_type === 'm5.xlarge' ? 'selected' : ''}>m5.xlarge (4 vCPU, 16 GB RAM)</option>
                </select>
            </div>

            <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    AMI ID
                </label>
                <input
                    type="text"
                    id="prop-ami"
                    value="${config.ami || ''}"
                    class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500"
                    placeholder="ami-0c55b159cbfafe1f0"
                />
            </div>
        </div>
    `;
}

/**
 * RDS Fields
 */
function renderRDSFields(config) {
    return `
        <div class="space-y-4 mt-6">
            <h3 class="text-sm font-medium text-gray-700 dark:text-gray-300 border-b border-gray-200 dark:border-gray-700 pb-2">
                RDS Konfiguration
            </h3>

            <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Engine
                </label>
                <select
                    id="prop-engine"
                    class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500"
                >
                    <option value="postgres" ${config.engine === 'postgres' ? 'selected' : ''}>PostgreSQL</option>
                    <option value="mysql" ${config.engine === 'mysql' ? 'selected' : ''}>MySQL</option>
                    <option value="mariadb" ${config.engine === 'mariadb' ? 'selected' : ''}>MariaDB</option>
                </select>
            </div>

            <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Instance Class
                </label>
                <select
                    id="prop-instance-class"
                    class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500"
                >
                    <option value="db.t3.micro" ${config.instance_class === 'db.t3.micro' ? 'selected' : ''}>db.t3.micro</option>
                    <option value="db.t3.small" ${config.instance_class === 'db.t3.small' ? 'selected' : ''}>db.t3.small</option>
                    <option value="db.t3.medium" ${config.instance_class === 'db.t3.medium' ? 'selected' : ''}>db.t3.medium</option>
                </select>
            </div>

            <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Allocated Storage (GB)
                </label>
                <input
                    type="number"
                    id="prop-allocated-storage"
                    value="${config.allocated_storage || 20}"
                    min="20"
                    class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500"
                />
            </div>

            <div>
                <label class="flex items-center">
                    <input
                        type="checkbox"
                        id="prop-multi-az"
                        ${config.multi_az ? 'checked' : ''}
                        class="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    />
                    <span class="ml-2 text-sm text-gray-700 dark:text-gray-300">Multi-AZ Deployment</span>
                </label>
            </div>

            <div>
                <label class="flex items-center">
                    <input
                        type="checkbox"
                        id="prop-storage-encrypted"
                        ${config.storage_encrypted !== false ? 'checked' : ''}
                        class="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    />
                    <span class="ml-2 text-sm text-gray-700 dark:text-gray-300">Storage Verschlüsselung</span>
                </label>
            </div>
        </div>
    `;
}

/**
 * S3 Fields
 */
function renderS3Fields(config) {
    return `
        <div class="space-y-4 mt-6">
            <h3 class="text-sm font-medium text-gray-700 dark:text-gray-300 border-b border-gray-200 dark:border-gray-700 pb-2">
                S3 Konfiguration
            </h3>

            <div>
                <label class="flex items-center">
                    <input
                        type="checkbox"
                        id="prop-versioning"
                        ${config.versioning_enabled ? 'checked' : ''}
                        class="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    />
                    <span class="ml-2 text-sm text-gray-700 dark:text-gray-300">Versioning aktivieren</span>
                </label>
            </div>

            <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Encryption
                </label>
                <select
                    id="prop-encryption"
                    class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500"
                >
                    <option value="none" ${!config.encryption ? 'selected' : ''}>Keine</option>
                    <option value="AES256" ${config.encryption === 'AES256' ? 'selected' : ''}>AES256</option>
                    <option value="aws:kms" ${config.encryption === 'aws:kms' ? 'selected' : ''}>AWS KMS</option>
                </select>
            </div>

            <div>
                <label class="flex items-center">
                    <input
                        type="checkbox"
                        id="prop-public-access"
                        ${config.public_access_block === false ? 'checked' : ''}
                        class="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    />
                    <span class="ml-2 text-sm text-gray-700 dark:text-gray-300">Öffentlicher Zugriff erlauben</span>
                </label>
            </div>
        </div>
    `;
}

/**
 * Lambda Fields
 */
function renderLambdaFields(config) {
    return `
        <div class="space-y-4 mt-6">
            <h3 class="text-sm font-medium text-gray-700 dark:text-gray-300 border-b border-gray-200 dark:border-gray-700 pb-2">
                Lambda Konfiguration
            </h3>

            <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Runtime
                </label>
                <select
                    id="prop-runtime"
                    class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500"
                >
                    <option value="nodejs18.x" ${config.runtime === 'nodejs18.x' ? 'selected' : ''}>Node.js 18.x</option>
                    <option value="python3.11" ${config.runtime === 'python3.11' ? 'selected' : ''}>Python 3.11</option>
                    <option value="python3.9" ${config.runtime === 'python3.9' ? 'selected' : ''}>Python 3.9</option>
                </select>
            </div>

            <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Memory (MB)
                </label>
                <input
                    type="number"
                    id="prop-memory"
                    value="${config.memory_mb || 256}"
                    min="128"
                    max="10240"
                    step="64"
                    class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500"
                />
            </div>

            <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Timeout (Sekunden)
                </label>
                <input
                    type="number"
                    id="prop-timeout"
                    value="${config.timeout_seconds || 30}"
                    min="1"
                    max="900"
                    class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500"
                />
            </div>
        </div>
    `;
}

/**
 * ALB Fields
 */
function renderALBFields(config) {
    return `
        <div class="space-y-4 mt-6">
            <h3 class="text-sm font-medium text-gray-700 dark:text-gray-300 border-b border-gray-200 dark:border-gray-700 pb-2">
                ALB Konfiguration
            </h3>

            <div>
                <label class="flex items-center">
                    <input
                        type="checkbox"
                        id="prop-internal"
                        ${config.internal ? 'checked' : ''}
                        class="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    />
                    <span class="ml-2 text-sm text-gray-700 dark:text-gray-300">Internal Load Balancer</span>
                </label>
            </div>
        </div>
    `;
}

/**
 * DynamoDB Fields
 */
function renderDynamoDBFields(config) {
    return `
        <div class="space-y-4 mt-6">
            <h3 class="text-sm font-medium text-gray-700 dark:text-gray-300 border-b border-gray-200 dark:border-gray-700 pb-2">
                DynamoDB Konfiguration
            </h3>

            <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Billing Mode
                </label>
                <select
                    id="prop-billing-mode"
                    class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500"
                >
                    <option value="PAY_PER_REQUEST" ${config.billing_mode === 'PAY_PER_REQUEST' ? 'selected' : ''}>Pay Per Request</option>
                    <option value="PROVISIONED" ${config.billing_mode === 'PROVISIONED' ? 'selected' : ''}>Provisioned</option>
                </select>
            </div>

            <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Hash Key
                </label>
                <input
                    type="text"
                    id="prop-hash-key"
                    value="${config.hash_key || 'id'}"
                    class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500"
                />
            </div>
        </div>
    `;
}

/**
 * Generic Fields (für unbekannte Services)
 */
function renderGenericFields(config) {
    return `
        <div class="space-y-4 mt-6">
            <h3 class="text-sm font-medium text-gray-700 dark:text-gray-300 border-b border-gray-200 dark:border-gray-700 pb-2">
                Konfiguration
            </h3>
            <div class="text-sm text-gray-600 dark:text-gray-400">
                Für diesen Service-Typ sind noch keine spezifischen Properties definiert.
            </div>
        </div>
    `;
}

/**
 * Setup Event Handlers
 */
function setupPropertiesHandlers(container, component, onPropertyChange) {
    const applyBtn = container.querySelector('#apply-properties-btn');

    if (applyBtn) {
        applyBtn.addEventListener('click', () => {
            const updatedProperties = extractProperties(container, component);

            if (onPropertyChange) {
                onPropertyChange(component.id, updatedProperties);
            }
        });
    }
}

/**
 * Extrahiere Properties aus dem Formular
 */
function extractProperties(container, component) {
    const properties = {
        name: container.querySelector('#prop-name')?.value || component.name,
        configuration: {}
    };

    // Service-specific extraction
    switch (component.provider_service) {
        case 'vpc':
            properties.configuration.cidr_block = container.querySelector('#prop-cidr-block')?.value;
            properties.configuration.enable_dns_hostnames = container.querySelector('#prop-enable-dns')?.checked;
            break;
        case 'ec2':
            properties.configuration.instance_type = container.querySelector('#prop-instance-type')?.value;
            properties.configuration.ami = container.querySelector('#prop-ami')?.value;
            break;
        case 'rds':
            properties.configuration.engine = container.querySelector('#prop-engine')?.value;
            properties.configuration.instance_class = container.querySelector('#prop-instance-class')?.value;
            properties.configuration.allocated_storage = parseInt(container.querySelector('#prop-allocated-storage')?.value);
            properties.configuration.multi_az = container.querySelector('#prop-multi-az')?.checked;
            properties.configuration.storage_encrypted = container.querySelector('#prop-storage-encrypted')?.checked;
            break;
        case 's3':
            properties.configuration.versioning_enabled = container.querySelector('#prop-versioning')?.checked;
            properties.configuration.encryption = container.querySelector('#prop-encryption')?.value;
            properties.configuration.public_access_block = !container.querySelector('#prop-public-access')?.checked;
            break;
        case 'lambda':
            properties.configuration.runtime = container.querySelector('#prop-runtime')?.value;
            properties.configuration.memory_mb = parseInt(container.querySelector('#prop-memory')?.value);
            properties.configuration.timeout_seconds = parseInt(container.querySelector('#prop-timeout')?.value);
            break;
        case 'alb':
            properties.configuration.internal = container.querySelector('#prop-internal')?.checked;
            break;
        case 'dynamodb':
            properties.configuration.billing_mode = container.querySelector('#prop-billing-mode')?.value;
            properties.configuration.hash_key = container.querySelector('#prop-hash-key')?.value;
            break;
    }

    return properties;
}
