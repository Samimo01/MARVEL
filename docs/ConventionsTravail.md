# Conventions de travail du projet DevOps (Thème 16)

Équipe de 5 étudiants · Version 1 du 30 octobre 2026 · À valider ensemble avant le début de l'implémentation

Ce document fixe les règles communes. Objectif : éviter les conflits, garder un code lisible et prouver une démarche DevOps rigoureuse. Une règle qui n'est pas appliquée automatiquement (CI, hooks, protections de branche) sera oubliée : chaque fois que possible, un outil la vérifie à notre place.

## 1. Langues

| Élément | Langue | Exemple |
| --- | --- | --- |
| Échanges d'équipe, documentation, README, ADR | Français | « Guide d'installation » |
| Interface utilisateur (libellés, messages) | Français | « Faire un don » |
| Noms de variables, fonctions, classes, fichiers, dossiers | Anglais | `create_donation`, `DonationReceipt` |
| Tables et colonnes de la base de données | Anglais | `donations`, `created_at` |
| Routes de l'API | Anglais | `/api/v1/donations` |
| Messages de commit | Français (court, à l'impératif) | `feat: a``jout`` ``n``um``érot`` ation  ``r``e``ç``u``s` |
| Titres et descriptions des Pull Requests | Français | « Ajoute la numérotation des reçus » |

Un seul glossaire métier fait foi (voir section 11) pour que « bénéficiaire », « aide » et « distribution » aient le même nom anglais partout.

## 2. Organisation du dépôt

Monorepo unique :

```
charity-donations/
├── backend/            # API FastAPI
├── frontend-public/    # Vitrine
├── frontend-admin/     # Back-office
├── infra/              # Docker Compose, proxy, monitoring, sauvegardes
├── docs/               # Documentation, ADR, schémas
├── .github/            # Workflows, templates d'issues et de PR
└── README.md
```

Règles :

- Chaque dossier racine a son propre `README.md` (comment lancer, tester, construire) ainsi que son `.``e``n``v.exa``mple` (variables d'environnement sans valeurs sensibles)
- Aucun fichier généré (builds, caches, `node_modules`, `__pycache__`, dumps de base) n'est versionné : tout est dans `.gitignore`.
- Un fichier ne vit que dans un seul dossier : pas de copie de code entre `frontend-public` et `frontend-admin`. Si du code est commun, on décide ensemble de l'extraire.

## 3. Stratégie de branches (GitHub Flow simplifié)

- `main` : toujours stable et déployable. **Personne ne pousse directement dessus** (protection de branche activée).
- Branches de travail courtes (idéalement moins de 3 jours), créées depuis `main` à jour.

| Préfixe | Usage | Exemple |
| --- | --- | --- |
| `feat/` | Nouvelle fonctionnalité | `feat/donation-receipt-pdf` |
| `fix/` | Correction de bug | `fix/stock-negative-quantity` |
| `docs/` | Documentation seule | `docs/install-guide` |
| `chore/` | Outillage, dépendances, config | `chore/add-ruff` |
| `ci/` | Pipelines | `ci/add-trivy-scan` |
| `test/` | Ajout ou refonte de tests | `test/e2e-donation-flow` |

Nommage : minuscules, tirets, anglais, descriptif (pas de `ma-branche` ni de prénom).

**Protection de `main` (à configurer dès le jour 1) :**

- Pull Request obligatoire.
- Au moins 1 approbation (2 pour les zones sensibles, voir section 5).
- La CI doit être verte avant fusion.
- Branche à jour avec `main` avant fusion.
- Force-push interdit.

## 4. Convention de commits (Conventional Commits)

Format : `type(scope optionnel): description courte à l'impératif`

| Type | Quand l'utiliser |
| --- | --- |
| `feat` | Nouvelle fonctionnalité |
| `fix` | Correction de bug |
| `docs` | Documentation |
| `style` | Formatage sans changement de logique |
| `refactor` | Restructuration sans changement de comportement |
| `test` | Ajout ou modification de tests |
| `chore` | Outillage, dépendances |
| `ci` | Pipelines CI/CD |
| `build` | Docker, dépendances de build |

Exemples :

```
feat(donations): ajout endpoint de don financier
fix(stock): empêchement des stocks négatifs
docs: documentation de restauration des sauvegardes
ci: exécution de Gitleaks sur les pull requests
```

Règles :

- Description de 72 caractères maximum, sans point final, à l'impératif (« add », pas « added »).
- **Un commit = un changement logique.** Pas de commit « divers » ni « wip » sur une branche destinée à être fusionnée.
- Jamais de commit contenant un secret, même supprimé ensuite : l'historique Git le conserve.
- Un hook `pre-commit` vérifie le format et détecte les secrets avant le commit.

## 5. Pull Requests et revues de code

### Ouvrir une PR

- Une PR = un sujet. Taille cible : moins de 400 lignes modifiées. Au-delà, on découpe.
- Titre au format Conventional Commits, description en français avec le modèle ci-dessous.
- PR en mode **Draft** tant qu'elle n'est pas prête à relire.
- Lier l'issue concernée (`Closes #12`).

**Modèle de description :**

```
## Contexte
Pourquoi ce changement ?

## Changements
- ...

## Comment tester
1. ...

## Checklist
- [ ] Tests ajoutés ou mis à jour
- [ ] Documentation mise à jour
- [ ] Aucune donnée sensible dans le code
- [ ] La CI est verte
```

### Relire une PR

- Délai cible de première relecture : **24 heures ouvrées**.
- Relire pour : la correction, la lisibilité, les tests, la sécurité, la cohérence avec l'architecture.
- Commentaires respectueux et précis : proposer une alternative plutôt que critiquer. Préfixes conseillés : `question:`, `suggestion:`, `bloquant:`.
- L'auteur répond à chaque commentaire ; le relecteur résout la discussion une fois satisfait.
- On ne fusionne pas sa propre PR sans approbation.

### Zones sensibles (2 approbations)

Authentification et rôles, paiement simulé, numérotation des reçus, mouvements de stock, migrations de base de données, pipelines CI/CD, secrets.

### Fusion

**Squash and merge** par défaut : un commit propre sur `main` par PR. La branche est archivée après fusion.

## 6. Gestion des conflits

- Récupérer `main` souvent (au moins une fois par jour de travail) : `git pull --rebase origin main` sur sa branche.
- Les conflits se résolvent **par l'auteur de la branche**, pas par le relecteur.
- En cas de doute sur le code de quelqu'un d'autre, on le contacte avant de trancher.
- Pour limiter les conflits : une personne par fichier sensible à un instant donné (migrations, `docker-compose`, fichiers de config), annonce sur le canal d'équipe avant de les modifier.
- Migrations de base de données : **jamais deux migrations en parallèle sans coordination** (voir section 9).

## 7. Conventions de code

### Nommage général

| Élément | Style | Exemple |
| --- | --- | --- |
| Variables, fonctions (Python) | `snake_case` | `total_amount` |
| Classes (Python et TypeScript) | `PascalCase` | `DonationService` |
| Constantes | `UPPER_SNAKE_CASE` | `MAX_UPLOAD_SIZE` |
| Fichiers et dossiers Python | `snake_case` | `receipt_service.py` |
| Variables et fonctions (TypeScript) | `camelCase` | `fetchDonations` |
| Composants React | `PascalCase` | `CampaignCard.tsx` |
| Fichiers non-composants front | `kebab-case` | `api-client.ts` |
| Tables SQL | pluriel, `snake_case` | `stock_movements` |
| Routes API | pluriel, minuscules, tirets | `/api/v1/stock-movements` |

### Backend (Python / FastAPI)

- Formatage et lint : `ruff` (une seule configuration partagée dans `pyproject.toml`).
- Annotations de types sur les fonctions publiques.
- Architecture en couches par module : `router` (HTTP) → `service` (logique métier) → `repository` (accès base). **Aucune logique métier dans les routers.**
- Schémas Pydantic distincts pour l'entrée et la sortie : on n'expose jamais directement un modèle de base de données.
- Gestion d'erreurs : exceptions métier explicites, converties en réponses HTTP cohérentes (format d'erreur unique).
- Docstring courte sur toute fonction métier non triviale. Un commentaire explique le **pourquoi**, pas le quoi.

### Frontend (React / Vite)

- Lint et format : `ESLint` et `Prettier`, configuration partagée.
- Composants fonctionnels et hooks uniquement.
- Les appels à l'API passent par un seul client centralisé (pas de `fetch` éparpillés dans les composants).
- Aucun secret ni clé privée côté frontend : tout ce qui est dans le bundle est public.
- Les textes d'interface sont regroupés (pas de chaînes françaises dupliquées partout).
- Accessibilité de base : labels de formulaires, contrastes, navigation clavier sur les formulaires de don.

#### Organisation des dossiers de composants

Les composants du dossier `components/` sont **réutilisables et ne contiennent aucune logique métier**. Tout ce qui connaît le vocabulaire de l'association (don, campagne, stock, bénéficiaire) vit dans `features/`. Le même schéma s'applique à `frontend-admin/` et `frontend-public/`.

```
src/
├── components/             # Composants génériques : réutilisables, sans logique métier
│   ├── ui/                 # Briques visuelles : Button, Input, Select, Modal, Table, Badge, Card
│   ├── layout/             # Structure des pages : AppShell, Header, Sidebar, PageContainer, Footer
│   └── feedback/           # Retours à l'utilisateur : Spinner, EmptyState, ErrorMessage, Toast
├── features/               # Un dossier par domaine métier : c'est ici que vit la logique métier
│   ├── donations/
│   │   ├── components/     # DonationForm, DonationList, ReceiptDownloadButton
│   │   ├── hooks/          # useDonations, useCreateDonation
│   │   ├── api.ts          # Appels à l'API de ce domaine
│   │   └── types.ts        # Types du domaine
│   ├── campaigns/
│   ├── stock/
│   └── beneficiaries/
├── pages/                  # Une page par route : assemble layout + features
├── hooks/                  # Hooks génériques (useDebounce, useMediaQuery), sans lien métier
├── lib/                    # Client API centralisé, utilitaires, configuration
└── styles/                 # Styles globaux et tokens (couleurs, espacements)
```

| Dossier | Rôle | Peut importer | Ne doit jamais |
| --- | --- | --- | --- |
| `components/ui/` | Éléments visuels de base, pilotés uniquement par leurs props | Autres `ui/`, `styles/`, `lib/` (utilitaires purs) | Appeler l'API, connaître un rôle ou un terme métier |
| `components/layout/` | Squelette des pages (en-tête, menu, conteneur) | `ui/`, `feedback/` | Décider quels menus afficher selon le rôle : la liste des entrées est passée en props |
| `components/feedback/` | États de chargement, d'erreur, de vide, notifications | `ui/` | Contenir un message métier en dur : le texte arrive en props |
| `features/<domaine>/` | Écrans et composants propres à un domaine, hooks, appels API | `components/`, `lib/`, `hooks/` | Importer depuis un autre `features/` (passer par la page ou un module partagé) |
| `pages/` | Assemblage d'une route | `components/`, `features/` | Contenir de la logique métier complexe : elle est dans les hooks du domaine |

**Sens des dépendances :** `pages` → `features` → `components`. Un composant de `components/` n'importe **jamais** depuis `features/` ni `pages/`. Si ça arrive, le composant n'est pas générique : il doit déménager dans `features/`.

**Règles pour tout composant de `components/` :**

1. **Piloté uniquement par ses props** : il affiche ce qu'on lui donne et signale les actions par des callbacks (`onClick`, `onSubmit`, `onChange`).
2. **Aucun appel réseau** (`fetch`, client API) et aucun accès direct au contexte d'authentification.
3. **Aucune règle métier** : pas de calcul de montant, pas de test sur un rôle, pas de statut de don ou de stock.
4. **Aucun vocabulaire métier dans son nom ni ses props** : `Table`, pas `DonationTable` ; `ProgressBar` avec `value` et `max`, pas `CampaignGauge`.
5. **Textes par props** (ou par clés de traduction passées de l'extérieur), jamais de phrase métier en dur.
6. **Testable seul** : un test Vitest avec des props suffit, sans serveur, sans base ni mock d'API.

**Test rapide avant de créer un composant dans `components/` :** peut-il être copié dans un autre projet, sans rien modifier, et fonctionner ? Si la réponse est non, il va dans `features/<domaine>/components/`.

**Exemple :**

- À éviter : `components/ui/DonationCard.tsx` qui récupère le don via l'API et colore le badge selon le statut du reçu.
- À faire : `components/ui/Card.tsx` et `components/ui/Badge.tsx` (génériques), puis `features/donations/components/DonationCard.tsx` qui assemble `Card` et `Badge` avec les données du don.

Les composants génériques dupliqués entre `frontend-admin/` et `frontend-public/` sont signalés à l'équipe : on décide ensemble s'il faut les extraire dans un paquet partagé plutôt que de les copier.

### Fichiers de style (Tailwind CSS et CSS)

Principe : **le style se fait d'abord avec les classes utilitaires Tailwind, directement dans les composants.** Le CSS écrit à la main est l'exception, limité à ce que Tailwind ne couvre pas.

```
src/
└── styles/
    ├── index.css       # Point d'entrée : directives Tailwind (@tailwind / @import) et imports ci-dessous
    ├── tokens.css      # Variables CSS : couleurs, espacements, rayons, typographie
    ├── base.css        # Reset léger et styles des balises HTML (body, a, h1...)
    └── animations.css  # Animations réutilisables (si besoin)
```

**Organisation des fichiers**

- **Un seul point d'entrée** (`index.css`), importé une fois dans `main.tsx`. Aucun composant n'importe un fichier CSS global.
- Les styles globaux vivent uniquement dans `src/styles/`. Pas de fichier CSS isolé à la racine de `src/` ou dans `pages/`.
- Un style propre à un composant, quand Tailwind ne suffit pas, va dans un fichier du même nom à côté du composant : `Button.module.css` à côté de `Button.tsx` (**CSS Modules**, portée locale).
- **Pas de CSS global pour un composant** : jamais de sélecteur `.card { ... }` dans un fichier partagé.
- Pas de fichier de style par page : une page assemble des composants, elle n'a pas d'identité visuelle propre.

**Design tokens (identité visuelle unique)**

- Couleurs, polices, espacements, rayons et ombres sont définis **une seule fois** (`tokens.css` et configuration Tailwind), puis réutilisés partout.
- **Interdit** : valeur de couleur en dur dans un composant (`#1e40af`, `rgb(...)`, `text-[#1e40af]`). On utilise un nom sémantique : `bg-primary`, `text-muted`, `border-danger`.
- Noms de tokens **sémantiques** (rôle, pas apparence) : `--color-primary`, `--color-danger`, `--color-surface`, pas `--color-blue-dark` ni `--color-red2`.
- Valeurs arbitraires Tailwind (`w-[437px]`, `mt-[13px]`) : à éviter. Si le besoin revient, on ajoute un token ou on utilise l'échelle d'espacement standard.
- Changer le thème de l'association (couleur principale, police) doit demander de modifier **un seul fichier**.

**Nommage**

- Fichiers de style : `kebab-case` en minuscules, **en anglais** (`tokens.css`, `base.css`), ou du même nom que leur composant pour les modules (`Button.module.css`).
- Variables CSS : préfixe par catégorie (`--color-*`, `--space-*`, `--radius-*`, `--font-*`).
- Classes CSS personnalisées (modules) : `camelCase` (`styles.cardHeader`), sans vocabulaire métier lorsqu'elles sont dans `components/` (voir la règle ci-dessus).

**Utilisation de Tailwind**

- Classes dans un ordre cohérent, appliqué automatiquement par le plugin `prettier-plugin-tailwindcss` (aucun tri manuel).
- Variantes avec le préfixe d'état ou de taille (`hover:`, `focus-visible:`, `md:`), approche **mobile d'abord** : le style de base vaut pour un petit écran, on l'enrichit avec `md:` et `lg:`.
- Une longue liste de classes répétée dans plusieurs endroits devient un **composant React** (par exemple `Button`), pas une classe `@apply` globale. `@apply` reste exceptionnel.
- Les variantes d'un composant (taille, couleur, état) sont décrites par des props typées et regroupées au même endroit, pas dispersées dans des conditions de chaînes.

**Règles générales de CSS**

- **Pas de `!important`**, sauf pour surcharger une bibliothèque tierce, avec un commentaire qui explique pourquoi.
- **Pas de style en ligne** (`style={{ ... }}`), sauf valeur réellement dynamique (largeur d'une jauge de progression calculée).
- Sélecteurs courts et peu imbriqués (3 niveaux maximum). Pas de sélecteur sur un identifiant (`#id`) pour du style.
- Unités relatives : `rem` pour les tailles et les espacements, pas de `px` pour la typographie.
- Pas de code mort : une règle inutilisée est supprimée, pas commentée.

**Accessibilité et responsive**

- Contraste suffisant entre texte et fond (ratio WCAG AA : 4,5 pour le texte normal). Les tokens de couleur sont choisis pour le respecter.
- **Ne jamais supprimer l'indicateur de focus** (`outline: none` interdit sans remplacement visible) : on utilise `focus-visible:`.
- Zones cliquables d'au moins 44 px de côté sur mobile.
- Les tableaux larges défilent dans leur propre conteneur (`overflow-x-auto`) : la page ne défile jamais horizontalement.
- Respect de `prefers-reduced-motion` pour les animations non essentielles.

**Vérification automatique**

- `Prettier` (avec le plugin Tailwind) et `ESLint` sont exécutés par le hook `pre-commit` et par la CI.
- Un outil de lint CSS (`stylelint`) peut être ajouté pour interdire `!important`, les couleurs en dur et les sélecteurs trop profonds.
- Une PR qui modifie les tokens ou la configuration Tailwind est relue par le responsable frontend, car elle affecte tout le site.

### Base de données

- Toute modification de schéma passe par une **migration Alembic** versionnée. Jamais de modification manuelle d'une base partagée.
- Contraintes d'intégrité dans la base (clés étrangères, `NOT NULL`, `UNIQUE`, `CHECK`), pas seulement dans le code.
- Montants financiers : type décimal, **jamais de flottant**. Dates en UTC.
- Colonnes standard : `id`, `created_at`, `updated_at`.
- On ne supprime pas les données financières ni de stock : on ajoute des écritures correctives (traçabilité).

### API

- Versionnée (`/api/v1/`), documentée automatiquement (OpenAPI).
- Codes HTTP corrects (201 création, 400/422 validation, 401/403 droits, 404 introuvable, 409 conflit).
- Listes paginées. Aucun endpoint de données privées sans authentification ni contrôle du rôle.
- **Un changement de contrat d'API est annoncé à l'équipe avant la fusion** (les frontends en dépendent).

## 8. Sécurité et secrets

- **Aucun secret dans le dépôt** : mots de passe, clés API, jetons, clés du moyen de paiement de test.
- `.env.example` versionné avec des valeurs factices et des commentaires ; `.env` jamais versionné (`.gitignore`).
- En CI/CD : secrets stockés dans **GitHub Secrets**, jamais affichés dans les logs.
- Si un secret fuit : on le **révoque et on le remplace immédiatement** (le supprimer du code ne suffit pas), puis on prévient l'équipe.
- Mots de passe stockés hachés (argon2 ou bcrypt), jamais en clair, jamais journalisés.
- Aucune donnée bancaire réelle, même pour tester. Aucune donnée personnelle réelle dans les jeux de test (données fictives uniquement).
- Les logs ne contiennent ni mot de passe, ni jeton, ni données personnelles inutiles.
- Dépendances : mises à jour régulières, scan automatique (`pip-audit`, `npm audit`, Trivy) en CI.

## 9. Tests et qualité

| Niveau | Outil | Ce qu'on teste | Quand |
| --- | --- | --- | --- |
| Unitaires | pytest, Vitest | Logique métier isolée (calcul de jauge, numérotation, règles de doublons) | À chaque PR |
| Intégration | pytest + base de test | API, base de données, droits par rôle | À chaque PR |
| Fonctionnels (E2E) | Playwright | Parcours clés (don, reçu, distribution) | Sur PR vers `main` et avant déploiement |
| Disponibilité | Healthchecks, Uptime Kuma | Services vivants | En continu |

Règles :

- **Une fonctionnalité n'est pas terminée tant que sa méthode de test n'est pas définie et exécutée.**
- Tout bug corrigé reçoit un test qui l'aurait détecté (test de non-régression).
- Les tests sont indépendants, reproductibles, et n'utilisent jamais de service externe réel.
- Les règles critiques (numérotation des reçus, stock jamais négatif, doublons de distribution, droits par rôle) ont **obligatoirement** des tests.
- La CI doit être verte pour fusionner. Un test qui échoue ne se désactive pas : on le corrige ou on en discute.

## 10. Définitions communes

### Definition of Ready (une tâche peut démarrer si…)

- Elle est décrite dans une issue avec un objectif clair.
- Les critères d'acceptation sont écrits.
- Ses dépendances (API, schéma, maquette) sont disponibles ou simulables (mock).

### Definition of Done (une tâche est terminée si…)

- Le code est fusionné dans `main` via PR approuvée.
- La CI est verte (lint, tests, build des images).
- Des tests couvrent la fonctionnalité.
- La documentation concernée est mise à jour (README, OpenAPI, schéma, guide).
- Aucune donnée sensible n'a été ajoutée au dépôt.
- La fonctionnalité a été vérifiée dans l'environnement `docker compose` local.
- Pour une fonctionnalité visible : démontrée à au moins un autre membre.

## 11. Docker, environnements et infrastructure

- Tout le projet se lance avec **une seule commande** : `docker compose up`. Si ce n'est plus le cas, c'est un bug prioritaire.
- Un Dockerfile par service (backend, frontend-public, frontend-admin). Images légères, construction en plusieurs étapes (multi-stage), exécution sans privilèges root quand c'est possible.
- Pas de tag `latest` en production : les images sont taguées avec la version ou le SHA du commit.
- Environnements : **dev** (local), **prod** (serveur) ; staging optionnel. Mêmes images, configuration différente par variables d'environnement.
- Volumes nommés pour les données persistantes (base, PDF de reçus). Réseaux Docker séparés pour isoler la base de données (non exposée publiquement).
- Toute modification d'infrastructure (Compose, proxy, pipelines) passe par PR avec 2 approbations.

## 12. CI/CD et sauvegardes

- **Sur chaque PR** : lint, tests, build des images Docker, scan de secrets (gitleaks), scan d'images/dépendances.
- **Sur merge dans `main`** : construction et publication des images dans GHCR, puis déploiement automatique.
- Un pipeline rouge est prioritaire sur toute nouvelle fonctionnalité : la personne qui l'a cassé le répare, ou annule son changement.
- On ne contourne jamais la CI (pas de fusion forcée).
- **Sauvegardes** : sauvegarde automatique de PostgreSQL, rétention définie, procédure de restauration écrite dans `docs/`, et **restauration testée régulièrement avec une preuve** (journal ou capture) conservée.

## 13. Documentation

- Docs dans le dépôt (`docs/`), en Markdown, relues comme du code (via PR).
- Documents minimaux : README racine (démarrage rapide), guide d'installation, architecture (schémas), modèle de données, guide de déploiement, procédure de sauvegarde/restauration, guide de contribution (ce document).
- **ADR** (Architecture Decision Record) pour toute décision structurante : un court fichier `docs/adr/NNNN-titre.md` (contexte, décision, conséquences). Exemples : choix de FastAPI, pas de Redis au MVP, simulateur de paiement interne.
- Quand une PR change le comportement, elle met à jour la documentation concernée.

## 14. Communication et organisation de l'équipe

- **Suivi des tâches** : GitHub Issues et GitHub Projects (colonnes : À faire, En cours, En revue, Terminé). Toute tâche a une personne responsable.
- **Point d'équipe court** (15 minutes, 2 à 3 fois par semaine) : qu'ai-je fait, que vais-je faire, ce qui me bloque.
- **Revue de sprint** à la fin de chaque sprint : démonstration et mise à jour du planning.
- Un canal de discussion unique pour l'équipe ; les décisions importantes sont consignées par écrit (issue, ADR ou compte rendu) pour ne pas dépendre de la mémoire de chacun.
- **On signale un blocage dès qu'il apparaît**, pas à la fin de la semaine. Demander de l'aide n'est pas un échec : le pair-programming est encouragé, surtout pour accompagner un membre moins expérimenté.
- Répartition équitable : les responsabilités principales sont définies, mais chacun relit le travail des autres et doit pouvoir expliquer l'ensemble du projet en soutenance.

## 15. Utilisation de l'assistant IA

L'assistant (Claude) est un mentor technique, pas un substitut à la compréhension.

- On avance **étape par étape** : pas de génération de tout le projet d'un coup.
- Chaque proposition de code précise **le chemin des fichiers** à créer ou modifier, et ce qui est ajouté, remplacé ou supprimé.
- Les décisions techniques sont expliquées **avant** les implémentations importantes.
- Le code généré est **relu, compris et testé** avant d'être commité. Chacun doit pouvoir expliquer ce qu'il soumet en PR.
- Face à une erreur, on commence par **comprendre la cause**, puis on corrige.
- On ne colle jamais de secret, de donnée personnelle ou de clé dans une conversation avec l'assistant.