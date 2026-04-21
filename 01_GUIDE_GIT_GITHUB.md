# Setup Git + GitHub privé (multi-machines)

Ce guide te permet de versionner le projet en repo privé et de le synchroniser entre tous tes ordinateurs. À faire **une seule fois** par ordinateur.

---

## 1. Prérequis

- **Git** installé sur chaque ordinateur → <https://git-scm.com/download/win>
- **Compte GitHub** + **GitHub CLI** (`gh`) → <https://cli.github.com/> (facultatif mais gros gain de temps)

Vérifie :

```bash
git --version
gh --version
```

---

## 2. Initialiser le repo (sur l'ordinateur actuel uniquement)

Depuis le dossier `Swiss HR AI` :

```bash
cd "C:\Users\guill\Documents\Claude\Projects\Swiss HR AI"

git init
git add .
git commit -m "Phase 0 : socle + interface générale"
```

---

## 3. Créer le repo privé sur GitHub

### Option A — avec GitHub CLI (le plus simple)

```bash
gh auth login          # à faire une fois
gh repo create swiss-hr-ai --private --source=. --remote=origin --push
```

Et c'est fini. Le repo est créé, connecté et poussé.

### Option B — via l'interface web GitHub

1. Va sur <https://github.com/new>
2. Nom : `swiss-hr-ai` (ou ce que tu veux)
3. Coche **Private**
4. Ne coche PAS "Initialize with README" (on a déjà le nôtre)
5. Crée le repo, puis exécute les commandes affichées :

```bash
git remote add origin https://github.com/<ton-user>/swiss-hr-ai.git
git branch -M main
git push -u origin main
```

---

## 4. Cloner sur un AUTRE ordinateur

```bash
cd "C:\Users\<toi>\Documents\Claude\Projects"
git clone https://github.com/<ton-user>/swiss-hr-ai.git "Swiss HR AI"
cd "Swiss HR AI"

python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Puis : ouvrir LM Studio, charger Qwen, lancer le serveur, et double-clic sur `SwissHR.bat`.

---

## 5. Workflow quotidien

Au **début** d'une session de travail :

```bash
git pull
```

À la **fin** d'une modification :

```bash
git add .
git commit -m "Description claire de ce que tu as changé"
git push
```

---

## 6. Ce qui est EXCLU du versioning (via .gitignore)

Le `.gitignore` que j'ai mis en place exclut automatiquement :

- Les environnements virtuels Python (`.venv/`)
- Les fichiers compilés (`__pycache__/`, `*.pyc`)
- Les sorties générées (`Outputs/`, `Logs/`, `data/`)
- Les modèles IA (`*.gguf`) — trop lourds, gérés par LM Studio séparément
- Les logos et signatures des entités réelles (sensibles) — la démo est gardée
- Les fichiers OS/IDE (`.DS_Store`, `.vscode/`, etc.)

**Point d'attention :** par défaut, les PDFs de `Base_Juridique/` SONT versionnés
(CO, LTr sont publics). Si tu y mets des CCT confidentielles ou des documents
spécifiques à un client, décommente la ligne `# Base_Juridique/*.pdf` dans
`.gitignore`.

---

## 7. Bonnes pratiques pour un projet privé à données sensibles

1. **Ne jamais** committer de vraies données d'employés, salaires ou contrats.
   Utilise toujours l'`Entite_Demo` pour tester.
2. Si tu ajoutes un token API, une clé, un mot de passe : mets-le dans un
   fichier `.env` (déjà ignoré par `.gitignore`).
3. Active la **protection de branche** `main` dans les paramètres GitHub
   une fois que le projet mûrit, pour éviter un `push --force` malheureux.
4. Pour un vrai déploiement client, ce repo doit rester **strictement privé**
   vu qu'il contient la logique métier qui fera la valeur du produit.
