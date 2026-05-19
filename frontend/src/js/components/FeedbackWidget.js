/**
 * Feedback Widget
 *
 * Fixed Button rechts unten + Modal für anonymes Feedback
 */

import { api } from '../lib/api.js';

export class FeedbackWidget {
    constructor() {
        this.isOpen = false;
        this.screenshot = null;
        this.render();
        this.attachListeners();
    }

    render() {
        // Feedback Button (fixed rechts unten)
        const button = document.createElement('button');
        button.id = 'feedback-button';
        button.className = 'fixed bottom-6 right-6 bg-blue-600 hover:bg-blue-700 text-white rounded-full p-4 shadow-lg transition-all duration-200 z-50';
        button.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
            </svg>
        `;
        button.title = 'Feedback senden';
        document.body.appendChild(button);

        // Feedback Modal
        const modal = document.createElement('div');
        modal.id = 'feedback-modal';
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 hidden';
        modal.innerHTML = `
            <div class="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
                <div class="flex justify-between items-center mb-4">
                    <h2 class="text-xl font-semibold text-gray-900">Feedback senden</h2>
                    <button id="feedback-close" class="text-gray-400 hover:text-gray-600">
                        <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>

                <form id="feedback-form" class="space-y-4">
                    <!-- Type Selection -->
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Typ</label>
                        <div class="grid grid-cols-2 gap-2">
                            <button type="button" class="feedback-type-btn" data-type="bug">
                                🐛 Bug
                            </button>
                            <button type="button" class="feedback-type-btn" data-type="feature">
                                💡 Feature Request
                            </button>
                            <button type="button" class="feedback-type-btn" data-type="feedback">
                                💬 Feedback
                            </button>
                            <button type="button" class="feedback-type-btn" data-type="other">
                                📝 Sonstiges
                            </button>
                        </div>
                        <input type="hidden" id="feedback-type" name="type" required>
                    </div>

                    <!-- Title -->
                    <div>
                        <label for="feedback-title" class="block text-sm font-medium text-gray-700 mb-1">
                            Titel <span class="text-red-500">*</span>
                        </label>
                        <input
                            type="text"
                            id="feedback-title"
                            name="title"
                            required
                            minlength="5"
                            maxlength="200"
                            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                            placeholder="Kurze Zusammenfassung..."
                        >
                    </div>

                    <!-- Description -->
                    <div>
                        <label for="feedback-description" class="block text-sm font-medium text-gray-700 mb-1">
                            Beschreibung <span class="text-red-500">*</span>
                        </label>
                        <textarea
                            id="feedback-description"
                            name="description"
                            required
                            minlength="10"
                            maxlength="1000"
                            rows="4"
                            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                            placeholder="Beschreibe dein Anliegen..."
                        ></textarea>
                        <p class="text-xs text-gray-500 mt-1">
                            <span id="char-count">0</span>/1000 Zeichen
                        </p>
                    </div>

                    <!-- Email (Optional) -->
                    <div>
                        <label for="feedback-email" class="block text-sm font-medium text-gray-700 mb-1">
                            Email (optional)
                        </label>
                        <input
                            type="email"
                            id="feedback-email"
                            name="email"
                            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                            placeholder="Für Rückmeldung..."
                        >
                        <p class="text-xs text-gray-500 mt-1">
                            Optional: Wenn du eine Antwort erhalten möchtest
                        </p>
                    </div>

                    <!-- Screenshot Upload -->
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">
                            Screenshot (optional)
                        </label>
                        <div class="border-2 border-dashed border-gray-300 rounded-md p-4 text-center hover:border-gray-400 transition">
                            <input
                                type="file"
                                id="feedback-screenshot"
                                name="screenshot"
                                accept="image/png,image/jpeg,image/jpg,image/webp"
                                class="hidden"
                            >
                            <label for="feedback-screenshot" class="cursor-pointer">
                                <div id="screenshot-preview" class="space-y-2">
                                    <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                                    </svg>
                                    <div class="text-sm text-gray-600">
                                        <span class="font-medium text-blue-600">Bild hochladen</span> oder Drag & Drop
                                    </div>
                                    <p class="text-xs text-gray-500">PNG, JPG, WebP (max 5MB)</p>
                                </div>
                            </label>
                        </div>
                    </div>

                    <!-- Submit / Cancel -->
                    <div class="flex gap-2 pt-2">
                        <button
                            type="submit"
                            id="feedback-submit"
                            class="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-md transition disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            Senden
                        </button>
                        <button
                            type="button"
                            id="feedback-cancel"
                            class="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition"
                        >
                            Abbrechen
                        </button>
                    </div>
                </form>

                <!-- Success Message (hidden by default) -->
                <div id="feedback-success" class="hidden">
                    <div class="text-center py-8">
                        <div class="text-green-500 text-5xl mb-4">✓</div>
                        <h3 class="text-lg font-semibold text-gray-900 mb-2">Vielen Dank!</h3>
                        <p class="text-gray-600 mb-4">Dein Feedback wurde erfolgreich gesendet.</p>
                        <button
                            id="feedback-success-close"
                            class="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-md transition"
                        >
                            Schließen
                        </button>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);

        // Add CSS for type buttons
        const style = document.createElement('style');
        style.textContent = `
            .feedback-type-btn {
                padding: 0.5rem;
                border: 2px solid #e5e7eb;
                border-radius: 0.375rem;
                background: white;
                transition: all 0.2s;
                font-size: 0.875rem;
            }
            .feedback-type-btn:hover {
                border-color: #3b82f6;
                background: #eff6ff;
            }
            .feedback-type-btn.active {
                border-color: #3b82f6;
                background: #3b82f6;
                color: white;
            }
        `;
        document.head.appendChild(style);
    }

    attachListeners() {
        // Open Modal
        document.getElementById('feedback-button').addEventListener('click', () => {
            this.openModal();
        });

        // Close Modal
        document.getElementById('feedback-close').addEventListener('click', () => {
            this.closeModal();
        });

        document.getElementById('feedback-cancel').addEventListener('click', () => {
            this.closeModal();
        });

        // Close on overlay click
        document.getElementById('feedback-modal').addEventListener('click', (e) => {
            if (e.target.id === 'feedback-modal') {
                this.closeModal();
            }
        });

        // Type Selection
        document.querySelectorAll('.feedback-type-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('.feedback-type-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                document.getElementById('feedback-type').value = btn.dataset.type;
            });
        });

        // Character Counter
        const textarea = document.getElementById('feedback-description');
        textarea.addEventListener('input', () => {
            document.getElementById('char-count').textContent = textarea.value.length;
        });

        // Screenshot Upload
        const fileInput = document.getElementById('feedback-screenshot');
        fileInput.addEventListener('change', (e) => {
            this.handleScreenshotUpload(e.target.files[0]);
        });

        // Drag & Drop
        const dropZone = fileInput.parentElement;
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('border-blue-500');
        });

        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('border-blue-500');
        });

        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('border-blue-500');
            const file = e.dataTransfer.files[0];
            if (file && file.type.startsWith('image/')) {
                this.handleScreenshotUpload(file);
            }
        });

        // Form Submit
        document.getElementById('feedback-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.submitFeedback();
        });

        // Success Close
        document.getElementById('feedback-success-close').addEventListener('click', () => {
            this.closeModal();
        });
    }

    handleScreenshotUpload(file) {
        if (!file) return;

        // Validate file type
        const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp'];
        if (!allowedTypes.includes(file.type)) {
            this.showError('Ungültiges Bildformat. Erlaubt: PNG, JPG, WebP');
            return;
        }

        // Validate file size (max 5MB)
        if (file.size > 5 * 1024 * 1024) {
            this.showError('Bild zu groß (max 5MB)');
            return;
        }

        this.screenshot = file;

        // Show preview
        const reader = new FileReader();
        reader.onload = (e) => {
            const preview = document.getElementById('screenshot-preview');
            preview.innerHTML = `
                <div class="relative">
                    <img src="${e.target.result}" class="max-h-32 mx-auto rounded border" alt="Screenshot">
                    <button
                        type="button"
                        id="remove-screenshot"
                        class="absolute top-0 right-0 bg-red-500 text-white rounded-full p-1 transform translate-x-2 -translate-y-2"
                    >
                        <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>
            `;

            // Remove screenshot
            document.getElementById('remove-screenshot').addEventListener('click', () => {
                this.screenshot = null;
                document.getElementById('feedback-screenshot').value = '';
                this.render();
                this.attachListeners();
            });
        };
        reader.readAsDataURL(file);
    }

    async submitFeedback() {
        const form = document.getElementById('feedback-form');
        const submitBtn = document.getElementById('feedback-submit');
        const formData = new FormData(form);

        // Validate type selected
        if (!formData.get('type')) {
            this.showError('Bitte wähle einen Typ aus');
            return;
        }

        // Add screenshot if present
        if (this.screenshot) {
            formData.append('screenshot', this.screenshot);
        }

        // Add URL and browser info
        formData.append('url', window.location.href);
        formData.append('user_agent', navigator.userAgent);
        formData.append('browser_info', JSON.stringify({
            language: navigator.language,
            platform: navigator.platform,
            screen: `${screen.width}x${screen.height}`,
            viewport: `${window.innerWidth}x${window.innerHeight}`,
        }));

        // Disable submit button
        submitBtn.disabled = true;
        submitBtn.textContent = 'Wird gesendet...';

        try {
            const response = await fetch('/api/v1/feedback', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Fehler beim Senden');
            }

            // Show success message
            document.getElementById('feedback-form').classList.add('hidden');
            document.getElementById('feedback-success').classList.remove('hidden');

            // Reset form after 3 seconds
            setTimeout(() => {
                this.resetForm();
            }, 3000);

        } catch (error) {
            console.error('Feedback submission error:', error);
            this.showError(error.message);
            submitBtn.disabled = false;
            submitBtn.textContent = 'Senden';
        }
    }

    showError(message) {
        // Simple alert for now (könnte durch besseres UI ersetzt werden)
        alert(message);
    }

    openModal() {
        this.isOpen = true;
        document.getElementById('feedback-modal').classList.remove('hidden');
        // Focus first type button
        document.querySelector('.feedback-type-btn').focus();
    }

    closeModal() {
        this.isOpen = false;
        document.getElementById('feedback-modal').classList.add('hidden');
        this.resetForm();
    }

    resetForm() {
        document.getElementById('feedback-form').reset();
        document.getElementById('feedback-form').classList.remove('hidden');
        document.getElementById('feedback-success').classList.add('hidden');
        document.querySelectorAll('.feedback-type-btn').forEach(b => b.classList.remove('active'));
        this.screenshot = null;
        document.getElementById('char-count').textContent = '0';
        document.getElementById('feedback-submit').disabled = false;
        document.getElementById('feedback-submit').textContent = 'Senden';
    }
}

// Auto-initialize if not in admin area
if (!window.location.pathname.startsWith('/admin')) {
    window.addEventListener('DOMContentLoaded', () => {
        new FeedbackWidget();
    });
}
