/**
 * OverCloud - Architecture Builder Page
 *
 * Hauptseite für Erstellung und Bearbeitung von Architekturen
 */

import { renderArchitectureForm, setupFormHandlers } from '../components/architecture-form.js';
import { EXAMPLE_ARCHITECTURES, getExampleById } from '../lib/example-architectures.js';
import { createArchitecture, getArchitecture, updateArchitecture } from '../api/architectures.js';
import jsonlint from 'jsonlint-mod';

/**
 * Rendert die Architecture Builder Page
 * @param {HTMLElement} container - Container-Element
 * @param {string} architectureId - Optional: ID für Edit-Modus
 */
export async function renderArchitectureBuilder(container, architectureId = null) {
    const isEditMode = !!architectureId;

    // Zeige Loading State
    container.innerHTML = renderLoadingState();

    try {
        let architecture = null;

        if (isEditMode) {
            // Lade existierende Architektur
            architecture = await getArchitecture(architectureId);
        }

        // Rendere Builder UI
        container.innerHTML = renderBuilderUI(architecture);

        // Setup Event Handlers
        setupBuilderHandlers(container, architecture);
    } catch (error) {
        console.error('Fehler beim Laden der Architektur:', error);
        container.innerHTML = renderErrorState(error);
    }
}

/**
 * Rendert Loading State
 */
function renderLoadingState() {
    return `
        <div class="flex items-center justify-center py-12">
            <div class="text-center">
                <div class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
                <p class="text-gray-600 dark:text-gray-400">Lade Builder...</p>
            </div>
        </div>
    `;
}

/**
 * Rendert Error State
 */
function renderErrorState(error) {
    return `
        <div class="text-center py-12">
            <div class="text-6xl mb-4">⚠️</div>
            <h3 class="text-2xl font-semibold text-gray-900 dark:text-white mb-2">
                Fehler beim Laden
            </h3>
            <p class="text-gray-600 dark:text-gray-400 mb-6">
                ${error.message || 'Der Builder konnte nicht geladen werden.'}
            </p>
            <button
                onclick="window.location.hash = '#/architectures'"
                class="inline-flex items-center px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors"
            >
                Zurück zur Übersicht
            </button>
        </div>
    `;
}

/**
 * Rendert die komplette Builder UI
 */
function renderBuilderUI(architecture) {
    const isEditMode = !!architecture;
    const currentStep = 'form';  // Immer Formular anzeigen

    return `
        <div class="max-w-7xl mx-auto">
            <!-- Header -->
            <div class="mb-6">
                <div class="flex items-center justify-between">
                    <div>
                        <h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-2">
                            ${isEditMode ? 'Architektur bearbeiten' : 'Neue Architektur erstellen'}
                        </h1>
                        <p class="text-gray-600 dark:text-gray-400">
                            ${isEditMode ? 'Passe deine Cloud-Architektur an' : 'Definiere die Anforderungen und baue deine Cloud-Infrastruktur'}
                        </p>
                    </div>
                    <button
                        onclick="window.location.hash = '#/architectures'"
                        class="text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
                    >
                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                        </svg>
                    </button>
                </div>
            </div>

            <!-- Steps Indicator -->
            ${renderStepsIndicator(currentStep, isEditMode)}

            <!-- Content Area -->
            <div id="builder-content" class="mt-6">
                ${currentStep === 'form' ? renderFormStep(architecture) : renderCanvasStep(architecture)}
            </div>
        </div>
    `;
}

/**
 * Rendert Steps Indicator
 */
function renderStepsIndicator(currentStep, isEditMode) {
    if (isEditMode) {
        return ''; // Keine Steps im Edit-Modus
    }

    const steps = [
        { id: 'form', name: 'Anforderungen', icon: '📋' },
        { id: 'canvas', name: 'Builder', icon: '🏗️' }
    ];

    return `
        <div class="flex items-center justify-center space-x-4 mb-8">
            ${steps.map((step, index) => {
                const isActive = step.id === currentStep;
                const isCompleted = false; // TODO: Track completed steps

                return `
                    <div class="flex items-center">
                        <div class="flex flex-col items-center">
                            <div class="flex items-center justify-center w-12 h-12 rounded-full border-2 ${
                                isActive
                                    ? 'border-blue-500 bg-blue-500 text-white'
                                    : isCompleted
                                    ? 'border-green-500 bg-green-500 text-white'
                                    : 'border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-500'
                            }">
                                <span class="text-xl">${step.icon}</span>
                            </div>
                            <span class="text-sm font-medium mt-2 ${
                                isActive ? 'text-blue-600 dark:text-blue-400' : 'text-gray-600 dark:text-gray-400'
                            }">
                                ${step.name}
                            </span>
                        </div>
                        ${index < steps.length - 1 ? `
                            <div class="w-24 h-0.5 bg-gray-300 dark:bg-gray-600 mx-4"></div>
                        ` : ''}
                    </div>
                `;
            }).join('')}
        </div>
    `;
}

/**
 * Rendert Form Step
 */
function renderFormStep(architecture) {
    // Wenn architecture vom Backend kommt (Edit-Modus), transformiere zu Form-Format
    let formData = architecture;
    if (architecture && architecture.architecture_json) {
        // Backend-Format → Form-Format
        formData = {
            ...architecture.architecture_json,
            metadata: {
                ...architecture.architecture_json.metadata,
                name: architecture.name,  // Name vom Backend-Level überschreiben
                description: architecture.description
            },
            version: architecture.version
        };
    }

    return `
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <!-- Form (2/3) -->
            <div class="lg:col-span-2">
                ${renderArchitectureForm(formData)}
            </div>

            <!-- Sidebar (1/3) -->
            <div class="space-y-6">
                ${renderExamplesCard()}
                ${renderTipsCard()}
            </div>
        </div>
    `;
}

/**
 * Rendert Examples Card
 */
function renderExamplesCard() {
    return `
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Beispiele laden
            </h3>
            <p class="text-sm text-gray-600 dark:text-gray-400 mb-4">
                Starte mit einer vorgefertigten Architektur
            </p>
            <div class="space-y-2">
                ${EXAMPLE_ARCHITECTURES.map(example => `
                    <button
                        onclick="window.OverCloud.loadExample('${example.id}')"
                        class="w-full text-left px-4 py-3 bg-gray-50 dark:bg-gray-900 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                    >
                        <div class="font-medium text-gray-900 dark:text-white text-sm">
                            ${example.name}
                        </div>
                        <div class="text-xs text-gray-600 dark:text-gray-400 mt-1">
                            ${example.description}
                        </div>
                        <div class="flex items-center mt-2 space-x-2">
                            <span class="text-xs px-2 py-0.5 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded">
                                ${example.provider.toUpperCase()}
                            </span>
                            <span class="text-xs px-2 py-0.5 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded">
                                ${example.complexity}
                            </span>
                        </div>
                    </button>
                `).join('')}
            </div>
        </div>
    `;
}

/**
 * Rendert Tips Card
 */
function renderTipsCard() {
    return `
        <div class="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-6">
            <h3 class="text-lg font-semibold text-blue-900 dark:text-blue-100 mb-3">
                Tipps
            </h3>
            <ul class="space-y-2 text-sm text-blue-800 dark:text-blue-200">
                <li class="flex items-start">
                    <svg class="w-5 h-5 mr-2 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
                    </svg>
                    <span>Definiere deine Anforderungen so genau wie möglich</span>
                </li>
                <li class="flex items-start">
                    <svg class="w-5 h-5 mr-2 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
                    </svg>
                    <span>Die KI empfiehlt basierend auf deinen Anforderungen die beste Architektur</span>
                </li>
                <li class="flex items-start">
                    <svg class="w-5 h-5 mr-2 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
                    </svg>
                    <span>Du kannst die Architektur später im JSON-Editor anpassen</span>
                </li>
            </ul>
        </div>
    `;
}

/**
 * Rendert Canvas Step (JSON Editor)
 */
function renderCanvasStep(architecture) {
    const jsonContent = architecture ? JSON.stringify(architecture, null, 2) : '';

    return `
        <div class="grid grid-cols-1 gap-6">
            <!-- Placeholder für Visual Builder -->
            <div class="bg-gradient-to-br from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 rounded-lg p-12 text-center border-2 border-dashed border-blue-300 dark:border-blue-700">
                <div class="text-6xl mb-4">🚧</div>
                <h3 class="text-2xl font-semibold text-gray-900 dark:text-white mb-2">
                    Visual Builder kommt bald
                </h3>
                <p class="text-gray-600 dark:text-gray-400 mb-6 max-w-2xl mx-auto">
                    Der grafische Drag-&-Drop Builder ist in Entwicklung.
                    Verwende vorerst den JSON-Editor unten, um deine Architektur zu definieren.
                </p>
                <div class="flex items-center justify-center space-x-4">
                    <div class="flex items-center">
                        <div class="w-3 h-3 bg-green-500 rounded-full animate-pulse mr-2"></div>
                        <span class="text-sm text-gray-600 dark:text-gray-400">Drag & Drop Components</span>
                    </div>
                    <div class="flex items-center">
                        <div class="w-3 h-3 bg-green-500 rounded-full animate-pulse mr-2"></div>
                        <span class="text-sm text-gray-600 dark:text-gray-400">Visual Relationships</span>
                    </div>
                    <div class="flex items-center">
                        <div class="w-3 h-3 bg-green-500 rounded-full animate-pulse mr-2"></div>
                        <span class="text-sm text-gray-600 dark:text-gray-400">Live Preview</span>
                    </div>
                </div>
            </div>

            <!-- JSON Editor -->
            <div class="bg-white dark:bg-gray-800 rounded-lg shadow-md">
                <div class="border-b border-gray-200 dark:border-gray-700 px-6 py-4 flex items-center justify-between">
                    <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
                        JSON Schema Editor
                    </h3>
                    <div class="flex items-center space-x-2">
                        <button
                            id="validate-json-btn"
                            class="px-4 py-2 bg-green-600 hover:bg-green-700 text-white text-sm rounded-lg transition-colors flex items-center space-x-2"
                        >
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                            </svg>
                            <span>Validieren</span>
                        </button>
                        <button
                            id="format-json-btn"
                            class="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white text-sm rounded-lg transition-colors flex items-center space-x-2"
                        >
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path>
                            </svg>
                            <span>Formatieren</span>
                        </button>
                    </div>
                </div>
                <div class="p-6">
                    <!-- JSON Editor mit Line Numbers -->
                    <div class="flex border border-gray-300 dark:border-gray-600 rounded-lg overflow-hidden h-96">
                        <!-- Line Numbers -->
                        <div
                            id="json-line-numbers"
                            class="bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400 font-mono text-sm text-right select-none"
                            style="padding: 12px 8px; line-height: 1.5; min-width: 3.5rem; user-select: none; white-space: pre; overflow-y: hidden; height: 100%;"
                        >1</div>
                        <!-- Textarea -->
                        <textarea
                            id="json-editor"
                            class="flex-1 px-4 py-3 font-mono text-sm bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none border-0"
                            style="line-height: 1.5; height: 100%; overflow-y: auto;"
                            placeholder='{\n  "version": "1.0.0",\n  "metadata": {...},\n  "requirements": {...},\n  "architecture": {...}\n}'
                        >${jsonContent}</textarea>
                    </div>
                    <div id="json-validation-result" class="mt-3"></div>
                </div>
            </div>

            <!-- Actions -->
            <div class="flex justify-between items-center">
                <button
                    id="back-to-form-btn"
                    class="px-6 py-3 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                >
                    Zurück zu Anforderungen
                </button>
                <div class="flex space-x-3">
                    <button
                        onclick="window.location.hash = '#/architectures'"
                        class="px-6 py-3 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                    >
                        Abbrechen
                    </button>
                    <button
                        id="save-architecture-btn"
                        class="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors flex items-center space-x-2"
                    >
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4"></path>
                        </svg>
                        <span>Architektur speichern</span>
                    </button>
                </div>
            </div>
        </div>
    `;
}

/**
 * Setup Builder Event Handlers
 */
function setupBuilderHandlers(container, architecture) {
    const isEditMode = !!architecture;

    // Form Handlers (wenn Form sichtbar)
    const formContainer = container.querySelector('#architecture-form');
    if (formContainer) {
        setupFormHandlers(
            container,
            (formData) => handleFormSubmit(container, formData, architecture),
            () => {
                window.location.hash = '#/architectures';
            }
        );
    }

    // JSON Editor Handlers
    setupJSONEditorHandlers(container, architecture);

    // Example Loader
    window.OverCloud = window.OverCloud || {};
    window.OverCloud.loadExample = (exampleId) => {
        loadExampleArchitecture(container, exampleId);
    };
}

/**
 * Handle Form Submit
 */
function handleFormSubmit(container, formData, existingArchitecture = null) {
    // Wechsle zum Canvas Step mit vorausgefüllten Daten
    const builderContent = container.querySelector('#builder-content');
    if (builderContent) {
        let architecture;

        if (existingArchitecture && existingArchitecture.architecture_json) {
            // Edit-Modus: Merge Formular-Daten mit existierendem architecture_json
            architecture = {
                ...existingArchitecture.architecture_json,
                metadata: {
                    ...existingArchitecture.architecture_json.metadata,
                    ...formData.metadata,  // Formular-Daten überschreiben
                    updated_at: new Date().toISOString()
                },
                version: formData.version,
                requirements: formData.requirements
            };
        } else {
            // Create-Modus: Neues Architecture-Objekt erstellen
            architecture = {
                ...formData,
                metadata: {
                    ...formData.metadata,
                    created_at: new Date().toISOString(),
                    updated_at: new Date().toISOString()
                },
                architecture: {
                    components: [],
                    relationships: []
                }
            };
        }

        builderContent.innerHTML = renderCanvasStep(architecture);
        setupJSONEditorHandlers(container, existingArchitecture);

        // Scroll to top
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
}

/**
 * Setup JSON Editor Handlers
 */
function setupJSONEditorHandlers(container, architecture) {
    const jsonEditor = container.querySelector('#json-editor');
    const lineNumbers = container.querySelector('#json-line-numbers');
    const validateBtn = container.querySelector('#validate-json-btn');
    const formatBtn = container.querySelector('#format-json-btn');
    const saveBtn = container.querySelector('#save-architecture-btn');
    const backBtn = container.querySelector('#back-to-form-btn');

    // Initialize Line Numbers
    if (jsonEditor && lineNumbers) {
        // Initial update (mit kleinem Delay um sicherzustellen dass DOM ready ist)
        setTimeout(() => {
            updateLineNumbers(jsonEditor, lineNumbers);
        }, 0);

        // Update line numbers on input
        jsonEditor.addEventListener('input', () => {
            updateLineNumbers(jsonEditor, lineNumbers);
        });

        // Synchronize scrolling
        jsonEditor.addEventListener('scroll', () => {
            lineNumbers.scrollTop = jsonEditor.scrollTop;
        });
    }

    if (validateBtn && jsonEditor) {
        validateBtn.addEventListener('click', () => {
            validateJSON(jsonEditor);
        });
    }

    if (formatBtn && jsonEditor) {
        formatBtn.addEventListener('click', () => {
            formatJSON(jsonEditor);
            // Update line numbers after formatting
            if (lineNumbers) {
                updateLineNumbers(jsonEditor, lineNumbers);
            }
        });
    }

    if (saveBtn && jsonEditor) {
        saveBtn.addEventListener('click', async () => {
            await saveArchitecture(jsonEditor, architecture);
        });
    }

    if (backBtn) {
        backBtn.addEventListener('click', () => {
            const builderContent = container.querySelector('#builder-content');
            if (builderContent) {
                builderContent.innerHTML = renderFormStep(architecture);
                setupFormHandlers(
                    container,
                    (formData) => handleFormSubmit(container, formData),
                    () => {
                        window.location.hash = '#/architectures';
                    }
                );
            }
        });
    }
}

/**
 * Update Line Numbers für JSON Editor
 */
function updateLineNumbers(jsonEditor, lineNumbers) {
    const lines = jsonEditor.value.split('\n').length;
    const lineNumbersArray = [];

    for (let i = 1; i <= lines; i++) {
        lineNumbersArray.push(i);
    }

    lineNumbers.textContent = lineNumbersArray.join('\n');
}

/**
 * Highlight Error Line in Line Numbers
 */
function highlightErrorLine(lineNumbers, errorLine) {
    if (!errorLine || !lineNumbers) return;

    // Create HTML with highlighted line
    const lines = lineNumbers.textContent.split('\n');
    const htmlLines = lines.map((num, index) => {
        const lineNum = index + 1;
        if (lineNum === errorLine) {
            return `<span style="color: #dc2626; font-weight: 600;">${num}</span>`;
        }
        return num;
    });

    lineNumbers.innerHTML = htmlLines.join('\n');
}

/**
 * Clear Error Highlighting
 */
function clearErrorHighlight(lineNumbers) {
    if (!lineNumbers) return;
    // Reset to plain text
    const text = lineNumbers.textContent || lineNumbers.innerText;
    lineNumbers.textContent = text;
}

/**
 * Pre-Check: Finde unbalancierte Klammern
 */
function findUnbalancedBracket(text) {
    const lines = text.split('\n');
    const stack = [];
    let lastContentLine = 0;

    for (let lineNum = 0; lineNum < lines.length; lineNum++) {
        const line = lines[lineNum].trim();

        // Track letzte Zeile mit Content
        if (line.length > 0) {
            lastContentLine = lineNum + 1;
        }

        for (let col = 0; col < lines[lineNum].length; col++) {
            const char = lines[lineNum][col];

            if (char === '{' || char === '[') {
                stack.push({ char, line: lineNum + 1, col });
            } else if (char === '}') {
                if (stack.length === 0 || stack[stack.length - 1].char !== '{') {
                    return {
                        line: lineNum + 1,
                        col,
                        type: 'unexpected_close',
                        expected: '{'
                    };
                }
                stack.pop();
            } else if (char === ']') {
                if (stack.length === 0 || stack[stack.length - 1].char !== '[') {
                    return {
                        line: lineNum + 1,
                        col,
                        type: 'unexpected_close',
                        expected: '['
                    };
                }
                stack.pop();
            }
        }
    }

    // Wenn Stack nicht leer: unclosed brackets
    if (stack.length > 0) {
        const unclosed = stack[stack.length - 1];
        const closingChar = unclosed.char === '{' ? '}' : ']';

        return {
            line: lastContentLine, // Zeige die letzte Content-Zeile, nicht wo es geöffnet wurde
            col: unclosed.col,
            type: 'unclosed',
            char: unclosed.char,
            closingChar: closingChar,
            openedAtLine: unclosed.line  // Wo es geöffnet wurde
        };
    }

    return null;
}

/**
 * Validiere JSON
 */
function validateJSON(jsonEditor) {
    const resultDiv = document.getElementById('json-validation-result');
    const lineNumbers = document.getElementById('json-line-numbers');

    // Clear previous error highlighting
    clearErrorHighlight(lineNumbers);

    // Pre-Check: Bracket Balancing
    const bracketError = findUnbalancedBracket(jsonEditor.value);
    if (bracketError) {
        highlightErrorLine(lineNumbers, bracketError.line);

        let errorMsg = '';
        let details = '';

        if (bracketError.type === 'unclosed') {
            errorMsg = `Fehlende schließende Klammer <code class="px-1 py-0.5 bg-red-200 dark:bg-red-800 rounded font-mono">${bracketError.closingChar}</code>`;
            details = `Die öffnende Klammer <code class="px-1 py-0.5 bg-blue-100 dark:bg-blue-900 rounded font-mono">${bracketError.char}</code> wurde in Zeile ${bracketError.openedAtLine} geöffnet, aber nie geschlossen.`;
        } else {
            errorMsg = `Unerwartete schließende Klammer <code class="px-1 py-0.5 bg-red-200 dark:bg-red-800 rounded font-mono">}</code>`;
            details = `Es gibt keine passende öffnende Klammer <code class="px-1 py-0.5 bg-blue-100 dark:bg-blue-900 rounded font-mono">${bracketError.expected}</code> für diese schließende Klammer.`;
        }

        resultDiv.innerHTML = `
            <div class="p-4 bg-red-50 dark:bg-red-900/20 border border-red-300 dark:border-red-700 rounded-lg">
                <div class="flex items-start">
                    <svg class="w-5 h-5 text-red-600 dark:text-red-400 mr-2 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"></path>
                    </svg>
                    <div class="flex-1">
                        <h4 class="font-medium text-red-800 dark:text-red-200">Klammer-Fehler</h4>
                        <p class="mt-1 text-sm text-red-700 dark:text-red-300">
                            <strong class="text-red-900 dark:text-red-100">Zeile ${bracketError.line}:</strong> ${errorMsg}
                        </p>
                        <p class="mt-2 text-xs text-red-600 dark:text-red-400">
                            ${details}
                        </p>
                        <div class="mt-3 p-2 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-300 dark:border-yellow-700 rounded text-xs">
                            <p class="text-yellow-800 dark:text-yellow-200">
                                ⚠️ <strong>Hinweis:</strong> Bei verschachtelten JSON-Strukturen kann der tatsächliche Fehler auch <strong>früher</strong> im Code vorkommen (z.B. zwischen Zeile ${bracketError.openedAtLine} und ${bracketError.line}).
                            </p>
                            <p class="text-yellow-700 dark:text-yellow-300 mt-1">
                                💡 Prüfe alle Klammern in diesem Bereich sorgfältig.
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        `;
        return;
    }

    try {
        // Nutze jsonlint für präzisere Fehler-Erkennung
        const json = jsonlint.parse(jsonEditor.value);

        // Basic validation
        const errors = [];

        if (!json.version) errors.push('Feld "version" fehlt');
        if (!json.metadata) errors.push('Feld "metadata" fehlt');
        if (!json.requirements) errors.push('Feld "requirements" fehlt');
        if (!json.architecture) errors.push('Feld "architecture" fehlt');

        if (errors.length > 0) {
            resultDiv.innerHTML = `
                <div class="p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-300 dark:border-yellow-700 rounded-lg">
                    <div class="flex items-start">
                        <svg class="w-5 h-5 text-yellow-600 dark:text-yellow-400 mr-2 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"></path>
                        </svg>
                        <div>
                            <h4 class="font-medium text-yellow-800 dark:text-yellow-200">Validierungs-Warnungen</h4>
                            <ul class="mt-2 text-sm text-yellow-700 dark:text-yellow-300 list-disc list-inside">
                                ${errors.map(err => `<li>${err}</li>`).join('')}
                            </ul>
                        </div>
                    </div>
                </div>
            `;
        } else {
            resultDiv.innerHTML = `
                <div class="p-4 bg-green-50 dark:bg-green-900/20 border border-green-300 dark:border-green-700 rounded-lg">
                    <div class="flex items-center">
                        <svg class="w-5 h-5 text-green-600 dark:text-green-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
                        </svg>
                        <span class="font-medium text-green-800 dark:text-green-200">JSON ist gültig!</span>
                    </div>
                </div>
            `;
        }
    } catch (error) {
        // JSONLint gibt präzisere Fehler-Informationen
        let errorLine = null;
        let errorColumn = null;
        let errorMessage = error.message;

        // JSONLint Error hat .hash Property mit detaillierten Infos
        if (error.hash && error.hash.line) {
            errorLine = error.hash.line;
            errorColumn = error.hash.loc?.first_column;
        } else {
            // Fallback: Extrahiere aus Message (z.B. "Parse error on line 65:")
            const lineMatch = error.message.match(/line (\d+)/i);
            if (lineMatch) {
                errorLine = parseInt(lineMatch[1]);
            }
        }

        // Highlight fehlerhafte Zeile in Line Numbers
        if (errorLine) {
            highlightErrorLine(lineNumbers, errorLine);
        }

        // Formatiere Error Message
        let errorDetails = errorMessage;
        if (errorLine) {
            const columnInfo = errorColumn ? ` Spalte ${errorColumn}` : '';
            errorDetails = `<strong class="text-red-900 dark:text-red-100">Zeile ${errorLine}${columnInfo}:</strong> ${errorMessage.replace(/Parse error on line \d+:/i, '').replace(/line \d+/i, '').trim()}`;
        }

        resultDiv.innerHTML = `
            <div class="p-4 bg-red-50 dark:bg-red-900/20 border border-red-300 dark:border-red-700 rounded-lg">
                <div class="flex items-start">
                    <svg class="w-5 h-5 text-red-600 dark:text-red-400 mr-2 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"></path>
                    </svg>
                    <div class="flex-1">
                        <h4 class="font-medium text-red-800 dark:text-red-200">JSON-Fehler</h4>
                        <p class="mt-1 text-sm text-red-700 dark:text-red-300">${errorDetails}</p>
                        ${errorLine ? `
                            <div class="mt-2 text-xs text-red-600 dark:text-red-400">
                                💡 Tipp: Scroll zu Zeile ${errorLine} links im Editor
                            </div>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;
    }
}

/**
 * Formatiere JSON
 */
function formatJSON(jsonEditor) {
    try {
        const json = JSON.parse(jsonEditor.value);
        jsonEditor.value = JSON.stringify(json, null, 2);
    } catch (error) {
        alert('JSON ist ungültig und kann nicht formatiert werden.');
    }
}

/**
 * Speichere Architektur
 */
async function saveArchitecture(jsonEditor, existingArchitecture) {
    const saveBtn = document.getElementById('save-architecture-btn');

    try {
        const architecture = JSON.parse(jsonEditor.value);

        // Transform zu Backend-Format
        const payload = {
            name: architecture.metadata?.name || existingArchitecture?.name || 'Unnamed Architecture',
            description: architecture.metadata?.description || existingArchitecture?.description || null,
            version: architecture.version || existingArchitecture?.version || '1.0.0',
            architecture_json: architecture,  // Komplettes JSON als architecture_json
            owner: existingArchitecture?.owner || 'user'  // TODO: Später von Authentication holen
        };

        // Zeige Loading State
        saveBtn.disabled = true;
        saveBtn.innerHTML = `
            <svg class="animate-spin h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span>Speichere...</span>
        `;

        let response;
        if (existingArchitecture?.id) {
            // Update
            response = await updateArchitecture(existingArchitecture.id, payload);
        } else {
            // Create
            response = await createArchitecture(payload);
        }

        // Success
        alert('Architektur erfolgreich gespeichert!');
        window.location.hash = '#/architectures';
    } catch (error) {
        console.error('Fehler beim Speichern:', error);
        alert('Fehler beim Speichern der Architektur: ' + error.message);

        // Reset Button
        saveBtn.disabled = false;
        saveBtn.innerHTML = `
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4"></path>
            </svg>
            <span>Architektur speichern</span>
        `;
    }
}

/**
 * Lade Example Architecture
 */
function loadExampleArchitecture(container, exampleId) {
    const example = getExampleById(exampleId);

    if (!example) {
        alert('Beispiel nicht gefunden');
        return;
    }

    // Entferne ID aus Example, damit es als neue Architektur behandelt wird
    // (Examples sind Templates, keine existierenden Architekturen)
    if (example?.metadata?.id) {
        delete example.metadata.id;
    }

    // Wechsle zum Canvas mit Example-Daten
    const builderContent = container.querySelector('#builder-content');
    if (builderContent) {
        builderContent.innerHTML = renderCanvasStep(example);
        setupJSONEditorHandlers(container, example);

        // Scroll to top
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
}

