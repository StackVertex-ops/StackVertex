/**
 * Component Palette
 *
 * Draggable AWS Components die auf das Canvas gezogen werden können
 */

export class ComponentPalette {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.render();
    }

    render() {
        this.container.innerHTML = `
            <div class="component-palette">
                <h3 class="text-lg font-semibold text-gray-900 mb-4">Components</h3>

                <!-- Network Components -->
                <div class="palette-section mb-4">
                    <h4 class="text-sm font-medium text-gray-700 mb-2">Network</h4>
                    <div class="grid grid-cols-2 gap-2">
                        ${this.renderComponent('vpc', 'VPC', '🌐')}
                        ${this.renderComponent('subnet', 'Subnet', '📦')}
                        ${this.renderComponent('igw', 'Internet Gateway', '🌍')}
                        ${this.renderComponent('nat', 'NAT Gateway', '🔀')}
                    </div>
                </div>

                <!-- Compute Components -->
                <div class="palette-section mb-4">
                    <h4 class="text-sm font-medium text-gray-700 mb-2">Compute</h4>
                    <div class="grid grid-cols-2 gap-2">
                        ${this.renderComponent('ec2', 'EC2', '🖥️')}
                        ${this.renderComponent('lambda', 'Lambda', 'λ')}
                        ${this.renderComponent('ecs', 'ECS', '🐳')}
                        ${this.renderComponent('alb', 'Load Balancer', '⚖️')}
                    </div>
                </div>

                <!-- Data Components -->
                <div class="palette-section mb-4">
                    <h4 class="text-sm font-medium text-gray-700 mb-2">Data</h4>
                    <div class="grid grid-cols-2 gap-2">
                        ${this.renderComponent('rds', 'RDS', '💾')}
                        ${this.renderComponent('dynamodb', 'DynamoDB', '⚡')}
                        ${this.renderComponent('s3', 'S3', '📁')}
                        ${this.renderComponent('elasticache', 'ElastiCache', '🔄')}
                    </div>
                </div>

                <!-- Security Components -->
                <div class="palette-section">
                    <h4 class="text-sm font-medium text-gray-700 mb-2">Security</h4>
                    <div class="grid grid-cols-2 gap-2">
                        ${this.renderComponent('sg', 'Security Group', '🛡️')}
                        ${this.renderComponent('nacl', 'Network ACL', '🔒')}
                        ${this.renderComponent('iam', 'IAM Role', '👤')}
                    </div>
                </div>
            </div>
        `;

        this.attachDragListeners();
    }

    renderComponent(type, name, icon) {
        return `
            <div
                class="palette-component"
                draggable="true"
                data-component-type="${type}"
            >
                <div class="component-icon">${icon}</div>
                <div class="component-name">${name}</div>
            </div>
        `;
    }

    attachDragListeners() {
        const components = this.container.querySelectorAll('.palette-component');

        components.forEach(comp => {
            comp.addEventListener('dragstart', (e) => {
                const type = comp.dataset.componentType;
                e.dataTransfer.setData('componentType', type);
                e.dataTransfer.effectAllowed = 'copy';

                // Visual feedback
                comp.classList.add('opacity-50');
            });

            comp.addEventListener('dragend', (e) => {
                comp.classList.remove('opacity-50');
            });
        });
    }
}
