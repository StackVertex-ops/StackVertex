/**
 * OverCloud - AWS Components Library
 *
 * Definition aller verfügbaren AWS-Services für den Architecture Builder
 */

/**
 * AWS Components gruppiert nach Kategorien
 */
export const AWS_COMPONENTS = {
  compute: {
    ec2: {
      name: 'EC2 Instance',
      icon: '🖥️',
      category: 'compute',
      description: 'Virtual server in the cloud',
      provider_service: 'ec2'
    },
    lambda: {
      name: 'Lambda Function',
      icon: '⚡',
      category: 'compute',
      description: 'Serverless compute service',
      provider_service: 'lambda'
    },
    ecs: {
      name: 'ECS',
      icon: '📦',
      category: 'compute',
      description: 'Container orchestration service',
      provider_service: 'ecs'
    },
    eks: {
      name: 'EKS',
      icon: '☸️',
      category: 'compute',
      description: 'Managed Kubernetes service',
      provider_service: 'eks'
    }
  },
  network: {
    vpc: {
      name: 'VPC',
      icon: '🌐',
      category: 'network',
      description: 'Isolated cloud network',
      provider_service: 'vpc'
    },
    subnet: {
      name: 'Subnet',
      icon: '📡',
      category: 'network',
      description: 'Network subdivision',
      provider_service: 'subnet'
    },
    alb: {
      name: 'Application Load Balancer',
      icon: '⚖️',
      category: 'network',
      description: 'Layer 7 load balancer',
      provider_service: 'alb'
    },
    nlb: {
      name: 'Network Load Balancer',
      icon: '🔀',
      category: 'network',
      description: 'Layer 4 load balancer',
      provider_service: 'nlb'
    },
    api_gateway: {
      name: 'API Gateway',
      icon: '🚪',
      category: 'network',
      description: 'Managed API service',
      provider_service: 'api_gateway'
    },
    route53: {
      name: 'Route 53',
      icon: '🌍',
      category: 'network',
      description: 'DNS service',
      provider_service: 'route53'
    }
  },
  storage: {
    s3: {
      name: 'S3 Bucket',
      icon: '🪣',
      category: 'storage',
      description: 'Object storage service',
      provider_service: 's3'
    },
    ebs: {
      name: 'EBS Volume',
      icon: '💾',
      category: 'storage',
      description: 'Block storage for EC2',
      provider_service: 'ebs'
    },
    efs: {
      name: 'EFS',
      icon: '📁',
      category: 'storage',
      description: 'Elastic file system',
      provider_service: 'efs'
    }
  },
  database: {
    rds: {
      name: 'RDS Database',
      icon: '🗄️',
      category: 'database',
      description: 'Managed relational database',
      provider_service: 'rds'
    },
    dynamodb: {
      name: 'DynamoDB',
      icon: '⚡',
      category: 'database',
      description: 'NoSQL database service',
      provider_service: 'dynamodb'
    },
    elasticache: {
      name: 'ElastiCache',
      icon: '💨',
      category: 'database',
      description: 'In-memory cache',
      provider_service: 'elasticache'
    },
    aurora: {
      name: 'Aurora',
      icon: '🌟',
      category: 'database',
      description: 'High-performance database',
      provider_service: 'aurora'
    }
  },
  analytics: {
    athena: {
      name: 'Athena',
      icon: '🔍',
      category: 'analytics',
      description: 'Query data in S3',
      provider_service: 'athena'
    },
    glue: {
      name: 'Glue',
      icon: '🔗',
      category: 'analytics',
      description: 'ETL service',
      provider_service: 'glue'
    },
    redshift: {
      name: 'Redshift',
      icon: '📊',
      category: 'analytics',
      description: 'Data warehouse',
      provider_service: 'redshift'
    }
  },
  messaging: {
    sqs: {
      name: 'SQS',
      icon: '📬',
      category: 'messaging',
      description: 'Message queue service',
      provider_service: 'sqs'
    },
    sns: {
      name: 'SNS',
      icon: '📢',
      category: 'messaging',
      description: 'Notification service',
      provider_service: 'sns'
    },
    eventbridge: {
      name: 'EventBridge',
      icon: '🎯',
      category: 'messaging',
      description: 'Event bus service',
      provider_service: 'eventbridge'
    }
  },
  security: {
    security_group: {
      name: 'Security Group',
      icon: '🛡️',
      category: 'security',
      description: 'Virtual firewall',
      provider_service: 'security_group'
    },
    iam_role: {
      name: 'IAM Role',
      icon: '🔑',
      category: 'security',
      description: 'Identity and access management',
      provider_service: 'iam_role'
    },
    waf: {
      name: 'WAF',
      icon: '🔒',
      category: 'security',
      description: 'Web application firewall',
      provider_service: 'waf'
    }
  },
  cdn: {
    cloudfront: {
      name: 'CloudFront',
      icon: '🌐',
      category: 'cdn',
      description: 'Content delivery network',
      provider_service: 'cloudfront'
    }
  }
};

/**
 * Azure Components (Platzhalter - Coming Soon)
 */
export const AZURE_COMPONENTS = {
  compute: {
    // Coming Soon
  },
  network: {
    // Coming Soon
  },
  storage: {
    // Coming Soon
  },
  database: {
    // Coming Soon
  }
};

/**
 * GCP Components (Platzhalter - Coming Soon)
 */
export const GCP_COMPONENTS = {
  compute: {
    // Coming Soon
  },
  network: {
    // Coming Soon
  },
  storage: {
    // Coming Soon
  },
  database: {
    // Coming Soon
  }
};

/**
 * Multi-Cloud Provider Konfiguration
 */
export const CLOUD_PROVIDERS = {
  aws: {
    name: 'Amazon Web Services',
    short: 'AWS',
    icon: '☁️',
    available: true,
    components: AWS_COMPONENTS,
    regions: [
      { id: 'us-east-1', name: 'US East (N. Virginia)' },
      { id: 'us-east-2', name: 'US East (Ohio)' },
      { id: 'us-west-1', name: 'US West (N. California)' },
      { id: 'us-west-2', name: 'US West (Oregon)' },
      { id: 'eu-central-1', name: 'Europe (Frankfurt)' },
      { id: 'eu-west-1', name: 'Europe (Ireland)' },
      { id: 'ap-southeast-1', name: 'Asia Pacific (Singapore)' },
      { id: 'ap-northeast-1', name: 'Asia Pacific (Tokyo)' }
    ]
  },
  azure: {
    name: 'Microsoft Azure',
    short: 'Azure',
    icon: '🔷',
    available: false,
    components: AZURE_COMPONENTS,
    regions: []
  },
  gcp: {
    name: 'Google Cloud Platform',
    short: 'GCP',
    icon: '🔶',
    available: false,
    components: GCP_COMPONENTS,
    regions: []
  }
};

/**
 * Hole alle Components für einen Provider
 * @param {string} provider - Provider ID (aws, azure, gcp)
 * @returns {Object} Components grouped by category
 */
export function getComponentsForProvider(provider) {
  return CLOUD_PROVIDERS[provider]?.components || {};
}

/**
 * Hole alle Kategorien für einen Provider
 * @param {string} provider - Provider ID
 * @returns {Array<string>} Category names
 */
export function getCategoriesForProvider(provider) {
  const components = getComponentsForProvider(provider);
  return Object.keys(components);
}

/**
 * Hole alle Components einer Kategorie
 * @param {string} provider - Provider ID
 * @param {string} category - Category name
 * @returns {Object} Components in category
 */
export function getComponentsByCategory(provider, category) {
  const components = getComponentsForProvider(provider);
  return components[category] || {};
}

/**
 * Finde Component by provider_service
 * @param {string} provider - Provider ID
 * @param {string} providerService - Service ID (e.g., 'ec2', 'lambda')
 * @returns {Object|null} Component definition or null
 */
export function findComponentByService(provider, providerService) {
  const components = getComponentsForProvider(provider);

  for (const category of Object.values(components)) {
    for (const [key, component] of Object.entries(category)) {
      if (component.provider_service === providerService) {
        return { ...component, key };
      }
    }
  }

  return null;
}

/**
 * Validiere ob ein Provider verfügbar ist
 * @param {string} provider - Provider ID
 * @returns {boolean} Ob Provider verfügbar ist
 */
export function isProviderAvailable(provider) {
  return CLOUD_PROVIDERS[provider]?.available === true;
}

/**
 * Hole Regions für einen Provider
 * @param {string} provider - Provider ID
 * @returns {Array} Regions
 */
export function getRegionsForProvider(provider) {
  return CLOUD_PROVIDERS[provider]?.regions || [];
}
