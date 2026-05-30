/**
 * FAQ Accordion Component
 *
 * Displays FAQs in an expandable accordion format with smooth animations.
 * Supports Markdown rendering in answers.
 * Can auto-load FAQs from API or accept data.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export class FaqAccordion {
    constructor(container, options = {}) {
        this.container = typeof container === 'string' ? document.getElementById(container) : container;
        this.options = {
            allowMultiple: false, // Allow multiple accordions open at once
            animationDuration: 300, // Animation duration in ms
            autoLoad: false, // Auto-load FAQs from API
            enableSearch: false, // Enable search functionality
            enableCategoryFilter: false, // Enable category filter
            trackViews: false, // Track FAQ views
            ...options,
        };
        this.openItems = new Set();
        this.allFaqs = [];
        this.filteredFaqs = [];
        this.selectedCategory = null;

        if (this.options.autoLoad) {
            this.init();
        }
    }

    async init() {
        await this.loadFaqs();
    }

    async loadFaqs() {
        try {
            const response = await fetch(`${API_BASE_URL}/faq`);
            if (!response.ok) throw new Error('Failed to load FAQs');

            const data = await response.json();

            if (data.success && data.data) {
                const categories = data.data.categories || [];
                this.allFaqs = this.flattenFaqs(categories);
                this.filteredFaqs = [...this.allFaqs];
                this.render(this.filteredFaqs);
            }
        } catch (error) {
            console.warn('API not available, using mock FAQs:', error);

            // Mock data fallback
            const mockData = {
                success: true,
                data: {
                    categories: [
                        {
                            name: 'Erste Schritte',
                            slug: 'getting-started',
                            icon: '🚀',
                            faqs: [
                                {
                                    id: 1,
                                    question: 'Was ist StackVertex?',
                                    answer: 'StackVertex ist eine Multi-Cloud-Infrastruktur-Orchestrierungsplattform, die es ermöglicht, Cloud-Infrastruktur aus Anforderungen statt aus einzelnen Ressourcen zu modellieren. Alles ist JSON-basiert, versionierbar und transparent.'
                                },
                                {
                                    id: 2,
                                    question: 'Welche Cloud-Provider werden unterstützt?',
                                    answer: 'Aktuell: AWS (MVP). Geplant: Azure (Phase 2), Google Cloud (Phase 3). Die Architektur ist von Anfang an multi-cloud-fähig.'
                                }
                            ]
                        },
                        {
                            name: 'Sicherheit',
                            slug: 'security',
                            icon: '🔐',
                            faqs: [
                                {
                                    id: 3,
                                    question: 'Wie werden meine AWS-Zugangsdaten gespeichert?',
                                    answer: 'Wir nutzen AWS AssumeRole (keine Access Keys). Alle Secrets werden verschlüsselt gespeichert (write-only) und niemals im Klartext angezeigt.'
                                },
                                {
                                    id: 4,
                                    question: 'Ist meine Infrastruktur-Konfiguration sicher?',
                                    answer: 'Ja! Alle Daten werden verschlüsselt gespeichert. Audit-Logs für alle Aktionen. Least-Privilege IAM-Policies für maximale Sicherheit.'
                                }
                            ]
                        },
                        {
                            name: 'Preise & Abrechnung',
                            slug: 'pricing',
                            icon: '💰',
                            faqs: [
                                {
                                    id: 5,
                                    question: 'Was kostet StackVertex?',
                                    answer: 'Wir bieten einen kostenlosen Starter-Plan. Für Production-Deployments siehe unsere Pricing-Seite.'
                                }
                            ]
                        }
                    ]
                }
            };

            const categories = mockData.data.categories || [];
            this.allFaqs = this.flattenFaqs(categories);
            this.filteredFaqs = [...this.allFaqs];
            this.render(this.filteredFaqs);
        }
    }

    flattenFaqs(categories) {
        const allFaqs = [];
        categories.forEach(cat => {
            cat.faqs.forEach(faq => {
                allFaqs.push({
                    ...faq,
                    category_name: cat.name,
                    category_slug: cat.slug,
                    category_icon: cat.icon || '📌',
                });
            });
        });
        return allFaqs;
    }

    showError() {
        if (this.container) {
            this.container.innerHTML = `
                <div class="text-center py-8 text-red-500">
                    Fehler beim Laden der FAQs.
                </div>
            `;
        }
    }

    /**
     * Render FAQs in accordion format
     * @param {Array} faqs - Array of FAQ objects
     */
    render(faqs) {
        if (!faqs || faqs.length === 0) {
            this.container.innerHTML = `
                <div class="text-center py-8 text-gray-500">
                    Keine FAQs verfügbar.
                </div>
            `;
            return;
        }

        const html = faqs.map((faq, index) => this.renderFaqItem(faq, index)).join('');
        this.container.innerHTML = `<div class="faq-accordion space-y-3">${html}</div>`;

        // Attach event listeners
        this.attachEventListeners();
    }

    /**
     * Render single FAQ item
     * @param {Object} faq - FAQ object
     * @param {number} index - Item index
     * @returns {string} HTML string
     */
    renderFaqItem(faq, index) {
        const isOpen = this.openItems.has(faq.faq_id);

        return `
            <div class="faq-item border border-gray-200 rounded-lg overflow-hidden hover:border-indigo-300 transition-colors"
                 data-faq-id="${faq.faq_id}">
                <!-- Question Header -->
                <button
                    class="faq-header w-full flex items-center justify-between p-4 text-left bg-white hover:bg-gray-50 transition-colors"
                    data-index="${index}"
                    aria-expanded="${isOpen}"
                    aria-controls="faq-content-${index}">
                    <span class="font-medium text-gray-900 pr-8">${this.escapeHtml(faq.question)}</span>
                    <svg
                        class="faq-icon flex-shrink-0 w-5 h-5 text-indigo-600 transform transition-transform duration-${this.options.animationDuration} ${isOpen ? 'rotate-180' : ''}"
                        xmlns="http://www.w3.org/2000/svg"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                    </svg>
                </button>

                <!-- Answer Content -->
                <div
                    id="faq-content-${index}"
                    class="faq-content overflow-hidden transition-all duration-${this.options.animationDuration}"
                    style="max-height: ${isOpen ? 'none' : '0'}">
                    <div class="p-4 pt-0 prose prose-sm max-w-none">
                        ${this.renderMarkdown(faq.answer)}
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Attach click event listeners to FAQ headers
     */
    attachEventListeners() {
        const headers = this.container.querySelectorAll('.faq-header');
        headers.forEach(header => {
            header.addEventListener('click', (e) => this.handleToggle(e));
        });
    }

    /**
     * Handle accordion toggle
     * @param {Event} e - Click event
     */
    handleToggle(e) {
        const button = e.currentTarget;
        const faqItem = button.closest('.faq-item');
        const faqId = faqItem.dataset.faqId;
        const content = faqItem.querySelector('.faq-content');
        const icon = button.querySelector('.faq-icon');
        const isOpen = this.openItems.has(faqId);

        if (isOpen) {
            // Close
            this.closeItem(faqItem, content, icon, faqId);
        } else {
            // Close others if not allowing multiple
            if (!this.options.allowMultiple) {
                this.closeAll();
            }
            // Open
            this.openItem(faqItem, content, icon, faqId);

            // Track view
            if (this.options.trackViews) {
                this.trackView(faqId);
            }
        }

        // Update aria-expanded
        button.setAttribute('aria-expanded', !isOpen);
    }

    async trackView(faqId) {
        try {
            await fetch(`${API_BASE_URL}/faq/${faqId}`, {
                method: 'GET',
            });
        } catch (error) {
            console.debug('Failed to track FAQ view:', error);
        }
    }

    /**
     * Open accordion item
     */
    openItem(faqItem, content, icon, faqId) {
        this.openItems.add(faqId);

        // Get content height
        content.style.maxHeight = 'none';
        const height = content.scrollHeight;
        content.style.maxHeight = '0';

        // Trigger reflow
        requestAnimationFrame(() => {
            content.style.maxHeight = `${height}px`;
            icon.style.transform = 'rotate(180deg)';
        });

        // Remove max-height after animation
        setTimeout(() => {
            if (this.openItems.has(faqId)) {
                content.style.maxHeight = 'none';
            }
        }, this.options.animationDuration);
    }

    /**
     * Close accordion item
     */
    closeItem(faqItem, content, icon, faqId) {
        this.openItems.delete(faqId);

        // Set height before closing
        content.style.maxHeight = `${content.scrollHeight}px`;

        // Trigger reflow
        requestAnimationFrame(() => {
            content.style.maxHeight = '0';
            icon.style.transform = 'rotate(0deg)';
        });
    }

    /**
     * Close all open items
     */
    closeAll() {
        const openItems = this.container.querySelectorAll('.faq-item');
        openItems.forEach(item => {
            const faqId = item.dataset.faqId;
            if (this.openItems.has(faqId)) {
                const content = item.querySelector('.faq-content');
                const icon = item.querySelector('.faq-icon');
                const button = item.querySelector('.faq-header');
                this.closeItem(item, content, icon, faqId);
                button.setAttribute('aria-expanded', 'false');
            }
        });
    }

    /**
     * Render Markdown (basic implementation)
     * @param {string} markdown - Markdown text
     * @returns {string} HTML string
     */
    renderMarkdown(markdown) {
        // Einfache Markdown-Konvertierung
        let html = markdown;

        // Code blocks
        html = html.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');

        // Inline code
        html = html.replace(/`([^`]+)`/g, '<code class="bg-gray-100 px-1 py-0.5 rounded text-sm">$1</code>');

        // Bold
        html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

        // Italic
        html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');

        // Links
        html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" class="text-indigo-600 hover:text-indigo-700" target="_blank" rel="noopener noreferrer">$1</a>');

        // Line breaks
        html = html.replace(/\n\n/g, '</p><p>');
        html = html.replace(/\n/g, '<br>');

        // Lists
        html = html.replace(/^- (.+)$/gm, '<li>$1</li>');
        html = html.replace(/(<li>.*<\/li>)/s, '<ul class="list-disc list-inside">$1</ul>');

        return `<p>${html}</p>`;
    }

    /**
     * Escape HTML to prevent XSS
     * @param {string} text - Text to escape
     * @returns {string} Escaped text
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Destroy component
     */
    destroy() {
        this.container.innerHTML = '';
        this.openItems.clear();
    }
}

export default FaqAccordion;
