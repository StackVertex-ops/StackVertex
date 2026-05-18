/**
 * OverCloud - Admin Dashboard
 *
 * SuperAdmin Dashboard zur Verwaltung von Users, Orgs, und Audit Logs.
 */

import { adminAPI } from '../api/admin.js';
import { authAPI } from '../api/auth.js';
import { getCurrentUser, logout } from '../lib/auth.js';

class AdminDashboard {
    constructor() {
        this.currentUser = null;
        this.allUsers = [];
        this.allOrgs = [];
        this.impersonateUserId = null;
        this.init();
    }

    async init() {
        // Check auth
        const user = getCurrentUser();
        if (!user) {
            window.location.href = '/src/login.html';
            return;
        }

        // Load current user data from API
        await this.loadCurrentUser();

        // Check if SuperAdmin
        if (this.currentUser.system_role !== 'superadmin') {
            alert('Access denied: SuperAdmin required');
            window.location.href = '/src/index.html';
            return;
        }

        // Setup UI
        this.setupEventListeners();
        await this.loadStatistics();
        await this.loadUsers();
    }

    async loadCurrentUser() {
        try {
            const token = localStorage.getItem('access_token');
            this.currentUser = await authAPI.getCurrentUser(token);
            document.getElementById('admin-email').textContent = this.currentUser.email;
        } catch (error) {
            console.error('Failed to load user:', error);
            localStorage.removeItem('access_token');
            window.location.href = '/src/login.html';
        }
    }

    async loadStatistics() {
        try {
            const stats = await adminAPI.getStatistics();

            document.getElementById('stat-total-users').textContent = stats.users.total;
            document.getElementById('stat-active-users').textContent = `${stats.users.active} active`;
            document.getElementById('stat-total-orgs').textContent = stats.organisations.total;
            document.getElementById('stat-total-archs').textContent = stats.architectures.total;
            document.getElementById('stat-deployed-archs').textContent = `${stats.architectures.deployed} deployed`;
        } catch (error) {
            console.error('Failed to load statistics:', error);
            this.showError('Failed to load statistics');
        }
    }

    async loadUsers() {
        try {
            document.getElementById('users-loading').classList.remove('hidden');
            document.getElementById('users-table').classList.add('hidden');

            this.allUsers = await adminAPI.listUsers(0, 1000);
            this.renderUsersTable(this.allUsers);

            document.getElementById('users-loading').classList.add('hidden');
            document.getElementById('users-table').classList.remove('hidden');
        } catch (error) {
            console.error('Failed to load users:', error);
            document.getElementById('users-loading').textContent = 'Failed to load users';
            this.showError('Failed to load users');
        }
    }

    renderUsersTable(users) {
        const table = `
            <table class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gray-50">
                    <tr>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Role</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Created</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                    </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                    ${users.map(user => `
                        <tr>
                            <td class="px-6 py-4 whitespace-nowrap text-sm">${user.email}</td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm">${user.name}</td>
                            <td class="px-6 py-4 whitespace-nowrap">
                                <span class="px-2 py-1 text-xs rounded-full ${
                                    user.status === 'active' ? 'bg-green-100 text-green-800' :
                                    user.status === 'suspended' ? 'bg-red-100 text-red-800' :
                                    'bg-gray-100 text-gray-800'
                                }">${user.status}</span>
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap">
                                <span class="px-2 py-1 text-xs rounded-full ${
                                    user.system_role === 'superadmin' ? 'bg-purple-100 text-purple-800' :
                                    user.system_role === 'support' ? 'bg-blue-100 text-blue-800' :
                                    user.system_role === 'auditor' ? 'bg-indigo-100 text-indigo-800' :
                                    'bg-gray-100 text-gray-800'
                                }">${user.system_role}</span>
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                ${new Date(user.created_at).toLocaleDateString('de-DE')}
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm">
                                <button class="text-blue-600 hover:text-blue-900 mr-3" data-action="reset-password" data-user-id="${user.id}">
                                    Reset Password
                                </button>
                                <button class="text-purple-600 hover:text-purple-900" data-action="impersonate" data-user-id="${user.id}" data-user-email="${user.email}">
                                    Impersonate
                                </button>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;

        document.getElementById('users-table').innerHTML = table;

        // Add click handlers for action buttons
        document.querySelectorAll('[data-action="reset-password"]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const userId = e.target.dataset.userId;
                this.resetPassword(userId);
            });
        });

        document.querySelectorAll('[data-action="impersonate"]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const userId = e.target.dataset.userId;
                const userEmail = e.target.dataset.userEmail;
                this.showImpersonateModal(userId, userEmail);
            });
        });
    }

    async resetPassword(userId) {
        if (!confirm('Reset password for this user?')) return;

        try {
            const result = await adminAPI.resetUserPassword(userId);

            // Show new password in modal
            document.getElementById('new-password-display').textContent = result.new_password;
            document.getElementById('password-reset-modal').classList.remove('hidden');
        } catch (error) {
            console.error('Failed to reset password:', error);
            alert('Failed to reset password. Please try again.');
        }
    }

    showImpersonateModal(userId, userEmail) {
        this.impersonateUserId = userId;
        document.getElementById('impersonate-user-email').textContent = userEmail;
        document.getElementById('impersonate-reason').value = '';
        document.getElementById('impersonate-modal').classList.remove('hidden');
    }

    async impersonateUser() {
        const reason = document.getElementById('impersonate-reason').value.trim();

        if (reason.length < 10) {
            alert('Please provide a reason (at least 10 characters)');
            return;
        }

        try {
            const result = await adminAPI.impersonateUser(this.impersonateUserId, reason);

            // Store impersonation token
            localStorage.setItem('access_token', result.access_token);

            alert(`Now impersonating ${result.impersonated_user_email}. Redirecting to dashboard...`);

            // Redirect to main dashboard
            setTimeout(() => {
                window.location.href = '/src/index.html';
            }, 1000);
        } catch (error) {
            console.error('Failed to impersonate:', error);
            alert('Failed to impersonate user. Please try again.');
        }
    }

    async loadOrganisations() {
        try {
            document.getElementById('orgs-loading').classList.remove('hidden');
            document.getElementById('orgs-table').classList.add('hidden');

            this.allOrgs = await adminAPI.listOrganisations(0, 1000);
            this.renderOrgsTable(this.allOrgs);

            document.getElementById('orgs-loading').classList.add('hidden');
            document.getElementById('orgs-table').classList.remove('hidden');
        } catch (error) {
            console.error('Failed to load organisations:', error);
            document.getElementById('orgs-loading').textContent = 'Failed to load organisations';
            this.showError('Failed to load organisations');
        }
    }

    renderOrgsTable(orgs) {
        const table = `
            <table class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gray-50">
                    <tr>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Plan</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Members</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Created</th>
                    </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                    ${orgs.map(org => `
                        <tr>
                            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">${org.name}</td>
                            <td class="px-6 py-4 whitespace-nowrap">
                                <span class="px-2 py-1 text-xs rounded-full ${
                                    org.type === 'personal' ? 'bg-gray-100 text-gray-800' :
                                    org.type === 'team' ? 'bg-blue-100 text-blue-800' :
                                    'bg-purple-100 text-purple-800'
                                }">${org.type}</span>
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap">
                                <span class="px-2 py-1 text-xs rounded-full ${
                                    org.plan === 'free' ? 'bg-gray-100 text-gray-800' :
                                    org.plan === 'pro' ? 'bg-blue-100 text-blue-800' :
                                    'bg-purple-100 text-purple-800'
                                }">${org.plan}</span>
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap">
                                <span class="px-2 py-1 text-xs rounded-full ${
                                    org.status === 'active' ? 'bg-green-100 text-green-800' :
                                    'bg-red-100 text-red-800'
                                }">${org.status}</span>
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                ${org.quota?.members || 0}
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                ${new Date(org.created_at).toLocaleDateString('de-DE')}
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;

        document.getElementById('orgs-table').innerHTML = table;
    }

    async loadAuditLogs(filters = {}) {
        try {
            document.getElementById('audit-loading').classList.remove('hidden');
            document.getElementById('audit-table').classList.add('hidden');

            const result = await adminAPI.getAuditLogs(filters, 0, 100);
            this.renderAuditTable(result.items);

            document.getElementById('audit-loading').classList.add('hidden');
            document.getElementById('audit-table').classList.remove('hidden');
        } catch (error) {
            console.error('Failed to load audit logs:', error);
            document.getElementById('audit-loading').textContent = 'Failed to load audit logs';
            this.showError('Failed to load audit logs');
        }
    }

    renderAuditTable(logs) {
        const table = `
            <table class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gray-50">
                    <tr>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Timestamp</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">User</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Action</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Resource</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Details</th>
                    </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                    ${logs.map(log => `
                        <tr>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                ${new Date(log.timestamp).toLocaleString('de-DE')}
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm">${log.user || 'System'}</td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm font-mono">${log.action}</td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm">
                                ${log.resource_type}${log.resource_id ? ` (${log.resource_id.substring(0, 8)}...)` : ''}
                            </td>
                            <td class="px-6 py-4 text-sm text-gray-500">
                                ${log.details ? JSON.stringify(log.details).substring(0, 50) + '...' : '-'}
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;

        document.getElementById('audit-table').innerHTML = table;
    }

    setupEventListeners() {
        // Tab switching
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const tab = e.target.dataset.tab;
                this.switchTab(tab);
            });
        });

        // Logout
        document.getElementById('logout-btn').addEventListener('click', () => {
            logout();
        });

        // User search
        document.getElementById('user-search').addEventListener('input', (e) => {
            const searchTerm = e.target.value.toLowerCase();
            const filtered = this.allUsers.filter(user =>
                user.email.toLowerCase().includes(searchTerm) ||
                user.name.toLowerCase().includes(searchTerm)
            );
            this.renderUsersTable(filtered);
        });

        // Password reset modal
        document.getElementById('close-password-modal').addEventListener('click', () => {
            document.getElementById('password-reset-modal').classList.add('hidden');
        });

        document.getElementById('copy-password-btn').addEventListener('click', () => {
            const password = document.getElementById('new-password-display').textContent;
            navigator.clipboard.writeText(password);
            alert('Password copied to clipboard!');
        });

        // Impersonate modal
        document.getElementById('cancel-impersonate-btn').addEventListener('click', () => {
            document.getElementById('impersonate-modal').classList.add('hidden');
        });

        document.getElementById('confirm-impersonate-btn').addEventListener('click', () => {
            this.impersonateUser();
        });

        // Audit log filters
        document.getElementById('audit-apply-filters').addEventListener('click', () => {
            const filters = {
                user: document.getElementById('audit-user-filter').value.trim() || null,
                action: document.getElementById('audit-action-filter').value.trim() || null,
                resource_type: document.getElementById('audit-resource-filter').value.trim() || null
            };
            this.loadAuditLogs(filters);
        });
    }

    switchTab(tab) {
        // Update buttons
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tab);
        });

        // Update content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.toggle('active', content.id === `${tab}-tab`);
        });

        // Load data for tab
        if (tab === 'organisations' && this.allOrgs.length === 0) {
            this.loadOrganisations();
        }
        if (tab === 'audit-logs') {
            this.loadAuditLogs();
        }
    }

    showError(message) {
        // Simple error display (could be improved with a toast/notification system)
        console.error(message);
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.adminDashboard = new AdminDashboard();
    });
} else {
    window.adminDashboard = new AdminDashboard();
}
