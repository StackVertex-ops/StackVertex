/**
 * OverCloud - Infrastructure Designer API Module
 *
 * Funktionen für den Zugriff auf Designer-Endpoints des Backends
 */

import { APIClient } from '../lib/api-client.js';

// API Client Instanz
const apiClient = new APIClient('http://localhost:8000');

/**
 * Speichert Architecture JSON aus dem Designer
 * @param {Object} data - Save request data
 * @param {string} data.name - Architecture name
 * @param {string} data.description - Architecture description
 * @param {Object} data.architecture_json - Complete architecture JSON from designer
 * @param {string} data.owner - Owner user ID (optional)
 * @returns {Promise<Object>} Save response with architecture_id
 */
export async function saveDesignerArchitecture(data) {
    return await apiClient.post('/api/v1/designer/save', data);
}

/**
 * Lädt Architecture JSON für den Designer
 * @param {string} architectureId - UUID of architecture
 * @returns {Promise<Object>} Complete architecture JSON for designer
 */
export async function loadDesignerArchitecture(architectureId) {
    return await apiClient.get(`/api/v1/designer/load/${architectureId}`);
}

/**
 * Generiert Terraform HCL Code aus Architecture JSON
 * @param {Object} architectureJson - Complete architecture JSON from designer
 * @returns {Promise<Object>} Generated Terraform files and metadata
 * @returns {Object.files} - Dict of filename -> content
 * @returns {number.component_count} - Number of components processed
 * @returns {Array<string>.warnings} - Generation warnings
 */
export async function generateTerraform(architectureJson) {
    return await apiClient.post('/api/v1/designer/generate-terraform', {
        architecture_json: architectureJson
    });
}

/**
 * Validiert Architecture JSON
 * @param {Object} architectureJson - Architecture JSON to validate
 * @returns {Promise<Object>} Validation result
 * @returns {boolean.valid} - True if architecture is valid
 * @returns {Array<string>.errors} - Validation errors
 * @returns {Array<string>.warnings} - Validation warnings
 * @returns {number.component_count} - Number of components
 * @returns {number.connection_count} - Number of connections
 */
export async function validateArchitecture(architectureJson) {
    return await apiClient.post('/api/v1/designer/validate', {
        architecture_json: architectureJson
    });
}

/**
 * Exportiert Terraform als ZIP-Download
 * @param {Object} architectureJson - Complete architecture JSON
 * @returns {Promise<Blob>} ZIP file blob
 */
export async function downloadTerraformZip(architectureJson) {
    try {
        const result = await generateTerraform(architectureJson);

        // Create ZIP using JSZip (must be imported separately)
        if (typeof JSZip === 'undefined') {
            throw new Error('JSZip library not loaded');
        }

        const zip = new JSZip();

        // Add all Terraform files to ZIP
        for (const [filename, content] of Object.entries(result.files)) {
            zip.file(filename, content);
        }

        // Generate ZIP blob
        return await zip.generateAsync({ type: 'blob' });
    } catch (error) {
        console.error('Error creating Terraform ZIP:', error);
        throw error;
    }
}

/**
 * Trigger download of Terraform ZIP
 * @param {Object} architectureJson - Complete architecture JSON
 * @param {string} filename - ZIP filename (default: terraform.zip)
 */
export async function triggerTerraformDownload(architectureJson, filename = 'terraform.zip') {
    try {
        const blob = await downloadTerraformZip(architectureJson);

        // Create download link
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    } catch (error) {
        console.error('Error downloading Terraform:', error);
        throw error;
    }
}
