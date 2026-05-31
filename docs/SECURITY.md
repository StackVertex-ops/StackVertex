# StackVertex - Security Documentation

## Admin User Creation Security

### Overview

Creating SuperAdmin users requires **two security layers**:

1. **AWS IAM Access** - Must have DynamoDB write permissions
2. **ADMIN_CREATION_SECRET** - Secret token known only to authorized personnel

This dual-layer approach prevents unauthorized admin creation even if:
- Source code is public (GitHub)
- Someone gains temporary AWS access
- Scripts are accidentally exposed

### Setting up ADMIN_CREATION_SECRET

#### For GitHub Actions

1. Generate a secure random token (32+ characters):
   ```bash
   openssl rand -base64 48
   ```

2. Add to GitHub Secrets:
   - Go to: `Settings` → `Secrets and variables` → `Actions`
   - Click: `New repository secret`
   - Name: `ADMIN_CREATION_SECRET`
   - Value: `<your-generated-token>`

#### For Local Usage

1. Generate token:
   ```bash
   openssl rand -base64 48
   ```

2. Store securely (password manager recommended)

3. Set environment variable:
   ```bash
   export ADMIN_CREATION_SECRET="<your-token>"
   ```

4. Run admin creation script:
   ```bash
   ./infrastructure/scripts/create-admin-user.sh
   ```

### Security Best Practices

#### Secrets Management

- ✅ **DO**: Store ADMIN_CREATION_SECRET in password manager
- ✅ **DO**: Use different secrets for dev/staging/prod
- ✅ **DO**: Rotate secret every 90 days
- ❌ **DON'T**: Commit secrets to git
- ❌ **DON'T**: Share secrets via email/Slack
- ❌ **DON'T**: Use the same secret across projects

#### Admin User Creation

- ✅ **DO**: Create minimal number of admins (1-2)
- ✅ **DO**: Use strong passwords (generated, 32+ chars)
- ✅ **DO**: Change password after first login
- ✅ **DO**: Enable 2FA when available
- ✅ **DO**: Use personal emails (not shared accounts)
- ❌ **DON'T**: Use `--force` flag unless absolutely necessary
- ❌ **DON'T**: Share admin credentials
- ❌ **DON'T**: Store passwords in plaintext

#### AWS IAM

- ✅ **DO**: Use least-privilege IAM policies
- ✅ **DO**: Enable MFA on AWS accounts
- ✅ **DO**: Rotate AWS access keys regularly
- ✅ **DO**: Use IAM roles instead of access keys (when possible)
- ❌ **DON'T**: Use root account for deployments
- ❌ **DON'T**: Share AWS credentials

### Authentication Flow

```
User Request → Frontend
    ↓
Login Page → API (POST /auth/login)
    ↓
Backend validates credentials (DynamoDB)
    ↓
JWT Token issued (expires in 24h)
    ↓
Frontend stores token (localStorage)
    ↓
Protected pages check token (auth-guard.js)
    ↓
API requests include token (Authorization header)
```

### Protected Resources

#### Frontend Pages (Require Login)

- `/dashboard.html`
- `/blueprints.html`
- `/architecture-builder.html`
- `/billing.html`
- `/security.html`
- `/aws-credentials.html`

#### Public Pages (No Login)

- `/index.html` (Landing page)
- `/pricing.html`
- `/login.html`
- `/register.html`
- `/guides/*` (Documentation)

#### Backend API Endpoints

**Public:**
- `POST /auth/login`
- `POST /auth/register`
- `GET /health`

**Authenticated:**
- `GET /architectures/*`
- `POST /architectures/*`
- `GET /deployments/*`
- `POST /deployments/*`
- `GET /user/*`

**Admin Only:**
- `GET /admin/users`
- `POST /admin/users/{id}/role`
- `DELETE /admin/users/{id}`

### Audit Logging

All sensitive operations are logged:

- Admin user creation
- User role changes
- Password resets
- Failed login attempts (after 5 tries)
- Deployment operations
- AWS credential updates

Logs stored in:
- **DynamoDB**: `stackvertex-{env}-audit-log`
- **CloudWatch**: `/aws/lambda/stackvertex-{env}-api`

### Token Security

#### JWT Configuration

- **Algorithm**: RS256 (RSA public/private key)
- **Expiration**: 24 hours
- **Refresh**: Via refresh token (30 days)
- **Storage**: localStorage (client-side)

#### Token Rotation

- Access tokens expire after 24h
- Refresh tokens expire after 30 days
- Automatic refresh before expiration
- Manual refresh via `/auth/refresh`

### Data Encryption

#### At Rest

- **DynamoDB**: Server-side encryption (AWS KMS)
- **S3**: AES-256 encryption
- **Secrets**: AWS Secrets Manager

#### In Transit

- **API**: HTTPS only (TLS 1.2+)
- **Frontend**: Served via CloudFront (HTTPS)
- **Backend**: API Gateway (HTTPS)

### Incident Response

If security breach suspected:

1. **Immediate Actions**:
   - Revoke all admin access tokens
   - Rotate ADMIN_CREATION_SECRET
   - Rotate AWS access keys
   - Review CloudWatch logs for suspicious activity

2. **Investigation**:
   - Check DynamoDB audit logs
   - Review CloudTrail for AWS API calls
   - Verify all admin users are legitimate

3. **Remediation**:
   - Reset all user passwords
   - Re-deploy infrastructure if compromised
   - Update security policies
   - Document incident

4. **Post-Mortem**:
   - Root cause analysis
   - Update security procedures
   - Train team on new policies

### Compliance

#### GDPR

- User data stored in EU region (eu-central-1)
- Data export available via API
- Account deletion within 30 days
- Cookie consent implemented

#### SOC 2

- Audit logs for all operations
- Encryption at rest and in transit
- Access control (RBAC)
- Regular security reviews

### Security Checklist

**Before Production Deployment:**

- [ ] ADMIN_CREATION_SECRET set in GitHub Secrets
- [ ] AWS MFA enabled on all accounts
- [ ] CloudWatch alarms configured
- [ ] Backup strategy implemented
- [ ] Disaster recovery plan documented
- [ ] Security scan passed (npm audit, safety check)
- [ ] Penetration test completed
- [ ] GDPR compliance verified
- [ ] SSL certificates configured
- [ ] Rate limiting enabled

**Monthly Security Tasks:**

- [ ] Review CloudWatch logs for anomalies
- [ ] Check for failed login attempts
- [ ] Verify all admin users still authorized
- [ ] Update dependencies (npm, Poetry)
- [ ] Rotate AWS access keys
- [ ] Review IAM policies

**Quarterly Security Tasks:**

- [ ] Rotate ADMIN_CREATION_SECRET
- [ ] Security audit (internal or external)
- [ ] Update security documentation
- [ ] Train team on security best practices

### Contact

For security issues, contact:
- **Email**: security@stackvertex.io
- **Responsible Disclosure**: Via GitHub Security Advisories

**DO NOT** disclose security vulnerabilities publicly before coordinated disclosure.
