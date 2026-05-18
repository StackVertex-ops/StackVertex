"""
WordPress Blueprint

Managed WordPress Setup mit EC2 + RDS MySQL + EFS
Perfekt für: Blogs, Corporate Websites, E-Commerce (WooCommerce)
"""

from .base import (
    Blueprint,
    BlueprintCategory,
    BlueprintDifficulty,
    BlueprintFormField,
    BlueprintMetadata,
    CostEstimate,
    FieldType,
    FieldValidation,
    SelectOption,
)

WORDPRESS = Blueprint(
    metadata=BlueprintMetadata(
        id="wordpress",
        name="WordPress Website",
        description="Production-ready WordPress mit EC2, RDS MySQL, EFS für Media Files und CloudFront CDN",
        category=BlueprintCategory.WEBAPP,
        difficulty=BlueprintDifficulty.INTERMEDIATE,
        estimated_cost=CostEstimate(
            min_usd=40.0,
            typical_usd=80.0,
            max_usd=200.0,
            breakdown={
                "EC2 (1x t3.small, 24/7)": 15.18,
                "RDS MySQL (db.t3.small)": 27.74,
                "EFS Storage (20GB)": 6.00,
                "CloudFront (optional, 500GB)": 42.50,
                "EBS Storage (20GB gp3)": 1.60,
                "Data Transfer": 5.00,
                "Elastic IP": 3.65,
            },
            assumptions=[
                "1x EC2 t3.small (24/7 running)",
                "RDS MySQL db.t3.small (Single-AZ für Kosten)",
                "~20GB Media Files in EFS",
                "CloudFront optional (empfohlen)",
                "~500GB Traffic pro Monat",
            ],
        ),
        setup_time_minutes=20,
        use_cases=[
            "WordPress Blogs & Corporate Websites",
            "E-Commerce mit WooCommerce",
            "Membership Sites",
            "Marketing Landing Pages mit WordPress",
            "News & Magazine Websites",
        ],
        features=[
            "Vollständig gemanagte WordPress Installation",
            "Automatische WordPress Updates (optional)",
            "EFS für shared Media Files (Multi-Instance fähig)",
            "RDS MySQL für Datenbank (Automated Backups)",
            "CloudFront CDN für statische Assets (optional)",
            "HTTPS via Let's Encrypt (automatisch)",
            "phpMyAdmin vorinstalliert",
        ],
        limitations=[
            "Kein Multi-Site Setup in diesem Blueprint",
            "Email-Versand erfordert SMTP Plugin (SES empfohlen)",
            "Plugins/Themes müssen manuell verwaltet werden",
            "Performance hängt stark von Plugins ab",
        ],
        icon="wordpress",
    ),
    form_schema=[
        BlueprintFormField(
            name="site_name",
            type=FieldType.TEXT,
            label="Site Name",
            description="Name für deine WordPress Site (z.B. 'my-blog')",
            required=True,
            validation=FieldValidation(
                pattern=r"^[a-z0-9][a-z0-9-]{1,61}[a-z0-9]$",
            ),
        ),
        BlueprintFormField(
            name="domain_name",
            type=FieldType.TEXT,
            label="Domain Name",
            description="z.B. blog.example.com",
            required=True,
            validation=FieldValidation(
                pattern=r"^([a-z0-9]+(-[a-z0-9]+)*\.)+[a-z]{2,}$",
            ),
        ),
        BlueprintFormField(
            name="admin_email",
            type=FieldType.TEXT,
            label="WordPress Admin Email",
            description="Email für WordPress Admin Account",
            required=True,
            validation=FieldValidation(
                pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
            ),
        ),
        BlueprintFormField(
            name="ec2_instance_type",
            type=FieldType.SELECT,
            label="EC2 Instance Type",
            description="Server-Größe für WordPress",
            required=True,
            default="t3.small",
            validation=FieldValidation(
                options=[
                    SelectOption(
                        value="t3.micro",
                        label="t3.micro (1 vCPU, 1GB RAM) - $7.30/Monat",
                        description="Nur für kleine Blogs (<1000 Besucher/Tag)",
                        price_factor=0.5,
                    ),
                    SelectOption(
                        value="t3.small",
                        label="t3.small (2 vCPU, 2GB RAM) - $15.18/Monat",
                        description="Empfohlen für die meisten WordPress Sites",
                        price_factor=1.0,
                    ),
                    SelectOption(
                        value="t3.medium",
                        label="t3.medium (2 vCPU, 4GB RAM) - $30.37/Monat",
                        description="Für größere Sites oder viele Plugins",
                        price_factor=2.0,
                    ),
                ],
            ),
        ),
        BlueprintFormField(
            name="rds_instance_class",
            type=FieldType.SELECT,
            label="Database Instance Class",
            description="MySQL Database Größe",
            required=True,
            default="db.t3.small",
            validation=FieldValidation(
                options=[
                    SelectOption(
                        value="db.t3.micro",
                        label="db.t3.micro (1GB RAM) - $13.87/Monat",
                        description="Nur für kleine Test-Sites",
                        price_factor=0.5,
                    ),
                    SelectOption(
                        value="db.t3.small",
                        label="db.t3.small (2GB RAM) - $27.74/Monat",
                        description="Empfohlen für Production",
                        price_factor=1.0,
                    ),
                    SelectOption(
                        value="db.t3.medium",
                        label="db.t3.medium (4GB RAM) - $55.48/Monat",
                        description="Für größere Datenbanken",
                        price_factor=2.0,
                    ),
                ],
            ),
        ),
        BlueprintFormField(
            name="rds_storage_gb",
            type=FieldType.NUMBER,
            label="Database Storage (GB)",
            description="MySQL Storage Size (20-1000 GB)",
            required=True,
            default=20,
            validation=FieldValidation(min=20, max=1000),
            constraints="aws.rds.storage",
        ),
        BlueprintFormField(
            name="enable_cloudfront",
            type=FieldType.TOGGLE,
            label="CloudFront CDN aktivieren",
            description="Schnellere Ladezeiten weltweit (+~$10-50/Monat je nach Traffic)",
            required=False,
            default=True,
        ),
        BlueprintFormField(
            name="enable_auto_backups",
            type=FieldType.TOGGLE,
            label="Automatische Backups",
            description="Tägliche EFS + RDS Snapshots (kostet ~$5/Monat)",
            required=False,
            default=True,
        ),
        BlueprintFormField(
            name="php_version",
            type=FieldType.SELECT,
            label="PHP Version",
            description="WordPress empfiehlt PHP 8.1+",
            required=True,
            default="8.2",
            validation=FieldValidation(
                options=[
                    SelectOption(value="8.2", label="PHP 8.2 (empfohlen)"),
                    SelectOption(value="8.1", label="PHP 8.1"),
                    SelectOption(value="8.0", label="PHP 8.0 (veraltet)"),
                ],
            ),
        ),
        BlueprintFormField(
            name="wordpress_plugins",
            type=FieldType.MULTISELECT,
            label="Vorinstallierte Plugins (optional)",
            description="Wähle Plugins die automatisch installiert werden",
            required=False,
            default=[],
            validation=FieldValidation(
                options=[
                    SelectOption(value="wordfence", label="Wordfence Security"),
                    SelectOption(value="wp-super-cache", label="WP Super Cache"),
                    SelectOption(value="yoast-seo", label="Yoast SEO"),
                    SelectOption(value="contact-form-7", label="Contact Form 7"),
                    SelectOption(value="woocommerce", label="WooCommerce"),
                    SelectOption(value="wp-mail-smtp", label="WP Mail SMTP"),
                ],
            ),
        ),
    ],
    aws_resources=[
        "EC2",
        "RDS MySQL",
        "EFS",
        "VPC",
        "Security Groups",
        "Elastic IP",
        "CloudFront",
        "ACM",
        "Route53",
    ],
    terraform_templates=[
        "blueprints/wordpress/vpc.tf.j2",
        "blueprints/wordpress/security_groups.tf.j2",
        "blueprints/wordpress/ec2.tf.j2",
        "blueprints/wordpress/rds.tf.j2",
        "blueprints/wordpress/efs.tf.j2",
        "blueprints/wordpress/cloudfront.tf.j2",
        "blueprints/wordpress/route53.tf.j2",
    ],
    deployment_guide="""
## Deployment Guide: WordPress

### 1. Nach Terraform Apply
Terraform hat automatisch:
- WordPress installiert (via User Data)
- MySQL Datenbank erstellt
- EFS für /wp-content/uploads mounted
- SSL Certificate via Let's Encrypt konfiguriert

### 2. WordPress Setup abschließen
Öffne: `https://YOUR_DOMAIN/wp-admin/install.php`

```
Site Title: Dein Blog Name
Username: admin (ändern empfohlen!)
Password: [generiert - siehe EC2 User Data Output]
Email: deine@email.com
```

### 3. WP-CLI nutzen (SSH Zugriff)
```bash
# SSH zu EC2 Instance
ssh -i key.pem ec2-user@YOUR_ELASTIC_IP

# Plugin installieren
wp plugin install wordfence --activate --allow-root

# Theme installieren
wp theme install astra --activate --allow-root

# User erstellen
wp user create john john@example.com --role=editor --allow-root

# Cache leeren
wp cache flush --allow-root
```

### 4. CloudFront invalidieren (bei Updates)
```bash
# Nach Theme/Plugin Updates
aws cloudfront create-invalidation \\
  --distribution-id YOUR_DISTRIBUTION_ID \\
  --paths "/wp-content/*"
```

### 5. Datenbank-Backup
```bash
# RDS Snapshot erstellen
aws rds create-db-snapshot \\
  --db-instance-identifier YOUR_RDS_ID \\
  --db-snapshot-identifier wordpress-backup-$(date +%Y%m%d)

# Oder via WP-CLI
wp db export backup.sql --allow-root
aws s3 cp backup.sql s3://your-backup-bucket/
```

### 6. Performance Optimierung

#### A) Install Caching Plugin
- **WP Super Cache** (einfach) oder
- **W3 Total Cache** (erweitert)

#### B) Nginx Reverse Proxy (optional)
Für noch bessere Performance installiere Nginx vor Apache:
```bash
sudo yum install nginx
# Nginx als Reverse Proxy zu Apache:80
```

#### C) Offload Images zu S3
- Plugin: **WP Offload Media Lite**
- Speichert Uploads in S3 statt EFS (günstiger!)

### 7. Security Hardening

```bash
# WordPress Core Updates
wp core update --allow-root

# Plugin Updates
wp plugin update --all --allow-root

# .htaccess schützen
chmod 444 /var/www/html/.htaccess

# wp-config.php schützen
chmod 440 /var/www/html/wp-config.php
```

#### Empfohlene Plugins:
- **Wordfence Security** (Firewall, Malware Scan)
- **iThemes Security** (Brute Force Protection)
- **UpdraftPlus** (Backups)

### 8. Email-Versand konfigurieren

WordPress kann standardmäßig keine Emails senden. Nutze AWS SES:

```bash
# Install WP Mail SMTP Plugin
wp plugin install wp-mail-smtp --activate --allow-root
```

WP Mail SMTP Konfiguration:
- Mailer: Amazon SES
- Region: us-east-1
- Access Key: [IAM User mit SES Permissions]
- Secret Key: [Secret]

### 9. Monitoring

CloudWatch Logs:
- `/var/log/httpd/access_log` → WordPress Traffic
- `/var/log/httpd/error_log` → PHP Errors
- RDS Performance Insights aktiviert

### Troubleshooting:

**Site lädt langsam:**
1. Prüfe CloudWatch EC2 CPU/Memory
2. Aktiviere Caching Plugin
3. Optimiere Bilder (TinyPNG, ShortPixel)
4. Deaktiviere unnötige Plugins

**Database Connection Error:**
1. Prüfe RDS Security Group (erlaubt EC2 SG?)
2. Prüfe wp-config.php (korrekte DB Credentials?)
3. Prüfe RDS Status (running?)

**Uploads funktionieren nicht:**
1. Prüfe EFS Mount: `df -h | grep efs`
2. Prüfe Permissions: `sudo chown -R apache:apache /var/www/html/wp-content/uploads`

**CloudFront zeigt alte Version:**
- Invalidation erstellen (siehe oben)
- Oder warte ~24h (Cache TTL)
""",
)
