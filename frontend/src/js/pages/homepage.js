/**
 * Homepage Scripts
 *
 * Handles:
 * - FAQ Accordion
 * - Reviews Display
 * - Smooth Scrolling
 */

import { FaqAccordion } from '../components/FaqAccordion.js';

// Initialize FAQ Accordion when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const faqContainer = document.getElementById('faq-accordion');

    if (faqContainer) {
        new FaqAccordion(faqContainer, {
            autoLoad: true,
            allowMultiple: false,
            trackViews: true,
            animationDuration: 300,
        });
    }
});
