/* ============================================================
   ARHIANE — L'IA qui remet les RH au centre — frontend logic
   Communique avec Python via window.pywebview.api
   ============================================================ */

'use strict';

/* -------- Icônes SVG (line style) -------- */
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

function iconHTML(name) { return ICONS[name] || ICONS.default; }

/* -------- Attente de l'API pywebview -------- */
function whenApiReady() {
    return new Promise((resolve) => {
        if (window.pywebview && window.pywebview.api) return resolve(window.pywebview.api);
        window.addEventListener('pywebviewready', () => resolve(window.pywebview.api), { once: true });
    });
}

/* -------- Utils -------- */
function escapeHTML(str) {
    return String(str ?? '').replace(/[&<>"']/g, c => (
        { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
    ));
}

function $(sel, root = document) { return root.querySelector(sel); }
function $$(sel, root = document) { return Array.from(root.querySelectorAll(sel)); }

/* -------- Toasts -------- */
function toast(message, variant = 'info', duration = 4000) {
    const stack = $('#toast-stack');
    if (!stack) return;
    const el = document.createElement('div');
    el.className = 'toast toast--' + variant;
    el.setAttribute('role', variant === 'err' ? 'alert' : 'status');
    el.textContent = message;
    stack.appendChild(el);
    setTimeout(() => {
        el.style.transition = 'opacity 0.2s';
        el.style.opacity = '0';
        setTimeout(() => el.remove(), 220);
    }, duration);
}

/* -------- Thème -------- */
const THEME_KEY = 'arhiane.theme';
const DEFAULT_ACCENT = '#6B4AAF';

function systemPrefersDark() {
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
}

function applyTheme(theme) {
    const effective = theme === 'auto' ? (systemPrefersDark() ? 'dark' : 'light') : theme;
    document.documentElement.setAttribute('data-theme', effective);
}

function applyAccent(hex) {
    if (!/^#[0-9a-fA-F]{6}$/.test(hex)) return;
    document.documentElement.style.setProperty('--accent', hex.toUpperCase());
}

async function loadAndApplyTheme(api) {
    let theme = 'auto';
    let accent = DEFAULT_ACCENT;
    try {
        const s = await api.settings();
        theme = s.theme || 'auto';
        accent = s.couleur_primaire || DEFAULT_ACCENT;
    } catch (_) { /* fallback */ }
    applyTheme(theme);
    applyAccent(accent);
    return theme;
}

/* -------- Focus trap pour modales -------- */
const FOCUSABLE = 'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';
let _focusReturnStack = [];

function trapFocus(modal) {
    const focusables = $$(FOCUSABLE, modal).filter(el => !el.hasAttribute('disabled'));
    if (!focusables.length) return () => {};
    const first = focusables[0];
    const last = focusables[focusables.length - 1];

    function handler(ev) {
        if (ev.key === 'Tab') {
            if (ev.shiftKey && document.activeElement === first) {
                ev.preventDefault(); last.focus();
            } else if (!ev.shiftKey && document.activeElement === last) {
                ev.preventDefault(); first.focus();
            }
        } else if (ev.key === 'Escape') {
            closeModal(modal.id);
        }
    }
    modal.addEventListener('keydown', handler);
    first.focus();
    return () => modal.removeEventListener('keydown', handler);
}

function openModal(id) {
    const m = document.getElementById(id);
    if (!m) return;
    _focusReturnStack.push(document.activeElement);
    m.hidden = false;
    m._trapOff = trapFocus(m);
}
function closeModal(id) {
    const m = document.getElementById(id);
    if (!m) return;
    m.hidden = true;
    if (m._trapOff) { m._trapOff(); m._trapOff = null; }
    const prev = _focusReturnStack.pop();
    if (prev && prev.focus) prev.focus();
}

document.addEventListener('click', (ev) => {
    const t = ev.target;
    if (t instanceof HTMLElement && t.matches('[data-close-modal]')) {
        const modal = t.closest('.modal');
        if (modal) closeModal(modal.id);
    }
});

/* -------- Dashboard : rendu des modules par section -------- */

const SECTIONS = [
    {
        id: 'recrutement_onboarding',
        label: 'Recrutement & Onboarding',
        description: 'Acquisition de talents et intégration des nouveaux arrivants.',
    },
    {
        id: 'administration_documents',
        label: 'Gestion administrative & documents',
        description: 'Production de documents contractuels ou officiels.',
    },
    {
        id: 'juridique_conformite',
        label: 'Juridique & conformité',
        description: 'Sécurisation des processus vis-à-vis de la loi suisse et des CCT.',
    },
    {
        id: 'communication_rh',
        label: 'Communication & développement RH',
        description: 'Gestion quotidienne, traduction et relations humaines.',
    },
];

async function renderModules(api) {
    const container = document.getElementById('modules-grid');
    const modules = await api.list_modules();
    if (!Array.isArray(modules) || modules.length === 0) {
        container.innerHTML = '<div class="loading-placeholder">Aucun module n\'est disponible pour le moment.</div>';
        return;
    }
    container.innerHTML = '';

    // Groupement par section, dans l'ordre défini par SECTIONS.
    const bySection = new Map(SECTIONS.map(s => [s.id, []]));
    const orphans = [];
    for (const m of modules) {
        if (bySection.has(m.categorie)) bySection.get(m.categorie).push(m);
        else orphans.push(m);
    }

    for (const section of SECTIONS) {
        const items = bySection.get(section.id) || [];
        if (!items.length) continue;
        const block = document.createElement('section');
        block.className = 'modules-section';
        block.innerHTML = `
            <header class="modules-section__head">
                <h2>${escapeHTML(section.label)}</h2>
                <p>${escapeHTML(section.description)}</p>
            </header>
            <div class="modules-section__grid"></div>
        `;
        const grid = block.querySelector('.modules-section__grid');
        for (const m of items) grid.appendChild(renderModuleCard(m));
        container.appendChild(block);
    }
    if (orphans.length) {
        const block = document.createElement('section');
        block.className = 'modules-section';
        block.innerHTML = `<header class="modules-section__head"><h2>Autres</h2></header><div class="modules-section__grid"></div>`;
        const grid = block.querySelector('.modules-section__grid');
        for (const m of orphans) grid.appendChild(renderModuleCard(m));
        container.appendChild(block);
    }
}

function renderModuleCard(m) {
    const coming = m.statut === 'a_venir';
    const card = document.createElement('button');
    card.type = 'button';
    card.className = 'module-card' + (coming ? ' module-card--coming' : '');
    card.dataset.moduleId = m.id;
    card.setAttribute('aria-label', `${m.nom} — ${coming ? 'à venir' : 'disponible'}`);
    card.innerHTML = `
        <span class="module-card__badge ${coming ? 'module-card__badge--coming' : 'module-card__badge--available'}">
            ${coming ? 'À venir' : 'Disponible'}
        </span>
        <div class="module-card__icon" aria-hidden="true">${iconHTML(m.icone)}</div>
        <h3 class="module-card__title">${escapeHTML(m.nom)}</h3>
        <p class="module-card__desc">${escapeHTML(m.description || '')}</p>
    `;
    card.addEventListener('click', () => openModule(m));
    return card;
}

function openModule(m) {
    if (m.statut === 'a_venir') {
        document.getElementById('preview-icon').innerHTML = iconHTML(m.icone);
        document.getElementById('preview-title').textContent = m.nom;
        document.getElementById('preview-desc').textContent = m.description || '';
        openModal('modal-module-preview');
        return;
    }
    if (m.id === 'certificats') {
        openCertificats();
        return;
    }
    toast(`Le module « ${m.nom} » s'ouvrira ici dans une prochaine phase.`, 'info');
}

/* ============================================================
   Module Certificats — wizard multi-étapes
   ============================================================ */

const CERT = {
    api: null,
    description: null,       // { id, nom, steps: [...] }
    dossier: null,           // résumé du dossier courant
    state: null,             // wizard_state
    currentStepId: null,
};

function showView(viewId) {
    ['view-dashboard', 'view-certificats', 'view-wizard'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.hidden = (id !== viewId);
    });
}

async function openCertificats() {
    const api = CERT.api || (CERT.api = await whenApiReady());
    showView('view-certificats');
    if (!CERT.description) {
        const desc = await api.wizard_describe('certificats');
        if (desc && desc.erreur) { toast(desc.erreur, 'err'); return; }
        CERT.description = desc;
        document.getElementById('cert-title').textContent = desc.nom || 'Certificats';
        document.getElementById('cert-subtitle').textContent = desc.description || '';
    }
    await renderDossierList();
    // Pas de dossier actif → placeholder visible
    document.getElementById('cert-wizard').hidden = true;
    document.getElementById('cert-empty').hidden = false;
}

async function renderDossierList() {
    const api = CERT.api;
    const list = await api.wizard_list_dossiers();
    const ul = document.getElementById('cert-dossier-list');
    ul.innerHTML = '';
    if (!Array.isArray(list) || list.length === 0) {
        const li = document.createElement('li');
        li.className = 'cert-empty';
        li.textContent = 'Aucun dossier. Cliquez « + Nouveau » pour commencer.';
        ul.appendChild(li);
        return;
    }
    for (const d of list) {
        const li = document.createElement('li');
        li.className = 'cert-dossier-item';
        if (CERT.dossier && CERT.dossier.id === d.id) li.classList.add('active');
        li.innerHTML = `
            <div class="cert-dossier-name">${escapeHTML(d.collaborateur || d.id)}</div>
            <div class="cert-dossier-meta">
                <span>${escapeHTML(d.type_document || '—')}</span>
                <span>·</span>
                <span>${escapeHTML((d.langue || 'fr').toUpperCase())}</span>
                <span>·</span>
                <span>étape : ${escapeHTML(d.wizard_step || '—')}</span>
            </div>
        `;
        li.addEventListener('click', () => openDossier(d.id));
        ul.appendChild(li);
    }
}

async function openDossier(dossierId) {
    const api = CERT.api;
    const res = await api.wizard_get_state(dossierId);
    if (res && res.erreur) { toast(res.erreur, 'err'); return; }
    CERT.dossier = res.dossier;
    CERT.state = res.state;
    CERT.currentStepId = res.current_step || (CERT.description.steps[0] && CERT.description.steps[0].id);
    document.getElementById('cert-empty').hidden = true;
    document.getElementById('cert-wizard').hidden = false;
    renderStepper();
    renderStepForm();
    await refreshManagers();
    await refreshDocuments();
    await refreshPreview();
    await renderDossierList();
}

/* -------- Managers & questionnaires (§15) -------- */

async function refreshManagers() {
    if (!CERT.dossier) return;
    const api = CERT.api;
    const res = await api.managers_list(CERT.dossier.id);
    const list = document.getElementById('cert-mgr-list');
    list.innerHTML = '';
    if (res && res.erreur) {
        list.innerHTML = `<li class="cert-empty">${escapeHTML(res.erreur)}</li>`;
        return;
    }
    const items = res.items || [];
    if (!items.length) {
        list.innerHTML = '<li class="cert-empty">Aucun manager enregistré. Si vous préférez la « saisie RH » directe, vous pouvez sauter cette étape.</li>';
        return;
    }
    for (const m of items) {
        const li = document.createElement('li');
        li.className = 'cert-mgr-item';
        const periode = (m.periode_debut || '—') + ' → ' + (m.periode_fin || 'en cours');
        const statusLabel = m.questionnaire_present
            ? (m.reponses_detectees && m.reponses_detectees.length
                ? `${m.reponses_detectees.length} réponse(s) reçue(s)`
                : 'Questionnaire généré — en attente de retour')
            : 'Questionnaire non généré';
        const statusClass = m.questionnaire_present
            ? (m.reponses_detectees && m.reponses_detectees.length ? 'ok' : 'pending')
            : 'muted';
        li.innerHTML = `
            <div class="cert-mgr-main">
                <div class="cert-mgr-name">${escapeHTML(m.nom)}</div>
                <div class="cert-mgr-meta">
                    <span>${escapeHTML(m.fonction || '—')}</span>
                    <span>·</span>
                    <span>${escapeHTML(periode)}</span>
                </div>
                <div class="cert-mgr-status cert-mgr-status--${statusClass}">${escapeHTML(statusLabel)}</div>
            </div>
            <div class="cert-mgr-actions">
                <button class="btn-ghost-line" type="button" data-act="gen" data-id="${escapeHTML(m.id)}">
                    ${m.questionnaire_present ? 'Régénérer' : 'Générer PDF'}
                </button>
                <button class="btn-ghost-line cert-doc-remove" type="button" data-act="rm" data-id="${escapeHTML(m.id)}">Supprimer</button>
            </div>
        `;
        list.appendChild(li);
    }
    list.querySelectorAll('button[data-act="gen"]').forEach(btn => {
        btn.addEventListener('click', () => generateQuestionnaire(btn.dataset.id));
    });
    list.querySelectorAll('button[data-act="rm"]').forEach(btn => {
        btn.addEventListener('click', () => removeManager(btn.dataset.id));
    });
}

async function addManager(ev) {
    ev.preventDefault();
    const api = CERT.api;
    const form = document.getElementById('form-new-manager');
    const data = Object.fromEntries(new FormData(form).entries());
    const res = await api.managers_add(CERT.dossier.id, data);
    if (res && res.erreur) { toast(res.erreur, 'err'); return; }
    closeModal('modal-new-manager');
    form.reset();
    toast('Manager ajouté.', 'ok', 2000);
    await refreshManagers();
}

async function generateQuestionnaire(managerId) {
    const api = CERT.api;
    toast('Génération du PDF en cours…', 'info', 2000);
    const res = await api.managers_generate_questionnaire(CERT.dossier.id, managerId);
    if (res && res.erreur) { toast(res.erreur, 'err', 6000); return; }
    toast(`Questionnaire généré : ${res.fichier}`, 'ok', 4000);
    await refreshManagers();
}

async function removeManager(managerId) {
    const api = CERT.api;
    if (!confirm('Retirer ce manager du dossier ? Les fichiers PDF existants ne sont pas supprimés.')) return;
    const res = await api.managers_remove(CERT.dossier.id, managerId);
    if (res && res.erreur) { toast(res.erreur, 'err'); return; }
    toast('Manager retiré.', 'ok', 2000);
    await refreshManagers();
}

async function openQuestionnairesFolder() {
    const api = CERT.api;
    const res = await api.managers_open_questionnaire_folder(CERT.dossier.id);
    if (res && res.erreur) toast(res.erreur, 'err');
}

/* -------- Documents sources (archivage §15.1) -------- */

function formatSize(bytes) {
    if (!bytes && bytes !== 0) return '';
    if (bytes < 1024) return bytes + ' o';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' Ko';
    return (bytes / 1024 / 1024).toFixed(1) + ' Mo';
}

async function refreshDocuments() {
    if (!CERT.dossier) return;
    const api = CERT.api;
    const res = await api.documents_list(CERT.dossier.id);
    const list = document.getElementById('cert-docs-list');
    list.innerHTML = '';
    if (res && res.erreur) {
        list.innerHTML = `<li class="cert-empty">${escapeHTML(res.erreur)}</li>`;
        return;
    }
    const items = res.items || [];
    if (!items.length) {
        list.innerHTML = '<li class="cert-empty">Aucun document archivé. Cliquez « + Ajouter » ou glissez-déposez via l\'Explorateur.</li>';
        return;
    }
    for (const it of items) {
        const li = document.createElement('li');
        li.className = 'cert-doc-item';
        li.innerHTML = `
            <div class="cert-doc-main">
                <span class="cert-doc-ext">${escapeHTML(it.extension || '?')}</span>
                <span class="cert-doc-name">${escapeHTML(it.nom)}</span>
            </div>
            <div class="cert-doc-meta">
                <span>${escapeHTML(formatSize(it.taille))}</span>
                <span>·</span>
                <span>${escapeHTML(it.modifie_le || '')}</span>
                <button class="btn-ghost-line cert-doc-remove" type="button" data-filename="${escapeHTML(it.nom)}" aria-label="Supprimer ${escapeHTML(it.nom)}">Supprimer</button>
            </div>
        `;
        list.appendChild(li);
    }
    // Bindings
    list.querySelectorAll('.cert-doc-remove').forEach(btn => {
        btn.addEventListener('click', () => removeDocument(btn.dataset.filename));
    });
}

async function addDocuments() {
    const api = CERT.api;
    const res = await api.documents_pick_and_attach(CERT.dossier.id);
    if (res && res.erreur) { toast(res.erreur, 'err'); return; }
    if (res.ajoutes > 0) {
        toast(`${res.ajoutes} document(s) archivé(s).`, 'ok', 2500);
    }
    if (res.erreurs && res.erreurs.length) {
        for (const e of res.erreurs) toast(e, 'warn', 5000);
    }
    await refreshDocuments();
}

async function removeDocument(filename) {
    const api = CERT.api;
    if (!confirm(`Déplacer « ${filename} » vers la corbeille du dossier ?`)) return;
    const res = await api.documents_remove(CERT.dossier.id, filename);
    if (res && res.erreur) { toast(res.erreur, 'err'); return; }
    toast('Document déplacé vers la corbeille du dossier.', 'ok', 2500);
    await refreshDocuments();
}

async function openDocumentsFolder() {
    const api = CERT.api;
    const res = await api.documents_open_folder(CERT.dossier.id);
    if (res && res.erreur) toast(res.erreur, 'err');
}

function renderStepper() {
    const nav = document.getElementById('cert-stepper');
    nav.innerHTML = '';
    CERT.description.steps.forEach((s, idx) => {
        const b = document.createElement('button');
        b.type = 'button';
        b.className = 'cert-step-tab';
        if (s.id === CERT.currentStepId) b.classList.add('active');
        if (CERT.state.completed && CERT.state.completed.includes(s.id)) b.classList.add('done');
        b.textContent = `${idx + 1}. ${s.label}`;
        b.addEventListener('click', () => {
            CERT.currentStepId = s.id;
            renderStepper();
            renderStepForm();
        });
        nav.appendChild(b);
    });
}

function renderStepForm() {
    const step = CERT.description.steps.find(s => s.id === CERT.currentStepId);
    if (!step) return;
    document.getElementById('cert-step-label').textContent = step.label;
    document.getElementById('cert-step-desc').textContent = step.description || '';
    const form = document.getElementById('cert-step-form');
    form.innerHTML = '';

    const current = (CERT.state.answers && CERT.state.answers[step.id]) || {};
    for (const f of step.inputs) {
        form.appendChild(renderField(f, current[f.id]));
    }
    document.getElementById('cert-errors').hidden = true;
}

function renderField(f, value) {
    const label = document.createElement('label');
    label.className = 'field' + (f.type === 'textarea' ? ' field--full' : '');
    const span = document.createElement('span');
    span.textContent = f.label + (f.required ? ' *' : '');
    label.appendChild(span);

    let input;
    if (f.type === 'textarea') {
        input = document.createElement('textarea');
        input.rows = 4;
        input.value = value || '';
    } else if (f.type === 'select') {
        input = document.createElement('select');
        for (const opt of (f.options || [])) {
            const o = document.createElement('option');
            o.value = opt.value;
            o.textContent = opt.label;
            input.appendChild(o);
        }
        input.value = value !== undefined ? String(value) : (f.options && f.options[0] ? f.options[0].value : '');
    } else if (f.type === 'checkbox') {
        input = document.createElement('input');
        input.type = 'checkbox';
        input.checked = !!value;
        label.classList.add('field--checkbox');
    } else {
        input = document.createElement('input');
        input.type = 'text';
        input.value = value !== undefined && value !== null ? String(value) : '';
    }
    input.name = f.id;
    input.id = 'cert-field-' + f.id;
    if (f.required && f.type !== 'checkbox') input.required = true;
    if (f.type === 'checkbox') {
        // checkbox goes on the left of label text
        label.innerHTML = '';
        label.appendChild(input);
        const sp = document.createElement('span');
        sp.textContent = ' ' + f.label + (f.required ? ' *' : '');
        label.appendChild(sp);
    } else {
        label.appendChild(input);
    }
    if (f.aide) {
        const help = document.createElement('small');
        help.className = 'field-help';
        help.textContent = f.aide;
        label.appendChild(help);
    }
    return label;
}

function collectStepAnswers() {
    const step = CERT.description.steps.find(s => s.id === CERT.currentStepId);
    const out = {};
    for (const f of step.inputs) {
        const el = document.getElementById('cert-field-' + f.id);
        if (!el) continue;
        if (f.type === 'checkbox') out[f.id] = !!el.checked;
        else out[f.id] = el.value;
    }
    return out;
}

async function saveAndAdvance() {
    const api = CERT.api;
    const answers = collectStepAnswers();
    const res = await api.wizard_save_step(CERT.dossier.id, CERT.currentStepId, answers);
    if (res.erreurs && res.erreurs.length) {
        const box = document.getElementById('cert-errors');
        box.hidden = false;
        box.innerHTML = '<strong>Veuillez corriger :</strong><ul>' +
            res.erreurs.map(e => `<li>${escapeHTML(e)}</li>`).join('') + '</ul>';
        return;
    }
    if (res.erreur) { toast(res.erreur, 'err'); return; }
    CERT.state = res.state;
    if (res.current_step) CERT.currentStepId = res.current_step;
    renderStepper();
    renderStepForm();
    await refreshPreview();
    await renderDossierList();
    toast('Étape enregistrée.', 'ok', 1600);
}

function goPrev() {
    const idx = CERT.description.steps.findIndex(s => s.id === CERT.currentStepId);
    if (idx > 0) {
        CERT.currentStepId = CERT.description.steps[idx - 1].id;
        renderStepper();
        renderStepForm();
    }
}

async function refreshPreview() {
    if (!CERT.dossier) return;
    const api = CERT.api;
    const res = await api.wizard_preview(CERT.dossier.id);
    const body = document.getElementById('cert-preview-body');
    const alertsEl = document.getElementById('cert-alerts');
    if (res && res.erreur) {
        body.textContent = '(aperçu indisponible)';
        alertsEl.innerHTML = `<div class="cert-alert err">${escapeHTML(res.erreur)}</div>`;
        return;
    }
    body.textContent = res.texte || '(brouillon vide — complétez les étapes)';
    alertsEl.innerHTML = '';
    for (const a of (res.alertes || [])) {
        const div = document.createElement('div');
        div.className = 'cert-alert cert-alert--' + (a.severite || 'alerte');
        div.innerHTML = `<strong>${escapeHTML(a.severite || '')} — ${escapeHTML(a.code || '')}</strong>
            <div>${escapeHTML(a.message || '')}</div>
            ${a.suggestion ? `<div class="cert-alert-suggestion">${escapeHTML(a.suggestion)}</div>` : ''}`;
        alertsEl.appendChild(div);
    }
}

async function finalizeCert() {
    const api = CERT.api;
    const force = document.getElementById('cert-force').checked;
    const res = await api.wizard_finalize(CERT.dossier.id, force);
    if (res && res.erreur) { toast(res.erreur, 'err', 6000); return; }
    if (!res.scelle) {
        toast(res.raison || 'Alertes bloquantes — cochez « Forcer » si vous souhaitez quand même sceller.', 'warn', 6000);
        await refreshPreview();
        return;
    }
    toast(`Certificat scellé (${res.audit}). Fichier : ${res.fichier.split(/[\\/]/).pop()}`, 'ok', 6000);
    await refreshPreview();
}

async function createDossier(ev) {
    ev.preventDefault();
    const api = CERT.api;
    const form = document.getElementById('form-new-dossier');
    const data = Object.fromEntries(new FormData(form).entries());
    const res = await api.wizard_create_dossier('certificats', data);
    if (res && res.erreur) { toast(res.erreur, 'err'); return; }
    closeModal('modal-new-dossier');
    form.reset();
    toast('Dossier créé.', 'ok', 2000);
    await renderDossierList();
    await openDossier(res.dossier.id);
}

function bindCertificats() {
    document.getElementById('cert-back').addEventListener('click', () => showView('view-dashboard'));
    document.getElementById('cert-new').addEventListener('click', () => openModal('modal-new-dossier'));
    document.getElementById('form-new-dossier').addEventListener('submit', createDossier);
    document.getElementById('cert-save-next').addEventListener('click', saveAndAdvance);
    document.getElementById('cert-prev').addEventListener('click', goPrev);
    document.getElementById('cert-refresh-preview').addEventListener('click', refreshPreview);
    document.getElementById('cert-finalize').addEventListener('click', finalizeCert);
    document.getElementById('cert-docs-add').addEventListener('click', addDocuments);
    document.getElementById('cert-docs-open').addEventListener('click', openDocumentsFolder);
    document.getElementById('cert-mgr-add').addEventListener('click', () => openModal('modal-new-manager'));
    document.getElementById('cert-mgr-open').addEventListener('click', openQuestionnairesFolder);
    document.getElementById('form-new-manager').addEventListener('submit', addManager);
}

/* -------- Barre de statut -------- */
async function refreshStatus(api) {
    let status;
    try {
        status = await api.status();
    } catch (_) { return; }

    const llmEl = document.getElementById('status-llm');
    const dot = llmEl.querySelector('.status-dot');
    const label = llmEl.querySelector('.status-value');
    dot.className = 'status-dot';
    llmEl.classList.remove('clickable');
    llmEl.onclick = null;

    switch (status.llm.status) {
        case 'ready':
            dot.classList.add('status-dot--ok');
            label.textContent = status.llm.active_model
                ? `Prête (${status.llm.active_model})` : 'Prête';
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

    const baseEl = document.getElementById('status-base');
    const baseDot = baseEl.querySelector('.status-dot');
    const baseVal = baseEl.querySelector('.status-value');
    baseDot.className = 'status-dot status-dot--warn';
    baseVal.textContent = 'à indexer';

    return status;
}

/* -------- Sélecteur d'entité (accessible clavier) -------- */
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
    trigger.disabled = false;

    const activeEnt = entities.find(e => e.id === activeId) || entities[0];
    current.textContent = activeEnt.nom;

    menu.innerHTML = '';
    entities.forEach((e, idx) => {
        const li = document.createElement('li');
        li.textContent = e.nom;
        li.setAttribute('role', 'option');
        li.id = `entity-opt-${idx}`;
        if (e.id === activeEnt.id) {
            li.classList.add('active');
            li.setAttribute('aria-selected', 'true');
        }
        li.tabIndex = -1;
        li.addEventListener('click', async () => {
            await api.set_active_entity(e.id);
            current.textContent = e.nom;
            closeMenu();
            $$('li', menu).forEach(c => {
                const sel = c.textContent === e.nom;
                c.classList.toggle('active', sel);
                c.setAttribute('aria-selected', sel ? 'true' : 'false');
            });
            toast(`Entité active : ${e.nom}`, 'ok', 2500);
        });
        menu.appendChild(li);
    });

    function openMenu() {
        menu.hidden = false;
        trigger.setAttribute('aria-expanded', 'true');
        const firstActive = menu.querySelector('li.active') || menu.firstElementChild;
        firstActive && firstActive.focus();
    }
    function closeMenu() {
        menu.hidden = true;
        trigger.setAttribute('aria-expanded', 'false');
    }

    trigger.addEventListener('click', (ev) => {
        ev.stopPropagation();
        menu.hidden ? openMenu() : closeMenu();
    });
    trigger.addEventListener('keydown', (ev) => {
        if (ev.key === 'ArrowDown' || ev.key === 'Enter' || ev.key === ' ') {
            ev.preventDefault();
            openMenu();
        }
    });
    menu.addEventListener('keydown', (ev) => {
        const items = $$('li', menu);
        const idx = items.indexOf(document.activeElement);
        if (ev.key === 'ArrowDown') { ev.preventDefault(); items[(idx + 1) % items.length].focus(); }
        else if (ev.key === 'ArrowUp') { ev.preventDefault(); items[(idx - 1 + items.length) % items.length].focus(); }
        else if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); document.activeElement.click(); }
        else if (ev.key === 'Escape') { closeMenu(); trigger.focus(); }
    });
    document.addEventListener('click', () => closeMenu());
}

/* -------- Wizard première entité -------- */
async function maybeShowWizard(api) {
    const entities = await api.list_entities();
    const needsWizard = entities.length === 0;
    document.getElementById('view-wizard').hidden = !needsWizard;
    document.getElementById('view-dashboard').hidden = needsWizard;
    document.getElementById('entity-selector-wrap').style.visibility = needsWizard ? 'hidden' : 'visible';
    if (!needsWizard) return;

    const form = document.getElementById('form-entity');
    if (form._bound) return;
    form._bound = true;

    form.addEventListener('submit', async (ev) => {
        ev.preventDefault();
        const btn = form.querySelector('button[type="submit"]');
        btn.disabled = true;
        const data = Object.fromEntries(new FormData(form).entries());
        const res = await api.create_entity(data);
        btn.disabled = false;
        if (res && res.erreur) {
            toast(res.erreur, 'err', 5000);
            return;
        }
        toast(`Entité « ${res.entite.nom} » créée.`, 'ok');
        document.getElementById('view-wizard').hidden = true;
        document.getElementById('view-dashboard').hidden = false;
        document.getElementById('entity-selector-wrap').style.visibility = 'visible';
        await renderEntitySelector(api);
    });
}

/* -------- Paramètres -------- */
async function bindSettings(api) {
    const modal = document.getElementById('modal-settings');
    const themeSel = document.getElementById('setting-theme');
    const auditChk = document.getElementById('setting-audit-full');
    const colorInput = document.getElementById('setting-color');
    const colorHex = document.getElementById('setting-color-hex');
    const colorReset = document.getElementById('setting-color-reset');

    document.getElementById('btn-settings').addEventListener('click', async () => {
        const s = await api.settings();
        themeSel.value = s.theme || 'auto';
        auditChk.checked = !!s.audit_log_prompts;
        colorInput.value = s.couleur_primaire || DEFAULT_ACCENT;
        colorHex.textContent = colorInput.value.toUpperCase();
        openModal('modal-settings');
        await renderEntityAssets(api);
    });

    themeSel.addEventListener('change', async () => {
        const updated = await api.update_settings({ theme: themeSel.value });
        applyTheme(updated.theme);
    });
    auditChk.addEventListener('change', async () => {
        await api.update_settings({ audit_log_prompts: auditChk.checked });
        toast(auditChk.checked
            ? 'Contenu complet des prompts désormais journalisé.'
            : 'Journal d\'audit limité aux empreintes (recommandé).',
            'warn', 5000);
    });
    colorInput.addEventListener('input', () => {
        colorHex.textContent = colorInput.value.toUpperCase();
        applyAccent(colorInput.value);  // preview live
    });
    colorInput.addEventListener('change', async () => {
        const updated = await api.update_settings({ couleur_primaire: colorInput.value });
        applyAccent(updated.couleur_primaire);
        toast('Couleur enregistrée.', 'ok', 1800);
    });
    colorReset.addEventListener('click', async () => {
        colorInput.value = DEFAULT_ACCENT;
        colorHex.textContent = DEFAULT_ACCENT;
        const updated = await api.update_settings({ couleur_primaire: DEFAULT_ACCENT });
        applyAccent(updated.couleur_primaire);
    });

    $$('[data-open-folder]', modal).forEach(btn => {
        btn.addEventListener('click', async () => {
            const ok = await api.open_folder(btn.dataset.openFolder);
            if (!ok) toast('Impossible d\'ouvrir ce dossier.', 'err');
        });
    });

    document.getElementById('form-edit-entity').addEventListener('submit', (ev) => submitEditEntity(ev, api));
}

/* -------- Assets par entité (logo / signature) -------- */

async function renderEntityAssets(api) {
    const list = document.getElementById('entity-asset-list');
    const entities = await api.list_entities();
    list.innerHTML = '';
    if (!entities.length) {
        list.innerHTML = '<li class="cert-empty">Aucune entité.</li>';
        return;
    }
    for (const ent of entities) {
        const li = document.createElement('li');
        li.className = 'entity-asset-item';
        li.innerHTML = `
            <div class="entity-asset-header">
                <div class="entity-asset-name">${escapeHTML(ent.nom)}</div>
                <button class="btn-ghost-line" data-ent="${escapeHTML(ent.id)}" data-act="edit" type="button">Modifier</button>
            </div>
            <div class="entity-asset-row">
                <span class="entity-asset-label">Logo</span>
                <span class="entity-asset-status ${ent.logo_present ? 'ok' : 'muted'}">
                    ${ent.logo_present ? 'Présent' : 'Absent'}
                </span>
                <button class="btn-ghost-line" data-ent="${escapeHTML(ent.id)}" data-kind="logo" data-act="set" type="button">Téléverser</button>
                ${ent.logo_present ? `<button class="btn-ghost-line" data-ent="${escapeHTML(ent.id)}" data-kind="logo" data-act="rm" type="button">Retirer</button>` : ''}
            </div>
            <div class="entity-asset-row">
                <span class="entity-asset-label">Signature</span>
                <span class="entity-asset-status ${ent.signature_presente ? 'ok' : 'muted'}">
                    ${ent.signature_presente ? 'Présente' : 'Absente'}
                </span>
                <button class="btn-ghost-line" data-ent="${escapeHTML(ent.id)}" data-kind="signature" data-act="set" type="button">Téléverser</button>
                ${ent.signature_presente ? `<button class="btn-ghost-line" data-ent="${escapeHTML(ent.id)}" data-kind="signature" data-act="rm" type="button">Retirer</button>` : ''}
            </div>
        `;
        list.appendChild(li);
    }
    list.querySelectorAll('button[data-act]').forEach(btn => {
        btn.addEventListener('click', async () => {
            const { ent, kind, act } = btn.dataset;
            if (act === 'edit') {
                await openEditEntityModal(api, ent);
                return;
            }
            let res;
            if (act === 'set') {
                res = await api.entity_pick_and_set_asset(ent, kind);
                if (res && res.annule) return;
            } else {
                if (!confirm(`Retirer le ${kind} de cette entité ?`)) return;
                res = await api.entity_remove_asset(ent, kind);
            }
            if (res && res.erreur) { toast(res.erreur, 'err', 5000); return; }
            toast(act === 'set' ? `${kind === 'logo' ? 'Logo' : 'Signature'} téléversé.` : `${kind === 'logo' ? 'Logo' : 'Signature'} retiré.`, 'ok', 2000);
            await renderEntityAssets(api);
        });
    });
}

async function openEditEntityModal(api, entityId) {
    if (typeof api.get_entity !== 'function') {
        toast("La fonction d'édition n'est pas disponible — fermez puis relancez l'application.",
              'err', 7000);
        return;
    }
    let data;
    try {
        data = await api.get_entity(entityId);
    } catch (err) {
        toast("Erreur lors du chargement de l'entité : " + (err && err.message ? err.message : err),
              'err', 6000);
        return;
    }
    if (data && data.erreur) { toast(data.erreur, 'err'); return; }
    const form = document.getElementById('form-edit-entity');
    form.reset();
    form.elements.entity_id.value = data.id;
    ['nom', 'forme_juridique', 'adresse', 'telephone', 'email',
     'signataire_nom', 'signataire_fonction'].forEach(k => {
        if (form.elements[k]) form.elements[k].value = data[k] || '';
    });
    openModal('modal-edit-entity');
}

async function submitEditEntity(ev, api) {
    ev.preventDefault();
    const form = document.getElementById('form-edit-entity');
    const payload = Object.fromEntries(new FormData(form).entries());
    const eid = payload.entity_id;
    delete payload.entity_id;
    const res = await api.update_entity(eid, payload);
    if (res && res.erreur) { toast(res.erreur, 'err', 5000); return; }
    closeModal('modal-edit-entity');
    toast('Entité enregistrée.', 'ok', 2000);
    await renderEntityAssets(api);
    // Rafraîchit le sélecteur d'entité en en-tête (le nom peut avoir changé).
    await renderEntitySelector(api);
}

/* -------- Cycle rapide thème depuis le header -------- */
async function bindThemeToggle(api) {
    document.getElementById('btn-theme').addEventListener('click', async () => {
        const cur = await api.settings();
        const order = ['auto', 'light', 'dark'];
        const next = order[(order.indexOf(cur.theme || 'auto') + 1) % order.length];
        const updated = await api.update_settings({ theme: next });
        applyTheme(updated.theme);
        const labels = { auto: 'Automatique', light: 'Clair', dark: 'Sombre' };
        toast(`Thème : ${labels[updated.theme]}`, 'info', 1800);
    });
}

/* -------- Streaming : API Python → handlers globaux -------- */
window._streams = new Map();

window.onStreamChunk = function (id, text) {
    const h = window._streams.get(id);
    if (h && h.onChunk) h.onChunk(text);
};
window.onStreamDone = function (id, result) {
    const h = window._streams.get(id);
    if (h && h.onDone) h.onDone(result);
    window._streams.delete(id);
};
window.onStreamError = function (id, message) {
    const h = window._streams.get(id);
    if (h && h.onError) h.onError(message);
    window._streams.delete(id);
};

/** Démarre une génération streamée. Usage :
 *   await startStream(api, 'certificats', inputs, {
 *     onChunk: (t) => ...,
 *     onDone: (result) => ...,
 *     onError: (msg) => ...,
 *   });
 */
window.startStream = async function (api, moduleId, inputs, handlers) {
    const res = await api.start_stream(moduleId, inputs);
    if (res.erreur) throw new Error(res.erreur);
    window._streams.set(res.stream_id, handlers);
    return res.stream_id;
};

window.cancelStream = function (api, streamId) {
    return api.cancel_stream(streamId);
};

/* -------- Bootstrap -------- */
(async () => {
    const api = await whenApiReady();
    await loadAndApplyTheme(api);

    // Re-applique le thème si l'utilisateur en "auto" change de préférence système.
    if (window.matchMedia) {
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', async () => {
            const s = await api.settings();
            if (s.theme === 'auto') applyTheme('auto');
        });
    }

    await maybeShowWizard(api);
    await Promise.all([
        renderEntitySelector(api),
        renderModules(api),
        refreshStatus(api),
    ]);

    document.getElementById('btn-retry-llm').addEventListener('click', async () => {
        closeModal('modal-llm-help');
        await refreshStatus(api);
    });

    await bindSettings(api);
    await bindThemeToggle(api);
    CERT.api = api;
    bindCertificats();

    setInterval(() => refreshStatus(api), 10000);
})();
