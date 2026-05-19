/**
 * Admin FAQ Management
 *
 * CRUD operations für FAQs und Kategorien mit Drag & Drop Sortierung.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

let authToken = null;
let allFaqs = [];
let categories = [];
let selectedCategory = null;
let editingFaqId = null;
let sortableInstance = null;

// ============================================================================
// Initialization
// ============================================================================

document.addEventListener('DOMContentLoaded', async () => {
    // Check authentication
    authToken = localStorage.getItem('access_token');
    if (!authToken) {
        window.location.href = '/login.html';
        return;
    }

    // Load data
    await Promise.all([
        loadCategories(),
        loadFaqs(),
        loadAnalytics(),
    ]);

    // Setup event listeners
    setupEventListeners();
});

// ============================================================================
// Data Loading
// ============================================================================

async function loadCategories() {
    try {
        const response = await fetch(`${API_BASE_URL}/faq/categories`);
        const data = await response.json();

        if (data.success) {
            categories = data.categories || [];
            renderCategories();
            renderCategoryFilter();
            renderCategorySelect();
        }
    } catch (error) {
        console.error('Error loading categories:', error);
        showMessage('error', 'Fehler beim Laden der Kategorien');
    }
}

async function loadFaqs(categoryFilter = null, statusFilter = null) {
    try {
        let url = `${API_BASE_URL}/admin/faq?`;
        if (categoryFilter) url += `category=${categoryFilter}&`;
        if (statusFilter) url += `status=${statusFilter}&`;

        const response = await fetch(url, {
            headers: {
                'Authorization': `Bearer ${authToken}`,
            },
        });

        const data = await response.json();

        if (data.success) {
            allFaqs = data.faqs || [];
            renderFaqList();
            initializeSortable();
        }
    } catch (error) {
        console.error('Error loading FAQs:', error);
        showMessage('error', 'Fehler beim Laden der FAQs');
    }
}

async function loadAnalytics() {
    try {
        const response = await fetch(`${API_BASE_URL}/admin/faq/analytics`, {
            headers: {
                'Authorization': `Bearer ${authToken}`,
            },
        });

        const data = await response.json();

        if (data.success && data.analytics) {
            const stats = data.analytics;
            document.getElementById('stat-total').textContent = stats.total_faqs || 0;
            document.getElementById('stat-published').textContent = stats.published || 0;
            document.getElementById('stat-drafts').textContent = stats.drafts || 0;
            document.getElementById('stat-views').textContent = stats.total_views || 0;
        }
    } catch (error) {
        console.error('Error loading analytics:', error);
    }
}

// ============================================================================
// Rendering
// ============================================================================

function renderCategoryFilter() {
    const container = document.getElementById('category-filter');
    if (!container) return;

    container.innerHTML = '';

    // Alle Button
    const allBtn = document.createElement('button');
    allBtn.className = 'category-btn' + (!selectedCategory ? ' active' : '');
    allBtn.textContent = 'Alle';
    allBtn.onclick = () => {
        selectedCategory = null;
        loadFaqs();
        renderCategoryFilter();
    };
    container.appendChild(allBtn);

    // Category Buttons
    categories.forEach(cat => {
        const btn = document.createElement('button');
        btn.className = 'category-btn' + (selectedCategory === cat.slug ? ' active' : '');
        btn.textContent = `${cat.icon || ''} ${cat.name}`;
        btn.onclick = () => {
            selectedCategory = cat.slug;
            loadFaqs(cat.slug);
            renderCategoryFilter();
        };
        container.appendChild(btn);
    });
}

function renderFaqList() {
    const container = document.getElementById('faq-list');
    if (!container) return;

    if (allFaqs.length === 0) {
        container.innerHTML = '<p style="text-align: center; color: var(--gray);">Keine FAQs vorhanden.</p>';
        return;
    }

    container.innerHTML = '';

    allFaqs.forEach(faq => {
        const item = createFaqListItem(faq);
        container.appendChild(item);
    });
}

function createFaqListItem(faq) {
    const item = document.createElement('div');
    item.className = 'faq-item';
    item.dataset.faqId = faq.faq_id;

    const categoryData = categories.find(c => c.slug === faq.category);
    const categoryName = categoryData ? `${categoryData.icon || ''} ${categoryData.name}` : faq.category;

    item.innerHTML = `
        <div class="faq-item-header">
            <h4>${faq.question}</h4>
            <div class="faq-item-actions">
                <button class="btn btn-sm btn-primary" onclick="openEditModal('${faq.faq_id}')">Bearbeiten</button>
                <button class="btn btn-sm btn-danger" onclick="deleteFaq('${faq.faq_id}')">Löschen</button>
            </div>
        </div>
        <div class="faq-item-meta">
            <span>${categoryName}</span>
            <span>${faq.view_count || 0} Views</span>
            <span class="badge ${faq.status === 'published' ? 'badge-published' : 'badge-draft'}">
                ${faq.status === 'published' ? 'Veröffentlicht' : 'Entwurf'}
            </span>
        </div>
    `;

    return item;
}

function renderCategories() {
    const container = document.getElementById('categories-list');
    if (!container) return;

    if (categories.length === 0) {
        container.innerHTML = '<p style="color: var(--gray);">Keine Kategorien vorhanden.</p>';
        return;
    }

    container.innerHTML = '';

    categories.forEach(cat => {
        const item = document.createElement('div');
        item.style.cssText = 'padding: 0.75rem; border-bottom: 1px solid #e5e7eb;';
        item.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span><strong>${cat.icon || ''} ${cat.name}</strong> (${cat.slug})</span>
                <button class="btn btn-sm btn-danger" onclick="deleteCategory('${cat.category_id}')">×</button>
            </div>
        `;
        container.appendChild(item);
    });
}

function renderCategorySelect() {
    const select = document.getElementById('faq-category');
    if (!select) return;

    select.innerHTML = '<option value="">-- Kategorie wählen --</option>';

    categories.forEach(cat => {
        const option = document.createElement('option');
        option.value = cat.slug;
        option.textContent = `${cat.icon || ''} ${cat.name}`;
        select.appendChild(option);
    });
}

// ============================================================================
// Sortable (Drag & Drop)
// ============================================================================

function initializeSortable() {
    const container = document.getElementById('faq-list');
    if (!container) return;

    if (sortableInstance) {
        sortableInstance.destroy();
    }

    sortableInstance = Sortable.create(container, {
        animation: 150,
        handle: '.faq-item',
        onEnd: handleReorder,
    });
}

async function handleReorder(evt) {
    const faqIds = Array.from(document.querySelectorAll('.faq-item')).map(item => item.dataset.faqId);

    try {
        const response = await fetch(`${API_BASE_URL}/admin/faq/reorder`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ faq_ids: faqIds }),
        });

        const data = await response.json();

        if (!data.success) {
            showMessage('error', 'Fehler beim Sortieren');
            await loadFaqs();
        }
    } catch (error) {
        console.error('Error reordering FAQs:', error);
        showMessage('error', 'Fehler beim Sortieren');
    }
}

// ============================================================================
// Modal Handling
// ============================================================================

window.openCreateModal = function() {
    editingFaqId = null;
    document.getElementById('modal-title').textContent = 'Neues FAQ';
    document.getElementById('faq-form').reset();
    document.getElementById('faq-modal').classList.add('active');
};

window.openEditModal = async function(faqId) {
    editingFaqId = faqId;
    const faq = allFaqs.find(f => f.faq_id === faqId);

    if (!faq) {
        showMessage('error', 'FAQ nicht gefunden');
        return;
    }

    document.getElementById('modal-title').textContent = 'FAQ bearbeiten';
    document.getElementById('faq-category').value = faq.category;
    document.getElementById('faq-question').value = faq.question;
    document.getElementById('faq-answer').value = faq.answer;
    document.getElementById('faq-status').value = faq.status;
    document.getElementById('faq-modal').classList.add('active');
};

window.closeFaqModal = function() {
    document.getElementById('faq-modal').classList.remove('active');
    document.getElementById('faq-form').reset();
    document.getElementById('modal-message').innerHTML = '';
    editingFaqId = null;
};

window.openCategoryModal = function() {
    document.getElementById('category-modal').classList.add('active');
};

window.closeCategoryModal = function() {
    document.getElementById('category-modal').classList.remove('active');
    document.getElementById('category-form').reset();
    document.getElementById('category-modal-message').innerHTML = '';
};

// ============================================================================
// Event Listeners
// ============================================================================

function setupEventListeners() {
    // FAQ Form
    document.getElementById('faq-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        await saveFaq();
    });

    // Category Form
    document.getElementById('category-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        await saveCategory();
    });

    // Auto-generate slug from name
    document.getElementById('category-name')?.addEventListener('input', (e) => {
        const slug = e.target.value
            .toLowerCase()
            .replace(/ä/g, 'ae')
            .replace(/ö/g, 'oe')
            .replace(/ü/g, 'ue')
            .replace(/ß/g, 'ss')
            .replace(/[^a-z0-9]+/g, '-')
            .replace(/^-|-$/g, '');
        document.getElementById('category-slug').value = slug;
    });
}

// ============================================================================
// CRUD Operations
// ============================================================================

async function saveFaq() {
    const category = document.getElementById('faq-category').value;
    const question = document.getElementById('faq-question').value;
    const answer = document.getElementById('faq-answer').value;
    const status = document.getElementById('faq-status').value;

    if (!category || !question || !answer) {
        showModalMessage('error', 'Alle Felder müssen ausgefüllt sein');
        return;
    }

    try {
        let response;

        if (editingFaqId) {
            // Update
            response = await fetch(`${API_BASE_URL}/admin/faq/${editingFaqId}`, {
                method: 'PATCH',
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ category, question, answer, status }),
            });
        } else {
            // Create
            response = await fetch(`${API_BASE_URL}/admin/faq`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ category, question, answer, status, sort_order: 0 }),
            });
        }

        const data = await response.json();

        if (data.success) {
            showMessage('success', editingFaqId ? 'FAQ aktualisiert' : 'FAQ erstellt');
            closeFaqModal();
            await loadFaqs();
            await loadAnalytics();
        } else {
            showModalMessage('error', data.detail || 'Fehler beim Speichern');
        }
    } catch (error) {
        console.error('Error saving FAQ:', error);
        showModalMessage('error', 'Fehler beim Speichern');
    }
}

window.deleteFaq = async function(faqId) {
    if (!confirm('FAQ wirklich löschen?')) return;

    try {
        const response = await fetch(`${API_BASE_URL}/admin/faq/${faqId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${authToken}`,
            },
        });

        const data = await response.json();

        if (data.success) {
            showMessage('success', 'FAQ gelöscht');
            await loadFaqs();
            await loadAnalytics();
        } else {
            showMessage('error', data.detail || 'Fehler beim Löschen');
        }
    } catch (error) {
        console.error('Error deleting FAQ:', error);
        showMessage('error', 'Fehler beim Löschen');
    }
};

async function saveCategory() {
    const name = document.getElementById('category-name').value;
    const slug = document.getElementById('category-slug').value;
    const icon = document.getElementById('category-icon').value;

    if (!name || !slug) {
        showCategoryMessage('error', 'Name und Slug sind erforderlich');
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/admin/faq/categories`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ name, slug, icon, sort_order: 0 }),
        });

        const data = await response.json();

        if (data.success) {
            showMessage('success', 'Kategorie erstellt');
            closeCategoryModal();
            await loadCategories();
        } else {
            showCategoryMessage('error', data.detail || 'Fehler beim Speichern');
        }
    } catch (error) {
        console.error('Error saving category:', error);
        showCategoryMessage('error', 'Fehler beim Speichern');
    }
}

window.deleteCategory = async function(categoryId) {
    if (!confirm('Kategorie wirklich löschen? FAQs in dieser Kategorie werden nicht gelöscht.')) return;

    try {
        const response = await fetch(`${API_BASE_URL}/admin/faq/categories/${categoryId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${authToken}`,
            },
        });

        const data = await response.json();

        if (data.success) {
            showMessage('success', 'Kategorie gelöscht');
            await loadCategories();
        } else {
            showMessage('error', data.detail || 'Fehler beim Löschen');
        }
    } catch (error) {
        console.error('Error deleting category:', error);
        showMessage('error', 'Fehler beim Löschen');
    }
};

// ============================================================================
// Utilities
// ============================================================================

function showMessage(type, message) {
    // Create alert at top of container
    const container = document.querySelector('.container');
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.textContent = message;
    container.insertBefore(alert, container.firstChild);

    setTimeout(() => alert.remove(), 5000);
}

function showModalMessage(type, message) {
    const el = document.getElementById('modal-message');
    el.className = `alert alert-${type}`;
    el.textContent = message;
}

function showCategoryMessage(type, message) {
    const el = document.getElementById('category-modal-message');
    el.className = `alert alert-${type}`;
    el.textContent = message;
}
