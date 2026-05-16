#!/bin/bash
# ============================================================================
# WordPress Installation Script (Amazon Linux 2023)
# ============================================================================

set -e

# Variables (injected via Terraform templatefile)
SITE_NAME="${site_name}"
DOMAIN_NAME="${domain_name}"
ADMIN_EMAIL="${admin_email}"
PHP_VERSION="${php_version}"
DB_HOST="${db_host}"
DB_NAME="${db_name}"
DB_USER="${db_user}"
DB_PASSWORD="${db_password}"
WP_ADMIN_USER="${wp_admin_user}"
WP_ADMIN_PASS="${wp_admin_pass}"
EFS_ID="${efs_id}"
AWS_REGION="${aws_region}"
SECRET_ARN="${secret_arn}"
PLUGINS="${plugins}"

# ============================================================================
# System Update & Package Installation
# ============================================================================

echo "==> Updating system packages..."
dnf update -y

echo "==> Installing PHP $PHP_VERSION and dependencies..."
dnf install -y \
    php$PHP_VERSION \
    php$PHP_VERSION-fpm \
    php$PHP_VERSION-mysqlnd \
    php$PHP_VERSION-gd \
    php$PHP_VERSION-mbstring \
    php$PHP_VERSION-xml \
    php$PHP_VERSION-zip \
    php$PHP_VERSION-opcache \
    php$PHP_VERSION-intl \
    php$PHP_VERSION-soap

echo "==> Installing Nginx, MySQL client, and utilities..."
dnf install -y \
    nginx \
    mariadb105 \
    unzip \
    wget \
    amazon-efs-utils \
    amazon-cloudwatch-agent

# ============================================================================
# Mount EFS for WordPress Uploads
# ============================================================================

echo "==> Mounting EFS..."
mkdir -p /mnt/efs
mount -t efs -o tls $EFS_ID:/ /mnt/efs

# Add to fstab for persistent mount
echo "$EFS_ID:/ /mnt/efs efs _netdev,tls 0 0" >> /etc/fstab

# ============================================================================
# Download & Install WordPress
# ============================================================================

echo "==> Downloading WordPress..."
cd /tmp
wget https://wordpress.org/latest.tar.gz
tar -xzf latest.tar.gz

echo "==> Installing WordPress to /var/www/html..."
mkdir -p /var/www/html
cp -r wordpress/* /var/www/html/
rm -rf wordpress latest.tar.gz

# ============================================================================
# WordPress Configuration
# ============================================================================

echo "==> Configuring wp-config.php..."
cd /var/www/html

cp wp-config-sample.php wp-config.php

# Replace database credentials
sed -i "s/database_name_here/$DB_NAME/" wp-config.php
sed -i "s/username_here/$DB_USER/" wp-config.php
sed -i "s/password_here/$DB_PASSWORD/" wp-config.php
sed -i "s/localhost/${DB_HOST%:*}/" wp-config.php

# Generate WordPress Salt Keys
SALT=$(curl -sL https://api.wordpress.org/secret-key/1.1/salt/)
printf '%s\n' "g?define( 'AUTH_KEY'?d" "a" "$SALT" "." "w" | ed -s wp-config.php

# WordPress Configuration Tweaks
cat >> wp-config.php <<'WPCONFIG'

/* Custom OverCloud Settings */
define('WP_DEBUG', false);
define('WP_DEBUG_LOG', false);
define('WP_DEBUG_DISPLAY', false);
define('DISALLOW_FILE_EDIT', true);
define('AUTOMATIC_UPDATER_DISABLED', false);
define('WP_AUTO_UPDATE_CORE', 'minor');
define('WP_MEMORY_LIMIT', '256M');
define('WP_MAX_MEMORY_LIMIT', '512M');

/* Increase upload limits */
@ini_set('upload_max_filesize', '64M');
@ini_set('post_max_size', '64M');
@ini_set('max_execution_time', '300');
WPCONFIG

# ============================================================================
# Link EFS to wp-content/uploads
# ============================================================================

echo "==> Linking EFS to wp-content/uploads..."
mkdir -p /mnt/efs/wp-content/uploads
mkdir -p /var/www/html/wp-content
rm -rf /var/www/html/wp-content/uploads
ln -s /mnt/efs/wp-content/uploads /var/www/html/wp-content/uploads

# ============================================================================
# Set Permissions
# ============================================================================

echo "==> Setting file permissions..."
chown -R nginx:nginx /var/www/html
chown -R nginx:nginx /mnt/efs
chmod -R 755 /var/www/html
chmod -R 775 /var/www/html/wp-content

# ============================================================================
# Install WP-CLI
# ============================================================================

echo "==> Installing WP-CLI..."
curl -O https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar
chmod +x wp-cli.phar
mv wp-cli.phar /usr/local/bin/wp

# ============================================================================
# Configure Nginx
# ============================================================================

echo "==> Configuring Nginx..."
cat > /etc/nginx/conf.d/wordpress.conf <<'NGINX'
server {
    listen 80;
    server_name _;
    root /var/www/html;
    index index.php index.html;

    access_log /var/log/nginx/wordpress_access.log;
    error_log /var/log/nginx/wordpress_error.log;

    client_max_body_size 64M;

    location / {
        try_files $uri $uri/ /index.php?$args;
    }

    location ~ \.php$ {
        fastcgi_pass unix:/run/php-fpm/www.sock;
        fastcgi_index index.php;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        include fastcgi_params;
    }

    location ~ /\.ht {
        deny all;
    }

    location = /favicon.ico {
        log_not_found off;
        access_log off;
    }

    location = /robots.txt {
        allow all;
        log_not_found off;
        access_log off;
    }

    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|webp)$ {
        expires max;
        log_not_found off;
    }
}
NGINX

# ============================================================================
# Configure PHP-FPM
# ============================================================================

echo "==> Configuring PHP-FPM..."
sed -i 's/user = apache/user = nginx/' /etc/php-fpm.d/www.conf
sed -i 's/group = apache/group = nginx/' /etc/php-fpm.d/www.conf

# PHP Configuration
cat >> /etc/php.ini <<'PHP'
upload_max_filesize = 64M
post_max_size = 64M
max_execution_time = 300
memory_limit = 256M
PHP

# ============================================================================
# Start Services
# ============================================================================

echo "==> Starting Nginx and PHP-FPM..."
systemctl enable nginx php-fpm
systemctl start nginx php-fpm

# ============================================================================
# WordPress Installation via WP-CLI
# ============================================================================

echo "==> Installing WordPress core..."
cd /var/www/html

# Wait for RDS to be ready
until mysql -h "${DB_HOST%:*}" -u "$DB_USER" -p"$DB_PASSWORD" -e "SELECT 1" >/dev/null 2>&1; do
    echo "Waiting for database to be ready..."
    sleep 5
done

# Install WordPress
wp core install \
    --url="http://$DOMAIN_NAME" \
    --title="$SITE_NAME" \
    --admin_user="$WP_ADMIN_USER" \
    --admin_password="$WP_ADMIN_PASS" \
    --admin_email="$ADMIN_EMAIL" \
    --skip-email \
    --allow-root

echo "==> WordPress installed successfully!"

# ============================================================================
# Install Plugins (if specified)
# ============================================================================

if [ -n "$PLUGINS" ]; then
    echo "==> Installing WordPress plugins: $PLUGINS"
    for plugin in $PLUGINS; do
        wp plugin install "$plugin" --activate --allow-root || echo "Failed to install $plugin"
    done
fi

# Install recommended plugins
echo "==> Installing recommended plugins..."
wp plugin install wordfence --activate --allow-root || true
wp plugin install wp-super-cache --activate --allow-root || true

# ============================================================================
# WordPress Performance Optimizations
# ============================================================================

echo "==> Configuring WordPress performance settings..."

# Disable pingbacks
wp option update default_pingback_flag 0 --allow-root
wp option update default_ping_status closed --allow-root

# Set permalink structure
wp rewrite structure '/%postname%/' --allow-root

# Disable post revisions
echo "define('WP_POST_REVISIONS', 3);" >> /var/www/html/wp-config.php

# ============================================================================
# Health Check Endpoint
# ============================================================================

echo "==> Creating health check endpoint..."
cat > /var/www/html/health <<'HEALTH'
OK
HEALTH

# ============================================================================
# CloudWatch Agent Setup
# ============================================================================

echo "==> Configuring CloudWatch Agent..."
cat > /opt/aws/amazon-cloudwatch-agent/etc/cloudwatch-config.json <<'CLOUDWATCH'
{
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/nginx/wordpress_access.log",
            "log_group_name": "/wordpress/nginx/access",
            "log_stream_name": "{instance_id}"
          },
          {
            "file_path": "/var/log/nginx/wordpress_error.log",
            "log_group_name": "/wordpress/nginx/error",
            "log_stream_name": "{instance_id}"
          },
          {
            "file_path": "/var/log/php-fpm/www-error.log",
            "log_group_name": "/wordpress/php-fpm",
            "log_stream_name": "{instance_id}"
          }
        ]
      }
    }
  },
  "metrics": {
    "namespace": "WordPress",
    "metrics_collected": {
      "mem": {
        "measurement": [
          {"name": "mem_used_percent", "unit": "Percent"}
        ],
        "metrics_collection_interval": 60
      },
      "disk": {
        "measurement": [
          {"name": "used_percent", "unit": "Percent"}
        ],
        "metrics_collection_interval": 60,
        "resources": ["*"]
      }
    }
  }
}
CLOUDWATCH

/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
    -a fetch-config \
    -m ec2 \
    -s \
    -c file:/opt/aws/amazon-cloudwatch-agent/etc/cloudwatch-config.json

# ============================================================================
# Final Cleanup & Summary
# ============================================================================

echo "==> Cleaning up..."
dnf clean all

echo "========================================="
echo "WordPress Installation Complete!"
echo "========================================="
echo "Site URL: http://$DOMAIN_NAME"
echo "Admin URL: http://$DOMAIN_NAME/wp-admin"
echo "Admin User: $WP_ADMIN_USER"
echo "Admin Password: (stored in Secrets Manager)"
echo ""
echo "Next Steps:"
echo "1. Configure DNS to point $DOMAIN_NAME to this server"
echo "2. Install SSL Certificate (Let's Encrypt recommended)"
echo "3. Configure caching plugin (WP Super Cache already installed)"
echo "4. Review security settings (Wordfence already installed)"
echo "========================================="

# Log completion
echo "WordPress setup completed at $(date)" >> /var/log/wordpress-setup.log
