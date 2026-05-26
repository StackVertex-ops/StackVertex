/**
 * StackVertex - Architecture Validator
 *
 * Client-side Validierung von Architecture JSON
 */

/**
 * Validiere Architecture JSON
 * @param {Object} architectureJson - Architecture JSON Objekt
 * @returns {Object} Validation Result mit {valid, errors, warnings}
 */
export function validateArchitecture(architectureJson) {
    const errors = [];
    const warnings = [];

    // Required Top-Level Fields
    if (!architectureJson.version) {
        errors.push('Feld "version" fehlt');
    }

    if (!architectureJson.metadata) {
        errors.push('Feld "metadata" fehlt');
    } else {
        if (!architectureJson.metadata.name) {
            errors.push('metadata.name fehlt');
        }
        if (!architectureJson.metadata.provider) {
            errors.push('metadata.provider fehlt');
        }
    }

    if (!architectureJson.requirements) {
        warnings.push('Feld "requirements" fehlt - empfohlen für Dokumentation');
    }

    if (!architectureJson.architecture) {
        errors.push('Feld "architecture" fehlt');
    } else {
        // Validate Components
        if (!architectureJson.architecture.components) {
            errors.push('architecture.components fehlt');
        } else if (!Array.isArray(architectureJson.architecture.components)) {
            errors.push('architecture.components muss ein Array sein');
        } else {
            const componentIds = new Set();

            architectureJson.architecture.components.forEach((comp, index) => {
                if (!comp.id) {
                    errors.push(`Component ${index}: Feld "id" fehlt`);
                } else if (componentIds.has(comp.id)) {
                    errors.push(`Component ${comp.id}: Duplicate ID gefunden`);
                } else {
                    componentIds.add(comp.id);
                }

                if (!comp.type) {
                    errors.push(`Component ${comp.id}: Feld "type" fehlt`);
                }

                if (!comp.provider_service) {
                    errors.push(`Component ${comp.id}: Feld "provider_service" fehlt`);
                }

                if (!comp.name) {
                    warnings.push(`Component ${comp.id}: Kein "name" definiert`);
                }
            });

            // Validate Relationships
            if (architectureJson.architecture.relationships) {
                if (!Array.isArray(architectureJson.architecture.relationships)) {
                    errors.push('architecture.relationships muss ein Array sein');
                } else {
                    architectureJson.architecture.relationships.forEach((rel, index) => {
                        if (!rel.from) {
                            errors.push(`Relationship ${index}: Feld "from" fehlt`);
                        } else if (!componentIds.has(rel.from)) {
                            errors.push(`Relationship ${index}: "from" referenziert unbekannte Component "${rel.from}"`);
                        }

                        if (!rel.to) {
                            errors.push(`Relationship ${index}: Feld "to" fehlt`);
                        } else if (!componentIds.has(rel.to)) {
                            errors.push(`Relationship ${index}: "to" referenziert unbekannte Component "${rel.to}"`);
                        }

                        if (!rel.type) {
                            warnings.push(`Relationship ${index}: Kein "type" definiert`);
                        }
                    });
                }
            }
        }
    }

    return {
        valid: errors.length === 0,
        errors,
        warnings
    };
}

/**
 * Validiere JSON Syntax
 * @param {string} jsonString - JSON als String
 * @returns {Object} {valid, error, json}
 */
export function validateJSONSyntax(jsonString) {
    try {
        const json = JSON.parse(jsonString);
        return { valid: true, json };
    } catch (error) {
        return {
            valid: false,
            error: error.message,
            line: extractLineNumber(error.message)
        };
    }
}

/**
 * Extrahiere Line Number aus Error Message
 */
function extractLineNumber(errorMessage) {
    const match = errorMessage.match(/line (\d+)/i);
    return match ? parseInt(match[1]) : null;
}

/**
 * Finde fehlende Dependencies (Components ohne Beziehungen)
 * @param {Object} architectureJson - Architecture JSON
 * @returns {Array} Liste von isolierten Component IDs
 */
export function findIsolatedComponents(architectureJson) {
    if (!architectureJson.architecture?.components || !architectureJson.architecture?.relationships) {
        return [];
    }

    const componentIds = new Set(architectureJson.architecture.components.map(c => c.id));
    const connectedIds = new Set();

    architectureJson.architecture.relationships.forEach(rel => {
        connectedIds.add(rel.from);
        connectedIds.add(rel.to);
    });

    return Array.from(componentIds).filter(id => !connectedIds.has(id));
}

/**
 * Validiere Circular Dependencies
 * @param {Object} architectureJson - Architecture JSON
 * @returns {Array} Liste von zirkulären Abhängigkeiten
 */
export function findCircularDependencies(architectureJson) {
    if (!architectureJson.architecture?.relationships) {
        return [];
    }

    const graph = new Map();
    const circles = [];

    // Build adjacency list
    architectureJson.architecture.relationships.forEach(rel => {
        if (!graph.has(rel.from)) {
            graph.set(rel.from, []);
        }
        graph.get(rel.from).push(rel.to);
    });

    // DFS to find cycles
    const visited = new Set();
    const recStack = new Set();

    function dfs(node, path = []) {
        if (recStack.has(node)) {
            // Found cycle
            const cycleStart = path.indexOf(node);
            circles.push(path.slice(cycleStart).concat(node));
            return;
        }

        if (visited.has(node)) {
            return;
        }

        visited.add(node);
        recStack.add(node);
        path.push(node);

        const neighbors = graph.get(node) || [];
        neighbors.forEach(neighbor => {
            dfs(neighbor, [...path]);
        });

        recStack.delete(node);
    }

    graph.forEach((_, node) => {
        if (!visited.has(node)) {
            dfs(node);
        }
    });

    return circles;
}
