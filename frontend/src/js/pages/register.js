/**
 * OverCloud - Register Page
 *
 * Handles user registration.
 */

import { authAPI } from '../api/auth.js';
import { saveAuthData, redirectIfAuthenticated } from '../lib/auth.js';

/**
 * Initialize register page
 */
function init() {
    // Redirect if already authenticated
    redirectIfAuthenticated();

    // Setup form handler
    const registerForm = document.getElementById('registerForm');
    registerForm.addEventListener('submit', handleRegister);

    // Setup password validation
    const passwordInput = document.getElementById('password');
    passwordInput.addEventListener('input', validatePassword);
}

/**
 * Handle register form submission
 * @param {Event} event - Form submit event
 */
async function handleRegister(event) {
    event.preventDefault();

    const submitBtn = document.getElementById('submitBtn');
    const nameInput = document.getElementById('name');
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');
    const passwordConfirmInput = document.getElementById('passwordConfirm');
    const termsCheckbox = document.getElementById('terms');
    const errorMessage = document.getElementById('errorMessage');

    // Get form values
    const name = nameInput.value.trim();
    const email = emailInput.value.trim();
    const password = passwordInput.value;
    const passwordConfirm = passwordConfirmInput.value;

    // Validate
    if (!name || !email || !password || !passwordConfirm) {
        showError('Bitte fülle alle Felder aus.');
        return;
    }

    if (!termsCheckbox.checked) {
        showError('Bitte akzeptiere die AGB und Datenschutzerklärung.');
        return;
    }

    // Email validation
    if (!isValidEmail(email)) {
        showError('Bitte gib eine gültige E-Mail-Adresse ein.');
        return;
    }

    // Password validation
    const passwordError = validatePasswordStrength(password);
    if (passwordError) {
        showError(passwordError);
        return;
    }

    // Password match
    if (password !== passwordConfirm) {
        showError('Passwörter stimmen nicht überein.');
        return;
    }

    // Show loading state
    const originalText = submitBtn.textContent;
    submitBtn.disabled = true;
    submitBtn.textContent = 'Account wird erstellt...';
    errorMessage.classList.add('hidden');

    try {
        // Register
        const response = await authAPI.register({
            name,
            email,
            password
        });

        // Save auth data
        saveAuthData(response);

        // Show success message
        submitBtn.textContent = '✓ Account erstellt!';
        submitBtn.classList.remove('bg-blue-600', 'hover:bg-blue-700');
        submitBtn.classList.add('bg-green-600');

        // Redirect to dashboard
        setTimeout(() => {
            window.location.href = '/src/index.html';
        }, 1000);

    } catch (error) {
        console.error('Registration failed:', error);

        // Show error message
        let errorText = 'Registrierung fehlgeschlagen. Bitte versuche es erneut.';

        if (error.message.includes('400')) {
            errorText = 'Diese E-Mail-Adresse ist bereits registriert. Bitte melde dich an.';
        } else if (error.message.includes('429')) {
            errorText = 'Zu viele Registrierungsversuche. Bitte warte einen Moment.';
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
 * Validate password on input
 */
function validatePassword() {
    const passwordInput = document.getElementById('password');
    const password = passwordInput.value;

    if (password.length === 0) {
        passwordInput.classList.remove('border-red-500', 'border-green-500');
        return;
    }

    const isValid = validatePasswordStrength(password) === null;

    if (isValid) {
        passwordInput.classList.remove('border-red-500');
        passwordInput.classList.add('border-green-500');
    } else {
        passwordInput.classList.remove('border-green-500');
        passwordInput.classList.add('border-red-500');
    }
}

/**
 * Validate password strength
 * @param {string} password - Password to validate
 * @returns {string|null} Error message or null if valid
 */
function validatePasswordStrength(password) {
    if (password.length < 8) {
        return 'Passwort muss mindestens 8 Zeichen lang sein.';
    }

    if (!/[a-z]/.test(password)) {
        return 'Passwort muss mindestens einen Kleinbuchstaben enthalten.';
    }

    if (!/[A-Z]/.test(password)) {
        return 'Passwort muss mindestens einen Großbuchstaben enthalten.';
    }

    if (!/[0-9]/.test(password)) {
        return 'Passwort muss mindestens eine Zahl enthalten.';
    }

    if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
        return 'Passwort muss mindestens ein Sonderzeichen enthalten.';
    }

    return null;
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
