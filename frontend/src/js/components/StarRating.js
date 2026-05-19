/**
 * StarRating Component
 * Wiederverwendbar für Input (clickable) + Display (readonly)
 */

export class StarRating {
    /**
     * Create StarRating component
     * @param {Object} options - Configuration options
     * @param {HTMLElement} options.container - Container element
     * @param {number} options.rating - Initial rating (0-5)
     * @param {boolean} options.readonly - Readonly mode (default: false)
     * @param {Function} options.onChange - Callback when rating changes
     */
    constructor({ container, rating = 0, readonly = false, onChange = null }) {
        this.container = container;
        this.rating = rating;
        this.readonly = readonly;
        this.onChange = onChange;
        this.hoveredRating = 0;

        this.render();
        if (!readonly) {
            this.attachEventListeners();
        }
    }

    /**
     * Render stars
     */
    render() {
        this.container.innerHTML = '';
        this.container.className = `star-rating ${this.readonly ? 'readonly' : 'interactive'}`;

        for (let i = 1; i <= 5; i++) {
            const star = document.createElement('span');
            star.className = 'star';
            star.dataset.rating = i;

            // Determine star state
            const currentRating = this.hoveredRating || this.rating;
            if (i <= currentRating) {
                star.classList.add('filled');
                star.textContent = '⭐';
            } else {
                star.classList.add('empty');
                star.textContent = '☆';
            }

            this.container.appendChild(star);
        }

        // Add rating text (nur im readonly mode)
        if (this.readonly && this.rating > 0) {
            const ratingText = document.createElement('span');
            ratingText.className = 'rating-text';
            ratingText.textContent = ` ${this.rating.toFixed(1)}`;
            this.container.appendChild(ratingText);
        }
    }

    /**
     * Attach event listeners (interactive mode)
     */
    attachEventListeners() {
        const stars = this.container.querySelectorAll('.star');

        stars.forEach((star) => {
            // Hover
            star.addEventListener('mouseenter', () => {
                this.hoveredRating = parseInt(star.dataset.rating);
                this.render();
            });

            // Click
            star.addEventListener('click', () => {
                this.rating = parseInt(star.dataset.rating);
                this.hoveredRating = 0;
                this.render();

                // Callback
                if (this.onChange) {
                    this.onChange(this.rating);
                }
            });
        });

        // Reset hover on leave
        this.container.addEventListener('mouseleave', () => {
            this.hoveredRating = 0;
            this.render();
        });
    }

    /**
     * Update rating programmatically
     * @param {number} rating - New rating (0-5)
     */
    setRating(rating) {
        this.rating = rating;
        this.render();
    }

    /**
     * Get current rating
     * @returns {number} Current rating
     */
    getRating() {
        return this.rating;
    }
}

/**
 * Create inline star display (for compact views)
 * @param {number} rating - Rating (0-5)
 * @returns {string} HTML string
 */
export function renderStarsInline(rating) {
    const fullStars = Math.floor(rating);
    const hasHalfStar = rating % 1 >= 0.5;
    const emptyStars = 5 - fullStars - (hasHalfStar ? 1 : 0);

    let html = '<span class="stars-inline">';
    html += '⭐'.repeat(fullStars);
    if (hasHalfStar) {
        html += '⭐'; // Kein half-star emoji, also voll
    }
    html += '☆'.repeat(emptyStars);
    html += '</span>';

    return html;
}
