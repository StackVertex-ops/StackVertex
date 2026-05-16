/**
 * OverCloud - AI Advisor Component
 *
 * Intelligente Empfehlungen & Warnungen für Architecture Building
 */

/**
 * Analysiert die Architecture und gibt Empfehlungen
 * @param {Object} architecture - Architecture JSON
 * @returns {Array<Object>} Array of recommendations
 */
export function analyzeArchitecture(architecture) {
    const recommendations = [];

    if (!architecture || !architecture.architecture) {
        return recommendations;
    }

    const components = architecture.architecture.components || [];
    const relationships = architecture.architecture.relationships || [];

    // Security Checks
    recommendations.push(...checkSecurity(components, relationships));

    // Cost Optimization
    recommendations.push(...checkCostOptimization(components));

    // Best Practices
    recommendations.push(...checkBestPractices(components, relationships));

    // Performance Checks
    recommendations.push(...checkPerformance(components, relationships));

    // High Availability
    recommendations.push(...checkHighAvailability(components));

    return recommendations;
}

/**
 * Security Checks
 */
function checkSecurity(components, relationships) {
    const warnings = [];

    // Check for unencrypted RDS
    components.forEach(comp => {
        if (comp.provider_service === 'rds') {
            if (comp.config?.storage_encrypted === false) {
                warnings.push({
                    type: 'security',
                    severity: 'high',
                    component: comp.id,
                    title: 'Unverschlüsselte Datenbank',
                    message: `RDS Instance "${comp.name}" hat keine Storage-Verschlüsselung aktiviert. Das ist ein Sicherheitsrisiko.`,
                    suggestion: 'Aktiviere Storage-Verschlüsselung in den Properties.',
                    icon: '🔒'
                });
            }
        }
    });

    // Check for S3 without encryption
    components.forEach(comp => {
        if (comp.provider_service === 's3') {
            if (!comp.config?.encryption || comp.config?.encryption === 'none') {
                warnings.push({
                    type: 'security',
                    severity: 'medium',
                    component: comp.id,
                    title: 'Unverschlüsselter S3 Bucket',
                    message: `S3 Bucket "${comp.name}" hat keine Verschlüsselung aktiviert.`,
                    suggestion: 'Aktiviere AES-256 oder KMS Verschlüsselung.',
                    icon: '🪣'
                });
            }
        }
    });

    // Check for public EC2 instances without VPC
    const hasVPC = components.some(c => c.provider_service === 'vpc');
    const ec2Instances = components.filter(c => c.provider_service === 'ec2');

    if (ec2Instances.length > 0 && !hasVPC) {
        warnings.push({
            type: 'security',
            severity: 'high',
            component: null,
            title: 'EC2 Instances ohne VPC',
            message: 'EC2 Instances sollten in einem VPC laufen, nicht im Default VPC.',
            suggestion: 'Füge ein VPC hinzu und verbinde die EC2 Instances damit.',
            icon: '🌐'
        });
    }

    // Check for databases without backup
    components.forEach(comp => {
        if (comp.provider_service === 'rds' || comp.provider_service === 'dynamodb') {
            if (!comp.config?.backup_enabled && comp.config?.backup_enabled !== true) {
                warnings.push({
                    type: 'security',
                    severity: 'medium',
                    component: comp.id,
                    title: 'Kein Backup konfiguriert',
                    message: `Datenbank "${comp.name}" hat kein automatisches Backup aktiviert.`,
                    suggestion: 'Aktiviere automatische Backups mit Retention Period von mindestens 7 Tagen.',
                    icon: '💾'
                });
            }
        }
    });

    return warnings;
}

/**
 * Cost Optimization Checks
 */
function checkCostOptimization(components) {
    const recommendations = [];

    // Check for over-provisioned EC2
    components.forEach(comp => {
        if (comp.provider_service === 'ec2') {
            const instanceType = comp.config?.instance_type;
            if (instanceType && (instanceType.includes('xlarge') || instanceType.includes('2xlarge'))) {
                recommendations.push({
                    type: 'cost',
                    severity: 'low',
                    component: comp.id,
                    title: 'Teure Instance Type',
                    message: `EC2 Instance "${comp.name}" nutzt ${instanceType}. Das ist teuer.`,
                    suggestion: 'Prüfe ob eine kleinere Instance (t3.medium oder t3.large) ausreicht.',
                    icon: '💰'
                });
            }
        }
    });

    // Check for RDS without reserved instances hint
    components.forEach(comp => {
        if (comp.provider_service === 'rds') {
            if (comp.config?.multi_az) {
                recommendations.push({
                    type: 'cost',
                    severity: 'info',
                    component: comp.id,
                    title: 'Reserved Instances Potenzial',
                    message: `Multi-AZ RDS "${comp.name}" läuft dauerhaft. Reserved Instances sparen bis zu 60%.`,
                    suggestion: 'Erwäge Reserved Instances für 1-3 Jahre.',
                    icon: '💡'
                });
            }
        }
    });

    // Check for S3 without lifecycle rules
    components.forEach(comp => {
        if (comp.provider_service === 's3') {
            if (!comp.config?.lifecycle_rules || comp.config?.lifecycle_rules?.length === 0) {
                recommendations.push({
                    type: 'cost',
                    severity: 'low',
                    component: comp.id,
                    title: 'Keine Lifecycle Rules',
                    message: `S3 Bucket "${comp.name}" hat keine Lifecycle Rules. Alte Daten bleiben teuer.`,
                    suggestion: 'Konfiguriere Lifecycle Rules: Transition nach Glacier nach 90 Tagen, Deletion nach 365 Tagen.',
                    icon: '📦'
                });
            }
        }
    });

    return recommendations;
}

/**
 * Best Practices Checks
 */
function checkBestPractices(components, relationships) {
    const recommendations = [];

    // Check for missing load balancer with multiple EC2
    const ec2Count = components.filter(c => c.provider_service === 'ec2').length;
    const hasALB = components.some(c => c.provider_service === 'alb' || c.provider_service === 'nlb');

    if (ec2Count >= 2 && !hasALB) {
        recommendations.push({
            type: 'best-practice',
            severity: 'medium',
            component: null,
            title: 'Fehlender Load Balancer',
            message: `Du hast ${ec2Count} EC2 Instances, aber keinen Load Balancer.`,
            suggestion: 'Füge einen Application Load Balancer (ALB) hinzu für bessere Verfügbarkeit.',
            icon: '⚖️'
        });
    }

    // Check for isolated components (no relationships)
    const connectedComponents = new Set();
    relationships.forEach(rel => {
        connectedComponents.add(rel.from);
        connectedComponents.add(rel.to);
    });

    components.forEach(comp => {
        if (!connectedComponents.has(comp.id) && comp.provider_service !== 'vpc') {
            recommendations.push({
                type: 'best-practice',
                severity: 'low',
                component: comp.id,
                title: 'Isolierte Komponente',
                message: `Component "${comp.name}" ist nicht mit anderen Components verbunden.`,
                suggestion: 'Verbinde die Component mit anderen Services oder entferne sie.',
                icon: '🔌'
            });
        }
    });

    // Check for database without monitoring
    components.forEach(comp => {
        if (comp.provider_service === 'rds' || comp.provider_service === 'dynamodb') {
            const hasCloudWatch = components.some(c =>
                c.provider_service === 'cloudwatch' &&
                relationships.some(r => r.from === c.id && r.to === comp.id)
            );

            if (!hasCloudWatch) {
                recommendations.push({
                    type: 'best-practice',
                    severity: 'medium',
                    component: comp.id,
                    title: 'Kein Monitoring',
                    message: `Datenbank "${comp.name}" hat kein CloudWatch Monitoring.`,
                    suggestion: 'Füge CloudWatch Alarms hinzu für CPU, Storage und Connections.',
                    icon: '📊'
                });
            }
        }
    });

    return recommendations;
}

/**
 * Performance Checks
 */
function checkPerformance(components, relationships) {
    const recommendations = [];

    // Check for RDS with low storage
    components.forEach(comp => {
        if (comp.provider_service === 'rds') {
            const storage = comp.config?.allocated_storage || 0;
            if (storage < 100) {
                recommendations.push({
                    type: 'performance',
                    severity: 'low',
                    component: comp.id,
                    title: 'Wenig Storage',
                    message: `RDS "${comp.name}" hat nur ${storage} GB Storage. Das könnte knapp werden.`,
                    suggestion: 'Erhöhe auf mindestens 100 GB für bessere IOPS.',
                    icon: '💾'
                });
            }
        }
    });

    // Check for Lambda without provisioned concurrency
    components.forEach(comp => {
        if (comp.provider_service === 'lambda') {
            if (!comp.config?.provisioned_concurrency) {
                recommendations.push({
                    type: 'performance',
                    severity: 'info',
                    component: comp.id,
                    title: 'Cold Start Risiko',
                    message: `Lambda "${comp.name}" könnte Cold Starts haben.`,
                    suggestion: 'Erwäge Provisioned Concurrency für konsistente Latenz.',
                    icon: '⚡'
                });
            }
        }
    });

    return recommendations;
}

/**
 * High Availability Checks
 */
function checkHighAvailability(components) {
    const recommendations = [];

    // Check for single EC2 instance
    const ec2Count = components.filter(c => c.provider_service === 'ec2').length;
    if (ec2Count === 1) {
        recommendations.push({
            type: 'availability',
            severity: 'medium',
            component: null,
            title: 'Single Point of Failure',
            message: 'Du hast nur eine EC2 Instance. Bei Ausfall ist der Service down.',
            suggestion: 'Füge mindestens eine zweite EC2 Instance in einer anderen AZ hinzu.',
            icon: '⚠️'
        });
    }

    // Check for RDS without Multi-AZ
    components.forEach(comp => {
        if (comp.provider_service === 'rds') {
            if (!comp.config?.multi_az) {
                recommendations.push({
                    type: 'availability',
                    severity: 'high',
                    component: comp.id,
                    title: 'Keine Multi-AZ',
                    message: `RDS "${comp.name}" läuft nur in einer AZ. Das ist ein Risiko.`,
                    suggestion: 'Aktiviere Multi-AZ für automatisches Failover bei AZ-Ausfall.',
                    icon: '🏗️'
                });
            }
        }
    });

    return recommendations;
}

/**
 * Rendert das AI Advisor Panel
 * @param {HTMLElement} container - Container Element
 * @param {Object} architecture - Current Architecture
 */
export function renderAIAdvisor(container, architecture, initiallyCollapsed = true) {
    const recommendations = analyzeArchitecture(architecture);

    // Group by severity
    const high = recommendations.filter(r => r.severity === 'high');
    const medium = recommendations.filter(r => r.severity === 'medium');
    const low = recommendations.filter(r => r.severity === 'low');
    const info = recommendations.filter(r => r.severity === 'info');

    container.innerHTML = `
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow-md">
            <!-- Header -->
            <div class="p-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
                <div class="flex items-center space-x-2">
                    <span class="text-2xl">🤖</span>
                    <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
                        AI Advisor
                    </h3>
                </div>
                <button id="collapse-advisor" class="text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white">
                    ${recommendations.length === 0 ? 'Keine Empfehlungen' : `${recommendations.length} Empfehlungen`}
                </button>
            </div>

            <!-- Content -->
            <div id="advisor-content" class="${initiallyCollapsed ? 'hidden ' : ''}p-4 space-y-3 max-h-96 overflow-y-auto">
                ${recommendations.length === 0 ? renderEmptyState() : ''}
                ${high.length > 0 ? renderRecommendationGroup('Kritisch', high, 'red') : ''}
                ${medium.length > 0 ? renderRecommendationGroup('Wichtig', medium, 'yellow') : ''}
                ${low.length > 0 ? renderRecommendationGroup('Optimierung', low, 'blue') : ''}
                ${info.length > 0 ? renderRecommendationGroup('Tipp', info, 'green') : ''}
            </div>
        </div>
    `;

    // Setup event handlers
    setupAdvisorHandlers(container);
}

/**
 * Rendert Empty State
 */
function renderEmptyState() {
    return `
        <div class="text-center py-8">
            <div class="text-4xl mb-2">✅</div>
            <p class="text-sm text-gray-600 dark:text-gray-400">
                Alles sieht gut aus! Keine Warnungen oder Empfehlungen.
            </p>
        </div>
    `;
}

/**
 * Rendert eine Gruppe von Empfehlungen
 */
function renderRecommendationGroup(title, recommendations, color) {
    const colorClasses = {
        red: 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800',
        yellow: 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800',
        blue: 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800',
        green: 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800'
    };

    return `
        <div class="space-y-2">
            <h4 class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                ${title}
            </h4>
            ${recommendations.map(rec => renderRecommendation(rec, colorClasses[color])).join('')}
        </div>
    `;
}

/**
 * Rendert eine einzelne Empfehlung
 */
function renderRecommendation(rec, colorClass) {
    return `
        <div class="border ${colorClass} rounded-lg p-3 recommendation-item" data-component="${rec.component || ''}">
            <div class="flex items-start space-x-2">
                <span class="text-lg flex-shrink-0">${rec.icon}</span>
                <div class="flex-1 min-w-0">
                    <h5 class="text-sm font-medium text-gray-900 dark:text-white mb-1">
                        ${rec.title}
                    </h5>
                    <p class="text-xs text-gray-600 dark:text-gray-400 mb-2">
                        ${rec.message}
                    </p>
                    <div class="bg-white dark:bg-gray-700 rounded px-2 py-1 text-xs text-gray-700 dark:text-gray-300 border border-gray-200 dark:border-gray-600">
                        <span class="font-medium">💡 Tipp:</span> ${rec.suggestion}
                    </div>
                </div>
            </div>
        </div>
    `;
}

/**
 * Setup Event Handlers
 */
function setupAdvisorHandlers(container) {
    // Collapse Advisor (internal collapse button)
    const collapseBtn = container.querySelector('#collapse-advisor');
    const content = container.querySelector('#advisor-content');

    if (collapseBtn) {
        collapseBtn.addEventListener('click', () => {
            content.classList.toggle('hidden');
        });
    }

    // Highlight component on recommendation click
    const recommendations = container.querySelectorAll('.recommendation-item');
    recommendations.forEach(item => {
        const componentId = item.dataset.component;
        if (componentId) {
            item.addEventListener('click', () => {
                // Dispatch event to highlight component on canvas
                window.dispatchEvent(new CustomEvent('highlight-component', {
                    detail: { componentId }
                }));
            });
            item.classList.add('cursor-pointer', 'hover:opacity-80', 'transition-opacity');
        }
    });
}
