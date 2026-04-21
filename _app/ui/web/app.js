/* ============================================================
   Swiss HR Local AI Toolbox — frontend logic
   Communique avec Python via window.pywebview.api
   ============================================================ */

'use strict';

// -------- Bibliothèque d'icônes SVG (line style) --------
const ICONS = {
    diplome: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M22 10L12 4 2 10l10 6 10-6z"/><path d="M6 12v5c3 3 9 3 12 0v-5"/></svg>',
    balance: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v18M5 21h14"/><path d="M3 10l4-6 4 6-4 2-4-2z"/><path d="M13 10l4-6 4 6-4 2-4-2z"/></svg>',
    cv: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="3" width="16" height="18" rx="2"/><path d="M8 8h8M8 12h8M8 16h5"/></svg>',
    passeport: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="3" width="14" height="18" rx="2"/><circle cx="12" cy="10" r="3"/><path d="M8 17h8"/></svg>',
    liste: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M9 6h12M9 12h12M9 18h12"/><circle cx="4" cy="6" r="1"/><circle cx="4" cy="12" r="1"/><circle cx="4" cy="18" r="1"/></svg>',
    bulle: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a8 8 0 1 1-3-6.2L21 5v4h-4"/><path d="M8 12h8M8 9h5"/></svg>',
    langue: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M3 5h10"/><path d="M8 3v2c0 6-4 8-5 9"/><path d="M5 10c0 3 4 5 8 5"/><path d="M13 21l5-12 5 12"/><path d="M15 17h6"/></svg>',
    accueil: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12l9-9 9 9"/><path d="M5 10v10h14V10"/><path d="M10 20v-6h4v6"/></svg>',
    loupe: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/></svg>',
    courrier: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 7 9-7"/></svg>',
    default: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="16" height="16" rx="3"/></svg>',
};

function iconHTML(name) {
    return ICONS[name] || ICONS.default;
}

// -------- Attente de l'API pywebview --------
function whenApiReady() {
    return new Promise((resolve) => {
        if (window.pywebview && window.pywebview.api) return resolve(window.pywebview.api);
        window.addEventListener('pywebviewready', () => resolve(window.pywebview.api), { once: true });
    });
}

// -------- Dashboard : rendu des modules --------
async function renderModules(api) {
    const grid = document.getElementById('modules-grid');
    const modules = await api.list_modules();
    if (!Array.isArray(modules) || modules.length === 0) {
        grid.innerHTML = '<div class="loading-placeholder">Aucun module n\'est disponible pour le moment.</div>';
        return;
    }
    grid.innerHTML = '';
    for (const m of modules) {
        const coming = m.statut === 'a_venir';
        const card = document.createElement('div');
        card.className = 'module-card' + (coming ? ' module-card--coming' : '');
        card.dataset.moduleId = m.id;
        card.innerHTML = `
            <span class="module-card__badge ${coming ? 'module-card__badge--coming' : 'module-card__badge--available'}">
                ${coming ? 'À venir' : 'Disponible'}
            </span>
            <div class="module-card__icon">${iconHTML(m.icone)}</div>
            <h3 class="module-card__title">${escapeHTML(m.nom)}</h3>
            <p class="module-card__desc">${escapeHTML(m.description || '')}</p>
            <div class="module-card__cat">${escapeHTML(m.categorie || '')}</div>
        `;
        card.addEventListener('click', () => openModule(m));
        grid.appendChild(card);
    }
}

function openModule(m) {
    if (m.statut === 'a_venir') {
        // Modale de prévisualisation pour les modules non encore implémentés
        document.getElementById('preview-icon').innerHTML = iconHTML(m.icone);
        document.getElementById('preview-title').textContent = m.nom;
        document.getElementById('preview-desc').textContent = m.description || '';
        openModal('modal-module-preview');
        return;
    }
    // Quand un module sera disponible : ouverture de sa vue dédiée (future phase).
    alert(`Le module "${m.nom}" sera bientôt accessible ici.`);
}

// -------- Barre de statut --------
async function refreshStatus(api) {
    const status = await api.status();
    // --- IA
    const llmEl = document.getElementById('status-llm');
    const dot = llmEl.querySelector('.status-dot');
    const label = llmEl.querySelector('.status-value');
    dot.className = 'status-dot';
    llmEl.classList.remove('clickable');
    switch (status.llm.status) {
        case 'ready':
            dot.classList.add('status-dot--ok');
            label.textContent = 'Prête';
            label.title = status.llm.message;
            break;
        case 'no_model':
            dot.classList.add('status-dot--warn');
            label.textContent = 'Aucun modèle chargé';
            llmEl.classList.add('clickable');
            llmEl.onclick = () => openModal('modal-llm-help');
            break;
        case 'unreachable':
            dot.classList.add('status-dot--err');
            label.textContent = 'Non détectée';
            llmEl.classList.add('clickable');
            llmEl.onclick = () => openModal('modal-llm-help');
            break;
        default:
            dot.classList.add('status-dot--err');
            label.textContent = 'Erreur';
    }
    // --- Base juridique (placeholder tant que RAG pas implémenté)
    const baseEl = document.getElementById('status-base');
    const baseDot = baseEl.querySelector('.status-dot');
    const baseVal = baseEl.querySelector('.status-value');
    baseDot.className = 'status-dot status-dot--warn';
    baseVal.textContent = 'à indexer';
}

// -------- Sélecteur d'entité --------
async function renderEntitySelector(api) {
    const current = document.getElementById('entity-current');
    const menu = document.getElementById('entity-menu');
    const trigger = document.getElementById('entity-trigger');
    const entities = await api.list_entities();
    const status = await api.status();
    const activeId = status.entite_active ? status.entite_active.id : null;

    if (!entities.length) {
        current.textContent = 'Aucune entité';
        trigger.disabled = true;
        return;
    }
    const activeEnt = entities.find(e => e.id === activeId) || entities[0];
    current.textContent = activeEnt.nom;
    menu.innerHTML = '';
    for (const e of entities) {
        const li = document.createElement('li');
        li.textContent = e.nom;
        if (e.id === activeEnt.id) li.classList.add('active');
        li.addEventListener('click', async () => {
            await api.set_active_entity(e.id);
            current.textContent = e.nom;
            menu.hidden = true;
            [...menu.children].forEach(c => c.classList.toggle('active', c.textContent === e.nom));
        });
        menu.appendChild(li);
    }
    trigger.addEventListener('click', (ev) => {
        ev.stopPropagation();
        menu.hidden = !menu.hidden;
    });
    document.addEventListener('click', () => { menu.hidden = true; });
}

// -------- Modales --------
function openModal(id) {
    const m = document.getElementById(id);
    if (m) m.hidden = false;
}
function closeModal(id) {
    const m = document.getElementById(id);
    if (m) m.hidden = true;
}
document.addEventListener('click', (ev) => {
    const t = ev.target;
    if (t instanceof HTMLElement && t.matches('[data-close-modal]')) {
        const modal = t.closest('.modal');
        if (modal) modal.hidden = true;
    }
});

// -------- Utils --------
function escapeHTML(str) {
    return String(str).replace(/[&<>"']/g, c => (
        { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
    ));
}

// -------- Bootstrap --------
(async () => {
    const api = await whenApiReady();
    await Promise.all([
        renderEntitySelector(api),
        renderModules(api),
        refreshStatus(api),
    ]);
    // Bouton "Réessayer" dans la modale d'aide LM Studio
    document.getElementById('btn-retry-llm').addEventListener('click', async () => {
        closeModal('modal-llm-help');
        await refreshStatus(api);
    });
    // Rafraîchissement du statut toutes les 10 secondes
    setInterval(() => refreshStatus(api), 10000);
    // Bouton paramètres — placeholder phase suivante
    document.getElementById('btn-settings').addEventListener('click', () => {
        alert('Les paramètres seront disponibles dans la prochaine phase (gestion entités, logos, signatures, réindexation RAG).');
    });
})();
