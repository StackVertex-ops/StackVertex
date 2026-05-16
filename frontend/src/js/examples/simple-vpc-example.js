/**
 * Simple VPC Example Architecture
 *
 * Einfache Beispiel-Architektur: VPC + Subnet + EC2
 */

export const SIMPLE_VPC_EXAMPLE = {
    id: 'example-simple-vpc',
    name: 'Simple VPC with EC2',
    version: '1.0.0',
    components: {
        'vpc-1': {
            id: 'vpc-1',
            type: 'vpc',
            name: 'main-vpc',
            config: {
                cidr: '10.0.0.0/16',
                enableDnsHostnames: true,
                enableDnsSupport: true
            },
            position: { x: 400, y: 200 }
        },
        'subnet-1': {
            id: 'subnet-1',
            type: 'subnet',
            name: 'public-subnet',
            config: {
                cidr: '10.0.1.0/24',
                subnetType: 'public',
                availabilityZone: 'us-east-1a'
            },
            position: { x: 400, y: 350 }
        },
        'ec2-1': {
            id: 'ec2-1',
            type: 'ec2',
            name: 'web-server',
            config: {
                instanceType: 't3.small',
                ami: 'ami-0c55b159cbfafe1f0',
                hasPublicIp: true,
                privateIp: '10.0.1.10'
            },
            position: { x: 400, y: 500 }
        }
    },
    connections: []
};

/**
 * Load simple VPC example into designer
 */
export function loadSimpleVPCExample() {
    const event = new CustomEvent('load-architecture', {
        detail: { architecture: SIMPLE_VPC_EXAMPLE }
    });
    window.dispatchEvent(event);
}
