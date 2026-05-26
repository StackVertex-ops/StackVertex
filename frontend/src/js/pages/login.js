/**
 * StackVertex - Login Page
 *
 * Handles user login.
 */

import { authAPI } from '../api/auth.js';
import { saveAuthData, redirectIfAuthenticated, getReturnUrl } from '../lib/auth.js';

// Import FeedbackWidget (auto-initializes on non-admin pages)
import '../components/FeedbackWidget.js';

/**
 * Initialize login page
 */
function init() {
    // Redirect if already authenticated
    redirectIfAuthenticated();

    // Setup form handler
    const loginForm = document.getElementById('loginForm');
    loginForm.addEventListener('submit', handleLogin);

    // Check for error in URL params (e.g., from OAuth redirect)
    const urlParams = new URLSearchParams(window.location.search);
    const error = urlParams.get('error');
    if (error) {
        showError(error);
    }
}

/**
 * Handle login form submission
 * @param {Event} event - Form submit event
 */
async function handleLogin(event) {
    event.preventDefault();

    const submitBtn = document.getElementById('submitBtn');
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');
    const errorMessage = document.getElementById('errorMessage');

    // Get form values
    const email = emailInput.value.trim();
    const password = passwordInput.value;

    // Validate
    if (!email || !password) {
        showError('Bitte fülle alle Felder aus.');
        return;
    }

    // Email validation
    if (!isValidEmail(email)) {
        showError('Bitte gib eine gültige E-Mail-Adresse ein.');
        return;
    }

    // Show loading state
    const originalText = submitBtn.textContent;
    submitBtn.disabled = true;
    submitBtn.textContent = 'Wird angemeldet...';
    errorMessage.classList.add('hidden');

    try {
        // Login
        const response = await authAPI.login(email, password);

        // Save auth data
        saveAuthData(response);

        // Show success message
        submitBtn.textContent = '✓ Erfolgreich!';
        submitBtn.classList.remove('bg-blue-600', 'hover:bg-blue-700');
        submitBtn.classList.add('bg-green-600');

        // Redirect to return URL or dashboard
        const returnUrl = getReturnUrl();

        setTimeout(() => {
            window.location.href = returnUrl;
        }, 500);

    } catch (error) {
        console.error('Login failed:', error);

        // Show error message
        let errorText = 'Anmeldung fehlgeschlagen. Bitte versuche es erneut.';

        if (error.message.includes('401')) {
            errorText = 'E-Mail oder Passwort falsch. Bitte versuche es erneut.';
        } else if (error.message.includes('403')) {
            errorText = error.message.includes('locked')
                ? 'Account gesperrt. Zu viele fehlgeschlagene Anmeldeversuche.'
                : 'Dein Account ist inaktiv. Bitte kontaktiere den Support.';
        } else if (error.message.includes('429')) {
            errorText = 'Zu viele Anmeldeversuche. Bitte warte einen Moment.';
        } else if (!navigator.onLine) {
            errorText = 'Keine Internetverbindung. Bitte prüfe deine Verbindung.';
        }

        showError(errorText);

        // Reset button
        submitBtn.disabled = false;
        submitBtn.textContent = originalText;
    }
}

/**
 * Show error message
 * @param {string} message - Error message to display
 */
function showError(message) {
    const errorMessage = document.getElementById('errorMessage');
    const errorText = document.getElementById('errorText');

    errorText.textContent = message;
    errorMessage.classList.remove('hidden');

    // Scroll to error
    errorMessage.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

/**
 * Validate email format
 * @param {string} email - Email address
 * @returns {boolean} True if valid
 */
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// Initialize page when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
