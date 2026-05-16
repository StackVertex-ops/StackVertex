/**
 * Sample Architecture Data
 *
 * Beispiel-Architektur zum Testen des Infrastructure Designers
 */

export const sampleArchitecture = {
    id: 'demo-1',
    name: 'Demo Web Application Architecture',
    version: '1.0.0',
    components: {
        'vpc-1': {
            id: 'vpc-1',
            type: 'vpc',
            name: 'Main VPC',
            config: {
                cidr: '10.0.0.0/16',
                enableDnsHostnames: true,
                enableDnsSupport: true
            },
            position: { x: 400, y: 100 }
        },
        'subnet-public-1': {
            id: 'subnet-public-1',
            type: 'subnet',
            name: 'Public Subnet 1',
            config: {
                cidr: '10.0.1.0/24',
                subnetType: 'public',
                availabilityZone: 'us-east-1a'
            },
            position: { x: 250, y: 250 }
        },
        'subnet-private-1': {
            id: 'subnet-private-1',
            type: 'subnet',
            name: 'Private Subnet 1',
            config: {
                cidr: '10.0.2.0/24',
                subnetType: 'private',
                availabilityZone: 'us-east-1a'
            },
            position: { x: 450, y: 250 }
        },
        'igw-1': {
            id: 'igw-1',
            type: 'igw',
            name: 'Internet Gateway',
            config: {},
            position: { x: 250, y: 50 }
        },
        'nat-1': {
            id: 'nat-1',
            type: 'nat',
            name: 'NAT Gateway',
            config: {
                subnetId: 'subnet-public-1'
            },
            position: { x: 350, y: 150 }
        },
        'alb-1': {
            id: 'alb-1',
            type: 'alb',
            name: 'Application Load Balancer',
            config: {
                scheme: 'internet-facing',
                ipAddressType: 'ipv4'
            },
            position: { x: 250, y: 350 }
        },
        'ec2-web-1': {
            id: 'ec2-web-1',
            type: 'ec2',
            name: 'Web Server 1',
            config: {
                instanceType: 't3.micro',
                ami: 'ami-0c55b159cbfafe1f0',
                privateIp: '10.0.2.10',
                hasPublicIp: false,
                publicIp: null
            },
            position: { x: 350, y: 450 }
        },
        'ec2-web-2': {
            id: 'ec2-web-2',
            type: 'ec2',
            name: 'Web Server 2',
            config: {
                instanceType: 't3.micro',
                ami: 'ami-0c55b159cbfafe1f0',
                privateIp: '10.0.2.11',
                hasPublicIp: false,
                publicIp: null
            },
            position: { x: 500, y: 450 }
        },
        'rds-1': {
            id: 'rds-1',
            type: 'rds',
            name: 'PostgreSQL Database',
            config: {
                engine: 'postgres',
                engineVersion: '14.7',
                instanceClass: 'db.t3.micro',
                privateIp: '10.0.2.20'
            },
            position: { x: 650, y: 450 }
        },
        's3-1': {
            id: 's3-1',
            type: 's3',
            name: 'Static Assets Bucket',
            config: {
                versioning: true,
                encryption: true,
                publicAccess: false
            },
            position: { x: 650, y: 250 }
        }
    },
    connections: [
        {
            from: 'igw-1',
            to: 'vpc-1',
            data: { label: 'attached' }
        },
        {
            from: 'igw-1',
            to: 'subnet-public-1',
            data: { label: 'route' }
        },
        {
            from: 'nat-1',
            to: 'subnet-public-1',
            data: { label: 'in' }
        },
        {
            from: 'nat-1',
            to: 'subnet-private-1',
            data: { label: 'route' }
        },
        {
            from: 'alb-1',
            to: 'ec2-web-1',
            data: { port: 80, protocol: 'HTTP' }
        },
        {
            from: 'alb-1',
            to: 'ec2-web-2',
            data: { port: 80, protocol: 'HTTP' }
        },
        {
            from: 'ec2-web-1',
            to: 'rds-1',
            data: { port: 5432, protocol: 'PostgreSQL' }
        },
        {
            from: 'ec2-web-2',
            to: 'rds-1',
            data: { port: 5432, protocol: 'PostgreSQL' }
        },
        {
            from: 'ec2-web-1',
            to: 's3-1',
            data: { label: 'S3 API' }
        },
        {
            from: 'ec2-web-2',
            to: 's3-1',
            data: { label: 'S3 API' }
        }
    ]
};

/**
 * Load sample architecture into designer
 */
export function loadSampleArchitecture() {
    const event = new CustomEvent('load-architecture', {
        detail: { architecture: sampleArchitecture }
    });
    window.dispatchEvent(event);
}
