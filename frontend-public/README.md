# frontend-public — Vitrine de l'association

## Rôle

Site public de l'association : présentation, **campagnes en cours avec objectif et jauge de
progression**, actualités, formulaire de don et espace donateur. Il est volontairement séparé du
back-office (`frontend-admin`) pour que la vitrine reste disponible même si le back-office est
en cours de déploiement ou en panne.

Il ne parle qu'aux routes **publiques** de l'API (`/api/v1/public/...`).

**Stack** : React 19, Vite, TypeScript, Tailwind CSS 4, React Router, Vitest + Testing Library,
ESLint, Prettier.

## Structure

```text
src/
├── components/            # Composants génériques, sans logique métier (pilotés par leurs props)
│   ├── ui/                # Button, Card, Badge, ProgressBar
│   ├── layout/            # Header, Footer, PageContainer, AppLayout
│   └── feedback/          # Spinner, ErrorMessage, EmptyState
├── features/              # Un dossier par domaine métier (composants, hooks, api.ts, types.ts)
│   ├── campaigns/         # Exemple complet : liste des campagnes depuis l'API
│   ├── donations/         # Formulaire de don (à faire)
│   ├── donor-space/       # Historique et reçus du donateur (à faire)
│   └── news/              # Actualités (à faire)
├── pages/                 # Une page par route : assemble layout + features
├── hooks/                 # Hooks génériques (useAsync)
├── lib/                   # Client API centralisé, config, textes (fr), formatage
└── styles/                # index.css, tokens.css (identité visuelle), base.css
```

Sens des dépendances : `pages` → `features` → `components`. Un composant de `components/` ne
connaît jamais le vocabulaire métier (don, campagne…) et n'appelle jamais l'API.

## Installation

Prérequis : Node.js 20 ou plus récent (npm inclus). L'API (`backend`) doit tourner pour afficher
les données.

```powershell
cd frontend-public

# 1. Dépendances
npm install

# 2. Configuration (le fichier .env n'est jamais versionné)
Copy-Item .env.example .env
```

Sous Linux / macOS : `cp .env.example .env`.

## Lancer le site

```powershell
npm run dev
```

Le site est servi sur <http://localhost:5173>.

## Communication avec l'API

En développement, les appels `/api/...` sont envoyés par le **proxy Vite** vers l'API
(`VITE_PROXY_TARGET`, par défaut `http://localhost:8000`), sans souci de CORS. Tous les appels
passent par `src/lib/api-client.ts` (aucun `fetch` ailleurs).
En production, laisser `VITE_API_URL` vide si le reverse proxy sert le site et l'API sur le même
domaine, sinon y mettre l'URL publique de l'API.

> Tout ce qui se trouve dans `.env` finit dans le bundle du navigateur : **aucun secret ici**.

## Commandes utiles

```powershell
npm run build          # build de production (dossier dist/)
npm run preview        # prévisualiser le build
npm test               # tests Vitest
npm run lint           # ESLint
npm run format         # Prettier (avec tri des classes Tailwind)
```

## Règles du module (rappel des conventions)

- Style : classes utilitaires Tailwind d'abord ; couleurs et polices uniquement via les tokens de
  `src/styles/tokens.css` (jamais de couleur en dur).
- Textes d'interface regroupés dans `src/lib/texts.ts` (français).
- Accessibilité de base : labels de formulaires, contrastes, navigation clavier.
