/**
 * DOM Utilities - SECURITY: XSS Prevention
 *
 * Safe alternatives to innerHTML with user input.
 */

/**
 * Escape HTML to prevent XSS
 * @param {string} unsafe - Unsafe user input
 * @returns {string} Safe escaped HTML
 */
export function escapeHtml(unsafe) {
    if (typeof unsafe !== 'string') return '';

    return unsafe
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

/**
 * SECURITY: Set text content safely (no XSS risk)
 * Use this instead of innerHTML when displaying user input.
 *
 * @param {HTMLElement} element - Target element
 * @param {string} text - Text to display
 */
export function setTextSafely(element, text) {
    element.textContent = text;
}

/**
 * SECURITY: Set HTML safely with user input escaped
 * Only use when you need HTML structure with user data.
 *
 * @param {HTMLElement} element - Target element
 * @param {string} htmlTemplate - HTML template with {{placeholders}}
 * @param {Object} userData - User data to inject (will be escaped)
 *
 * Example:
 *   setHtmlSafely(div, '<h1>{{title}}</h1><p>{{description}}</p>', {
 *     title: userInput.title,
 *     description: userInput.description
 *   });
 */
export function setHtmlSafely(element, htmlTemplate, userData = {}) {
    let safeHtml = htmlTemplate;

    // Replace all {{key}} with escaped user data
    Object.keys(userData).forEach(key => {
        const placeholder = new RegExp(`{{${key}}}`, 'g');
        const safeValue = escapeHtml(userData[key]);
        safeHtml = safeHtml.replace(placeholder, safeValue);
    });

    element.innerHTML = safeHtml;
}

/**
 * Create element with safe text content
 * @param {string} tagName - HTML tag name
 * @param {string} text - Text content (will be set safely)
 * @param {string} className - Optional CSS classes
 * @returns {HTMLElement} Created element
 */
export function createTextElement(tagName, text, className = '') {
    const element = document.createElement(tagName);
    if (className) element.className = className;
    element.textContent = text; // Safe: no XSS
    return element;
}

/**
 * SECURITY NOTE:
 *
 * All innerHTML usage in this codebase has been reviewed:
 *
 * SAFE USES (static templates):
 * - main.js: Static error messages
 * - TabSystem.js: Static tab templates
 * - component-palette.js: Static component templates
 * - CIDRCalculator.js: Static UI templates
 * - architecture-form.js: Static form templates
 *
 * POTENTIAL XSS RISKS (user input):
 * - architecture-list.js: Displays architecture names/descriptions
 *   → FIXED: Use setTextSafely() or escapeHtml()
 *
 * If you need to display Markdown or rich text:
 * 1. Install DOMPurify: npm install dompurify
 * 2. Use: import DOMPurify from 'dompurify';
 *         element.innerHTML = DOMPurify.sanitize(userInput);
 */
