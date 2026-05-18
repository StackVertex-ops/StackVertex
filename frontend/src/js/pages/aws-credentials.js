/**
 * AWS Credentials Management Page
 */

import { APIClient } from '../api/auth.js';

const API_BASE_URL = 'http://localhost:8000';
const apiClient = new APIClient(API_BASE_URL);

class AWSCredentialsManager {
    constructor() {
        this.credentials = [];
        this.init();
    }

    async init() {
        this.setupEventListeners();
        await this.loadCredentials();
    }

    setupEventListeners() {
        // Add Credential Button
        document.getElementById('add-credential-btn').addEventListener('click', () => {
            this.showModal();
        });

        // Close Modal
        document.getElementById('close-modal-btn').addEventListener('click', () => {
            this.hideModal();
        });

        document.getElementById('cancel-btn').addEventListener('click', () => {
            this.hideModal();
        });

        // Credential Type Change
        document.getElementById('credential-type').addEventListener('change', (e) => {
            this.toggleFieldsByType(e.target.value);
        });

        // Form Submit
        document.getElementById('credential-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.createCredential();
        });

        // Setup Guide
        document.getElementById('show-setup-guide-btn').addEventListener('click', async () => {
            await this.showSetupGuide();
        });

        document.getElementById('close-guide-btn').addEventListener('click', () => {
            document.getElementById('setup-guide-modal').classList.add('hidden');
        });

        // Logout
        document.getElementById('logout-btn').addEventListener('click', () => {
            localStorage.removeItem('authToken');
            window.location.href = '/login.html';
        });
    }

    toggleFieldsByType(type) {
        const assumeRoleFields = document.getElementById('assume-role-fields');
        const accessKeyFields = document.getElementById('access-key-fields');

        if (type === 'assume_role') {
            assumeRoleFields.classList.remove('hidden');
            accessKeyFields.classList.add('hidden');
        } else {
            assumeRoleFields.classList.add('hidden');
            accessKeyFields.classList.remove('hidden');
        }
    }

    showModal() {
        document.getElementById('credential-modal').classList.remove('hidden');
        document.getElementById('credential-form').reset();
        this.toggleFieldsByType('assume_role');
    }

    hideModal() {
        document.getElementById('credential-modal').classList.add('hidden');
    }

    async loadCredentials() {
        try {
            this.credentials = await apiClient.get('/api/v1/aws-credentials');
            this.renderCredentials();
        } catch (error) {
            console.error('Failed to load credentials:', error);
            document.getElementById('credentials-list').innerHTML = `
                <p class="text-red-600">Fehler beim Laden der Credentials: ${error.message}</p>
            `;
        }
    }

    renderCredentials() {
        const listEl = document.getElementById('credentials-list');

        if (this.credentials.length === 0) {
            listEl.innerHTML = `
                <div class="text-center py-12">
                    <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"></path>
                    </svg>
                    <h3 class="mt-2 text-sm font-medium text-gray-900">Keine Credentials</h3>
                    <p class="mt-1 text-sm text-gray-500">Füge AWS Credentials hinzu um Deployments zu starten.</p>
                    <div class="mt-6">
                        <button onclick="document.getElementById('add-credential-btn').click()" class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
                            + Erste Credentials hinzufügen
                        </button>
                    </div>
                </div>
            `;
            return;
        }

        listEl.innerHTML = this.credentials.map(cred => `
            <div class="bg-white rounded-lg shadow p-6">
                <div class="flex justify-between items-start">
                    <div class="flex-1">
                        <div class="flex items-center space-x-3">
                            <h3 class="text-lg font-semibold">${cred.name}</h3>
                            <span class="px-2 py-1 rounded text-xs font-semibold ${this.getStatusClass(cred.status)}">
                                ${cred.status}
                            </span>
                        </div>
                        <div class="mt-2 text-sm text-gray-600 space-y-1">
                            <p><strong>Typ:</strong> ${cred.credential_type === 'assume_role' ? 'AssumeRole' : 'Access Keys'}</p>
                            <p><strong>Region:</strong> ${cred.region}</p>
                            <p><strong>ID:</strong> <code class="text-xs bg-gray-100 px-1 py-0.5 rounded">${cred.id}</code></p>
                            ${cred.last_verified ? `<p><strong>Zuletzt verifiziert:</strong> ${new Date(cred.last_verified).toLocaleString('de-DE')}</p>` : ''}
                        </div>
                    </div>
                    <div class="flex space-x-2">
                        <button onclick="awsCredentialsManager.verifyCredential('${cred.id}')" class="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700">
                            Verifizieren
                        </button>
                        <button onclick="awsCredentialsManager.deleteCredential('${cred.id}')" class="px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700">
                            Löschen
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
    }

    getStatusClass(status) {
        const classes = {
            'active': 'bg-gray-100 text-gray-800',
            'verified': 'bg-green-100 text-green-800',
            'failed': 'bg-red-100 text-red-800'
        };
        return classes[status] || 'bg-gray-100 text-gray-800';
    }

    async createCredential() {
        const credentialType = document.getElementById('credential-type').value;

        const data = {
            name: document.getElementById('credential-name').value,
            credential_type: credentialType,
            region: document.getElementById('credential-region').value
        };

        if (credentialType === 'assume_role') {
            data.role_arn = document.getElementById('role-arn').value;
            data.external_id = document.getElementById('external-id').value || null;

            if (!data.role_arn) {
                alert('Bitte gib eine Role ARN ein');
                return;
            }
        } else {
            data.access_key_id = document.getElementById('access-key-id').value;
            data.secret_access_key = document.getElementById('secret-access-key').value;

            if (!data.access_key_id || !data.secret_access_key) {
                alert('Bitte gib Access Key ID und Secret Access Key ein');
                return;
            }
        }

        try {
            await apiClient.post('/api/v1/aws-credentials', data);
            alert('Credentials erfolgreich hinzugefügt!');
            this.hideModal();
            await this.loadCredentials();
        } catch (error) {
            console.error('Failed to create credential:', error);
            alert('Fehler beim Erstellen der Credentials: ' + error.message);
        }
    }

    async verifyCredential(credentialId) {
        if (!confirm('Credentials jetzt verifizieren?')) return;

        try {
            const result = await apiClient.post(`/api/v1/aws-credentials/${credentialId}/verify`, {});

            if (result.valid) {
                alert('Credentials sind gültig!');
            } else {
                alert('Credentials sind ungültig. Bitte überprüfe sie.');
            }

            await this.loadCredentials();
        } catch (error) {
            console.error('Verification failed:', error);
            alert('Verification fehlgeschlagen: ' + error.message);
        }
    }

    async deleteCredential(credentialId) {
        if (!confirm('Credential wirklich löschen?')) return;

        try {
            await apiClient.delete(`/api/v1/aws-credentials/${credentialId}`);
            alert('Credential gelöscht');
            await this.loadCredentials();
        } catch (error) {
            console.error('Delete failed:', error);
            alert('Löschen fehlgeschlagen: ' + error.message);
        }
    }

    async showSetupGuide() {
        try {
            const response = await apiClient.get('/api/v1/aws-credentials/setup-guide');
            const guideHtml = this.markdownToHtml(response.guide);

            document.getElementById('setup-guide-content').innerHTML = guideHtml;
            document.getElementById('setup-guide-modal').classList.remove('hidden');
        } catch (error) {
            console.error('Failed to load setup guide:', error);
        }
    }

    markdownToHtml(markdown) {
        // Simple Markdown to HTML converter
        return markdown
            .replace(/^# (.+)$/gm, '<h1 class="text-2xl font-bold mt-6 mb-3">$1</h1>')
            .replace(/^## (.+)$/gm, '<h2 class="text-xl font-bold mt-5 mb-2">$1</h2>')
            .replace(/^### (.+)$/gm, '<h3 class="text-lg font-semibold mt-4 mb-2">$1</h3>')
            .replace(/```bash\n([\s\S]+?)\n```/g, '<pre class="bg-gray-100 p-3 rounded overflow-x-auto text-sm my-3"><code>$1</code></pre>')
            .replace(/```([\s\S]+?)```/g, '<pre class="bg-gray-100 p-3 rounded overflow-x-auto text-sm my-3"><code>$1</code></pre>')
            .replace(/`([^`]+)`/g, '<code class="bg-gray-100 px-1 py-0.5 rounded text-sm">$1</code>')
            .replace(/^\*\*(.+?)\*\*/gm, '<strong>$1</strong>')
            .replace(/^- (.+)$/gm, '<li class="ml-5">$1</li>')
            .replace(/⚠️/g, '<span class="text-yellow-600">⚠️</span>')
            .replace(/---/g, '<hr class="my-4 border-gray-300">')
            .replace(/\n\n/g, '<br><br>');
    }
}

// Initialize
const awsCredentialsManager = new AWSCredentialsManager();
window.awsCredentialsManager = awsCredentialsManager;
