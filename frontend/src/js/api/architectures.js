/**
 * OverCloud - Architectures API Module
 *
 * Funktionen für den Zugriff auf Architecture-Endpoints des Backends
 */

import { APIClient } from '../lib/api-client.js';

// API Client Instanz - SECURITY FIX: No hardcoded URL
const apiClient = new APIClient();

/**
 * Liste aller Architekturen abrufen
 * @param {number} skip - Anzahl zu überspringender Einträge (Pagination)
 * @param {number} limit - Maximale Anzahl zurückzugebender Einträge
 * @returns {Promise<Array>} Liste von Architekturen
 */
export async function listArchitectures(skip = 0, limit = 100) {
    const endpoint = `/api/v1/architectures?skip=${skip}&limit=${limit}`;
    return await apiClient.get(endpoint);
}

/**
 * Einzelne Architektur anhand ihrer ID abrufen
 * @param {string} id - Architecture ID
 * @returns {Promise<Object>} Architecture-Objekt
 */
export async function getArchitecture(id) {
    return await apiClient.get(`/api/v1/architectures/${id}`);
}

/**
 * Neue Architektur erstellen
 * @param {Object} data - Architecture-Daten
 * @returns {Promise<Object>} Erstellte Architektur
 */
export async function createArchitecture(data) {
    return await apiClient.post('/api/v1/architectures', data);
}

/**
 * Bestehende Architektur aktualisieren
 * @param {string} id - Architecture ID
 * @param {Object} data - Aktualisierte Architecture-Daten
 * @returns {Promise<Object>} Aktualisierte Architektur
 */
export async function updateArchitecture(id, data) {
    return await apiClient.put(`/api/v1/architectures/${id}`, data);
}

/**
 * Architektur löschen
 * @param {string} id - Architecture ID
 * @returns {Promise<void>}
 */
export async function deleteArchitecture(id) {
    return await apiClient.delete(`/api/v1/architectures/${id}`);
}
