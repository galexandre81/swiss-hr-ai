# ARHIANE — L'IA qui remet les RH au centre — Architecture globale

**Version :** 1.0 — 21 avril 2026
**Objet :** Proposition d'infrastructure avant développement des modules métier
**Référence :** Cahier des Charges v1.2 (avril 2026)

---

## 1. Décision structurante : LM Studio plutôt qu'un wrapper llama.cpp

Le cahier des charges mentionne un wrapper Python autour de llama.cpp. Nous retenons **LM Studio** car :

- LM Studio est déjà un wrapper graphique autour de llama.cpp
- Il expose une **API locale compatible OpenAI** sur `http://localhost:1234/v1`
- Notre application devient un simple client HTTP — zéro complexité d'embedding du moteur d'inférence
- Installation LM Studio = `.exe` officiel, rassurant pour le DSI du client
- Chargement modèle + démarrage serveur = quelques clics dans l'interface

### Points d'attention

- **Modèle :** "Qwen 3.5 9B" n'existe pas à ce jour. Tailles disponibles : Qwen 2.5 (7B/14B), Qwen 3 (8B/14B/32B). Cible recommandée : **Qwen 3 8B Instruct GGUF Q4_K_M**.
- **Démarrage automatique :** LM Studio ne se lance pas en service Windows silencieux. Pour une v2, envisager **Ollama** (service Windows natif).

---

## 2. Structure de dossiers

Principe : séparer strictement le code (caché à l'utilisateur) des données éditables (visibles, modifiables sans compétence informatique).

```
ARHIANE_Toolbox/
├── ARHIANE.exe                    ← double-clic pour lancer
├── README_UTILISATEUR.pdf         ← guide illustré pas-à-pas
│
├── _app/                          ← code compilé — l'utilisateur n'y touche jamais
│   ├── core/                      ← briques partagées
│   │   ├── llm_client.py
│   │   ├── rag_engine.py
│   │   ├── doc_engine.py
│   │   ├── entity_manager.py
│   │   ├── config.py
│   │   ├── logger.py
│   │   └── prompts/
│   ├── modules/                   ← un dossier par outil RH
│   └── ui/                        ← dashboard + vues modules
│
├── Base_Juridique/                ← PDFs CO, LTr, CCT (éditable utilisateur)
├── Templates/                     ← modèles Word (éditable utilisateur)
├── Entities/                      ← multi-sociétés (éditable utilisateur)
│   └── Entite_A/
│       ├── logo.png
│       ├── signature.png
│       └── config.json
├── Outputs/                       ← documents générés horodatés
├── Logs/                          ← journal auditable LPD
├── data/                          ← index vectoriel ChromaDB (régénérable)
└── config.json                    ← réglages globaux
```

**Règle d'or :** tout dossier nommé en français et placé à la racine doit être compréhensible et modifiable par un utilisateur non technique via l'Explorateur Windows.

---

## 3. Socle (core) — à bâtir AVANT les modules métier

Six services partagés que chaque module consomme. Ne pas commencer les modules tant que le socle n'est pas stable.

| Service | Rôle | Livrable |
|---|---|---|
| `llm_client` | Unique point d'entrée LM Studio, streaming, détection disponibilité | `generate(prompt, temperature, stream)` |
| `rag_engine` | Chunking PDFs, embeddings MiniLM, recherche ChromaDB, grounding | `reindex()`, `search(q, k)` → passages + refs |
| `doc_engine` | Remplissage templates Word + export PDF + injection logo/signature | `render(template, variables, entity)` |
| `entity_manager` | Multi-sociétés : logo, signature, config par entité active | `current.logo_path`, `switch(id)` |
| `logger` | Journal LPD : module, prompt, température, sources RAG, fichier | `log(module, request, response, sources)` |
| `config` | `config.json` unique, lu au démarrage | accès attribut |

Le **grounding** (affichage du passage source avant la réponse) exigé au §5.2 du cahier des charges est implémenté une seule fois dans `rag_engine` et réutilisé par tous les modules juridiques.

---

## 4. Contrat de module

Chaque outil RH est un dossier Python qui expose une classe standard :

```python
class Module:
    id = "certificats"
    nom = "Générateur de Certificats"
    icone = "diplome.svg"
    description = "Génère un certificat de travail (Art. 330a CO)"
    temperature = 0.3          # 0.1 pour juridique, 0.7 pour créatif

    def inputs_schema(self):
        """Décrit les champs de formulaire à afficher."""

    def run(self, inputs, services):
        """services = {llm, rag, doc, entity, logger}
        Retourne le chemin du fichier généré."""
```

Le dashboard scanne `_app/modules/` au démarrage et génère automatiquement une tuile par module trouvé. **Ajouter un nouvel outil = créer un dossier + une classe.** Zéro modification de l'UI.

### Mapping des 10 modules du cahier des charges

| Module cahier des charges | Température | Utilise RAG ? | Template Word |
|---|---|---|---|
| Générateur de Certificats | 0.3 | Non | `certificat.docx` |
| Assistant Juridique | 0.1 | **Oui (CO, LTr)** | — (chat) |
| Sourcing & CV Matcher | 0.2 | Non | `analyse_cv.docx` |
| Permis de Travail | 0.3 | Partiel | `lettre_permis.docx` |
| Cahier des Charges | 0.5 | Non | `fiche_poste.docx` |
| Neutraliseur de Feedback | 0.5 | Non | — (texte) |
| Traducteur Terminologique | 0.1 | Lexique AVS/LPP | — (texte) |
| Onboarding Dynamique | 0.6 | Non | `welcome_book.pdf` |
| Analyseur de CCT | 0.1 | **Oui (CCT déposée)** | `rapport_cct.docx` |
| Lettres Officielles | 0.2 | Partiel | `lettre_*.docx` |

---

## 5. Interface utilisateur

**Technologie retenue : PyWebView + HTML/Tailwind.**

- UI web locale rendue dans une fenêtre native (pas de navigateur ouvert)
- Look "application Windows" classique pour rassurer l'utilisateur RH
- Pas de dépendance à un navigateur tiers installé

### Écrans clés

1. **Dashboard** — Grille de 10 tuiles, sélecteur d'entité en haut à gauche, barre de statut en bas.
2. **Vue module** — Formulaire d'entrée + panneau de prévisualisation streaming + boutons "Ouvrir document" / "Ouvrir dossier".
3. **Paramètres** — Gestion entités (logos, signatures), bibliothèque juridique (liste + bouton "Réindexer"), préférences.
4. **Journal** — Historique consultable des générations (conformité LPD).

### Barre de statut permanente

```
🟢 IA Locale : Prêt    🟢 Base juridique : 247 articles    🔒 Hors ligne (Sécurisé)
```

En cas d'erreur : jamais de message technique brut. Traduction en langage métier + bouton "Afficher l'aide" qui ouvre un guide illustré.

---

## 6. Parcours utilisateur cible

1. Double-clic sur `ARHIANE.exe`
2. Fenêtre d'application s'ouvre — statut IA affiché
3. Sélection de l'entité (déroulant avec logos miniatures)
4. Clic sur une tuile du dashboard
5. Remplissage d'un formulaire simple
6. Génération avec aperçu streaming
7. Clic "Ouvrir le document" — `.docx` final avec logo et signature

**Jamais** de terminal, de fichier JSON à éditer, ou de message d'erreur technique.

---

## 7. Packaging

- **PyInstaller** en mode `--onedir` (pas `--onefile` : démarrage plus rapide, séparation code/données)
- Dossier final 200-400 Mo, copiable-collable sur tout poste Windows
- **Non embarqué dans le .exe :** modèle GGUF (reste dans LM Studio), `Base_Juridique/`, `Templates/`, `Entities/` (éditables)

---

## 8. Phasage de développement

Ordre strict pour garantir l'intégration propre :

### Phase 0 — Socle (1-2 semaines)
Arborescence, `config.json`, `llm_client` avec connexion LM Studio testée, `logger`, `entity_manager`, shell PyWebView avec dashboard vide auto-découvreur de modules.

**Livrable :** un `.exe` qui s'ouvre, détecte LM Studio, affiche "Aucun module installé" et log proprement.

### Phase 1 — Module pilote : Générateur de Certificats
Choix le plus emblématique ; il valide `doc_engine` + templates Word + multi-entités d'un coup. Si ce module fonctionne bout-en-bout, les suivants sont triviaux.

### Phase 2 — RAG + Assistant Juridique
Intégration ChromaDB, indexation CO et LTr, affichage des citations sources. Valide tout le sous-système juridique.

### Phase 3-N — Les 8 autres modules
Un par un. Chaque nouveau module devient un exercice de prompt engineering + template Word, sans code d'infrastructure.

### Phase finale — Packaging & documentation
PyInstaller + `README_UTILISATEUR.pdf` illustré (installation LM Studio, téléchargement modèle, premier usage).

---

## 9. Risques à surveiller

| Risque | Mitigation |
|---|---|
| LM Studio non lancé au démarrage | Guide illustré + détection + message métier clair |
| Modèle 9B trop lent sur poste client faible | Benchmark sur CPU moyen dès phase 0 ; fallback Qwen 7B Q4 |
| Hallucinations sur contenu juridique | Grounding obligatoire, température 0.1, citation source systématique |
| Taille package .exe | `--onedir`, exclusion modèle et bases éditables |
| Mise à jour réglementaire | Dépôt PDF utilisateur + bouton "Réindexer" (déjà au cahier des charges) |
| Dépendance à un poste Windows unique | v2 : mode réseau local avec serveur LM Studio mutualisé |

---

## 10. Prochaine étape

Démarrer la Phase 0 : créer l'arborescence, écrire `llm_client.py` et un shell PyWebView minimal qui affiche la barre de statut. Valider la connexion à LM Studio avant toute autre ligne de code.
