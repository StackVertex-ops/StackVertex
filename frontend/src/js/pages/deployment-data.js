/**
 * Deployment Data Upload Page
 *
 * Ermöglicht Upload von Docker Images und Static Files
 */

import { APIClient } from '../api/auth.js';

const API_BASE_URL = 'http://localhost:8000';
const apiClient = new APIClient(API_BASE_URL);

// Get Deployment ID from URL
const urlParams = new URLSearchParams(window.location.search);
const deploymentId = urlParams.get('id');

class DeploymentDataUploader {
    constructor() {
        this.uploadedFiles = [];
        this.deploymentData = null;
        this.init();
    }

    async init() {
        if (!deploymentId) {
            alert('Keine Deployment ID gefunden!');
            window.location.href = '/deployments.html';
            return;
        }

        this.setupEventListeners();
        await this.loadDeployment();
        await this.loadUploadedFiles();
    }

    setupEventListeners() {
        // Docker Image Upload
        document.getElementById('upload-image-btn').addEventListener('click', () => {
            this.uploadDockerImage();
        });

        // DockerHub Import
        document.getElementById('import-dockerhub-btn').addEventListener('click', () => {
            this.importFromDockerHub();
        });

        // Static Files Drag & Drop
        const dropzone = document.getElementById('dropzone');
        const fileInput = document.getElementById('static-files-input');

        dropzone.addEventListener('click', () => fileInput.click());

        dropzone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropzone.classList.add('border-blue-500', 'bg-blue-50');
        });

        dropzone.addEventListener('dragleave', () => {
            dropzone.classList.remove('border-blue-500', 'bg-blue-50');
        });

        dropzone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropzone.classList.remove('border-blue-500', 'bg-blue-50');
            this.handleFiles(e.dataTransfer.files);
        });

        fileInput.addEventListener('change', (e) => {
            this.handleFiles(e.target.files);
        });

        // Upload Files Button
        document.getElementById('upload-files-btn').addEventListener('click', () => {
            this.uploadStaticFiles();
        });

        // Deploy Button
        document.getElementById('deploy-btn').addEventListener('click', () => {
            this.deployInfrastructure();
        });

        // Radio Buttons (Image Source)
        document.querySelectorAll('input[name="image-source"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                document.getElementById('upload-section').classList.toggle('hidden', e.target.value !== 'upload');
                document.getElementById('dockerhub-section').classList.toggle('hidden', e.target.value !== 'dockerhub');
            });
        });

        // Logout
        document.getElementById('logout-btn').addEventListener('click', () => {
            localStorage.removeItem('authToken');
            window.location.href = '/login.html';
        });
    }

    async loadDeployment() {
        try {
            const deployment = await apiClient.get(`/api/v1/deployments/${deploymentId}`);
            this.deploymentData = deployment;

            // Display Deployment Info
            document.getElementById('deployment-info').innerHTML = `
                <h2 class="text-lg font-semibold mb-2">Deployment Details</h2>
                <div class="text-sm text-gray-600">
                    <p><strong>ID:</strong> ${deployment.id}</p>
                    <p><strong>Name:</strong> ${deployment.name || 'N/A'}</p>
                    <p><strong>Status:</strong> <span class="px-2 py-1 rounded text-xs font-semibold ${this.getStatusClass(deployment.status)}">${deployment.status}</span></p>
                </div>
            `;
        } catch (error) {
            console.error('Failed to load deployment:', error);
            alert('Deployment konnte nicht geladen werden');
        }
    }

    async loadUploadedFiles() {
        try {
            const response = await apiClient.get(`/api/v1/data-upload/list/${deploymentId}`);

            const listEl = document.getElementById('uploaded-files-list');
            if (response.files.length === 0) {
                listEl.innerHTML = '<p class="text-gray-500 text-sm">Noch keine Dateien hochgeladen</p>';
            } else {
                listEl.innerHTML = `
                    <div class="space-y-2">
                        ${response.files.map(file => `
                            <div class="flex items-center justify-between p-3 bg-gray-50 rounded">
                                <div class="flex-1">
                                    <p class="text-sm font-medium">${file.key.split('/').pop()}</p>
                                    <p class="text-xs text-gray-500">${this.formatSize(file.size_bytes)}</p>
                                </div>
                                <span class="text-xs text-gray-400">${new Date(file.last_modified).toLocaleString('de-DE')}</span>
                            </div>
                        `).join('')}
                    </div>
                    <p class="text-sm text-gray-600 mt-4">
                        <strong>Gesamt:</strong> ${response.files.length} Dateien, ${this.formatSize(response.total_size_bytes)}
                    </p>
                `;
            }
        } catch (error) {
            console.error('Failed to load uploaded files:', error);
        }
    }

    async uploadDockerImage() {
        const fileInput = document.getElementById('docker-image-file');
        const file = fileInput.files[0];

        if (!file) {
            alert('Bitte wähle eine Datei aus');
            return;
        }

        // Validate file type
        if (!file.name.endsWith('.tar.gz') && !file.name.endsWith('.tar')) {
            alert('Nur .tar.gz oder .tar Dateien erlaubt');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        // Show progress
        const progressEl = document.getElementById('upload-progress');
        progressEl.classList.remove('hidden');

        try {
            // Use XMLHttpRequest for progress tracking
            await this.uploadWithProgress(
                `/api/v1/data-upload/docker-image?deployment_id=${deploymentId}`,
                formData,
                (percent) => {
                    document.getElementById('progress-bar').style.width = `${percent}%`;
                    document.getElementById('progress-text').textContent = `${percent}%`;
                }
            );

            alert('Docker Image erfolgreich hochgeladen!');
            await this.loadUploadedFiles();

        } catch (error) {
            console.error('Upload failed:', error);
            alert('Upload fehlgeschlagen: ' + error.message);
        } finally {
            progressEl.classList.add('hidden');
        }
    }

    async uploadWithProgress(url, formData, onProgress) {
        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();

            xhr.upload.addEventListener('progress', (e) => {
                if (e.lengthComputable) {
                    const percentComplete = Math.round((e.loaded * 100) / e.total);
                    onProgress(percentComplete);
                }
            });

            xhr.addEventListener('load', () => {
                if (xhr.status >= 200 && xhr.status < 300) {
                    resolve(JSON.parse(xhr.responseText));
                } else {
                    reject(new Error(`Upload failed: ${xhr.statusText}`));
                }
            });

            xhr.addEventListener('error', () => {
                reject(new Error('Upload failed'));
            });

            xhr.open('POST', `${API_BASE_URL}${url}`);
            xhr.setRequestHeader('Authorization', `Bearer ${localStorage.getItem('authToken')}`);
            xhr.withCredentials = true;
            xhr.send(formData);
        });
    }

    async importFromDockerHub() {
        const image = document.getElementById('dockerhub-image').value;
        const username = document.getElementById('dockerhub-username').value;
        const token = document.getElementById('dockerhub-token').value;

        if (!image) {
            alert('Bitte gib einen Image Namen ein');
            return;
        }

        try {
            const result = await apiClient.post('/api/v1/data-upload/from-dockerhub', {
                deployment_id: deploymentId,
                image,
                dockerhub_username: username || null,
                dockerhub_token: token || null
            });

            alert('DockerHub Import gestartet! Dies kann einige Minuten dauern.');

            // Reload uploaded files after a delay
            setTimeout(() => this.loadUploadedFiles(), 5000);

        } catch (error) {
            console.error('Import failed:', error);
            alert('Import fehlgeschlagen: ' + error.message);
        }
    }

    handleFiles(files) {
        for (const file of files) {
            this.uploadedFiles.push(file);
        }
        this.renderFileList();
    }

    renderFileList() {
        const fileList = document.getElementById('file-list');

        if (this.uploadedFiles.length === 0) {
            fileList.innerHTML = '';
            document.getElementById('upload-files-btn').disabled = true;
            return;
        }

        document.getElementById('upload-files-btn').disabled = false;

        fileList.innerHTML = this.uploadedFiles.map((file, index) => `
            <div class="flex items-center justify-between p-2 bg-gray-50 rounded">
                <span class="text-sm">${file.name} (${this.formatSize(file.size)})</span>
                <button onclick="window.deploymentDataUploader.removeFile(${index})" class="text-red-600 text-sm hover:text-red-800">
                    Entfernen
                </button>
            </div>
        `).join('');
    }

    removeFile(index) {
        this.uploadedFiles.splice(index, 1);
        this.renderFileList();
    }

    formatSize(bytes) {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
        return (bytes / (1024 * 1024 * 1024)).toFixed(1) + ' GB';
    }

    async uploadStaticFiles() {
        if (this.uploadedFiles.length === 0) {
            alert('Bitte wähle Dateien aus');
            return;
        }

        const formData = new FormData();
        this.uploadedFiles.forEach(file => {
            formData.append('files', file);
        });

        try {
            const response = await fetch(
                `${API_BASE_URL}/api/v1/data-upload/files?deployment_id=${deploymentId}`,
                {
                    method: 'POST',
                    credentials: 'include',
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('authToken')}`
                    },
                    body: formData
                }
            );

            if (!response.ok) throw new Error('Upload failed');

            const result = await response.json();
            alert(`${result.uploaded.length} Dateien erfolgreich hochgeladen!`);

            this.uploadedFiles = [];
            this.renderFileList();
            await this.loadUploadedFiles();

        } catch (error) {
            console.error('Upload failed:', error);
            alert('Upload fehlgeschlagen: ' + error.message);
        }
    }

    async deployInfrastructure() {
        if (!confirm('Infrastruktur jetzt zu AWS deployen?')) return;

        try {
            const result = await apiClient.post(`/api/v1/deployments/${deploymentId}/deploy`, {});
            alert('Deployment gestartet!');
            window.location.href = `/deployment-status.html?id=${deploymentId}`;
        } catch (error) {
            console.error('Deployment failed:', error);
            alert('Deployment fehlgeschlagen: ' + error.message);
        }
    }

    getStatusClass(status) {
        const classes = {
            'pending': 'bg-yellow-100 text-yellow-800',
            'in_progress': 'bg-blue-100 text-blue-800',
            'deployed': 'bg-green-100 text-green-800',
            'failed': 'bg-red-100 text-red-800'
        };
        return classes[status] || 'bg-gray-100 text-gray-800';
    }
}

// Initialize
const deploymentDataUploader = new DeploymentDataUploader();
window.deploymentDataUploader = deploymentDataUploader;
