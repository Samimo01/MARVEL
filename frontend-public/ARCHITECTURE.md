# Architecture et conventions du frontend

Ce document décrit comment organiser et faire évoluer le code frontend. Il sert de référence pour ajouter des pages, des composants et des échanges avec le backend. Il ne constitue pas un inventaire des fonctionnalités.

## Principes d'organisation

- Regrouper le code propre à un domaine dans `src/features/<domaine>/`.
- Garder les pages comme points de composition : elles assemblent les composants et le hook du domaine, sans porter les détails du transport HTTP.
- Garder les composants d'interface réutilisables indépendants des données métier.
- Faire transiter les échanges avec une source distante par la couche API du domaine, plutôt que d'appeler le backend depuis un composant.
- Utiliser TypeScript pour décrire les entrées, sorties et états. Préférer les imports de type (`import type`) lorsqu'un import ne sert qu'au typage.
- Réutiliser les éléments transverses de `src/components/`, `src/hooks/` et `src/lib/` lorsqu'ils sont réellement génériques.

## Structure du code

```text
src/
├── App.tsx                 # Routes et composition des routes
├── main.tsx                # Montage React et styles globaux
├── styles/                 # Import de Tailwind et des styles globaux
├── components/
│   ├── layout/             # Structure commune et navigation
│   ├── ui/                 # Composants d'interface génériques
│   └── feedback/           # Chargement, erreur et état vide
├── features/
│   └── <domaine>/
│       ├── api.ts          # Accès aux données et opérations distantes
│       ├── types.ts        # Types du domaine et des entrées/sorties
│       ├── mocks/          # Données statiques temporaires tant que le backend manque
│       ├── hooks/          # Chargement, état et règles de présentation
│       └── components/     # Composants propres au domaine
├── hooks/                  # Hooks transverses sans dépendance métier
├── lib/                    # Utilitaires et infrastructure partagés
└── styles/                 # Styles globaux et jetons du thème
```

Les dossiers `api.ts`, `types.ts` et `hooks/` sont des repères d'organisation, pas une obligation de créer des fichiers vides. Commencer petit, puis extraire une couche quand elle a une responsabilité distincte ou qu'elle est réutilisée.

### Responsabilités

| Couche | Responsabilité | À éviter |
|---|---|---|
| `App.tsx` et `components/layout/` | Déclarer les routes, les gardes et la structure commune des écrans. | Charger les données propres à une page. |
| `pages/` | Composer un écran, choisir les états à afficher et relier le hook aux composants. | Implémenter le transport réseau ou accumuler la logique métier. |
| `features/<domaine>/api.ts` | Exposer des opérations typées et isoler la source des données. | Dépendre de composants React ou accéder au DOM. |
| `features/<domaine>/hooks/` | Orchestrer chargement, état local, actions et données dérivées. | Connaître les détails de rendu d'une table ou d'un formulaire. |
| `features/<domaine>/components/` | Afficher les données du domaine et remonter les intentions via des props/callbacks. | Effectuer directement des appels réseau. |
| `components/ui/` | Fournir des contrôles génériques configurés par props. | Contenir des règles propres à un domaine. |
| `components/feedback/` | Présenter les états communs de chargement, d'erreur ou de résultat vide. | Décider comment récupérer ou modifier les données. |
| `hooks/` et `lib/` | Héberger les comportements transverses et utilitaires purs. | Devenir un dépôt par défaut pour le code d'un domaine. |

Une page qui utilise le même domaine importe son hook et ses composants depuis `features/<domaine>`. Les composants partagés ne doivent pas importer un domaine pour en lire l'état : les données et callbacks descendent par props, les événements remontent par callbacks.

## Flux de données

### Flux de lecture

```text
Page
  → hook du domaine
    → fonction exportée par features/<domaine>/api.ts
      → client HTTP partagé (à introduire pour les appels backend)
        → backend
      ← réponse / erreur
    ← données typées + état de chargement/erreur
  → page et composants d'affichage
  → rendu React
```

La séquence attendue pour une lecture est la suivante :

1. La page appelle le hook du domaine.
2. Le hook déclenche l'opération exportée par le module `api.ts`, généralement depuis un `useEffect` ou en réponse à une action utilisateur.
3. La fonction API utilise le client HTTP partagé et retourne une `Promise` typée. Elle adapte la réponse réseau au type utilisé par l'interface si le contrat backend diffère.
4. Le hook met à jour les données et l'état de chargement ou d'erreur. Il ignore les résultats devenus obsolètes si le composant est démonté ou si la requête est remplacée.
5. La page choisit l'état de présentation, puis transmet les données aux composants. Les composants affichent les props sans connaître leur provenance.

Les données dérivées de l'état déjà chargé (filtrage local, agrégats, options d'affichage) restent dans le hook ou dans une fonction pure proche du domaine. Elles ne doivent pas déclencher une nouvelle requête. Utiliser `useMemo` uniquement lorsque le calcul ou sa stabilité le justifie.

### Flux de modification

```text
Action utilisateur
  → callback de la page / du composant
    → fonction API du domaine
      → backend
    ← succès ou erreur
  → mise à jour de l'état du hook
  → nouveau rendu
```

Les opérations de création, mise à jour et suppression suivent la même frontière API que les lectures. Le hook décide quand actualiser l'état local (réponse du serveur, rechargement ou mise à jour optimiste justifiée). Une mise à jour optimiste doit prévoir le retour arrière en cas d'échec. Les erreurs ne doivent pas être transformées en succès apparent.

### État affiché

Pour une donnée asynchrone, rendre explicites les états pertinents : chargement, erreur avec une action de reprise si appropriée, absence de résultat et données disponibles. Le hook expose des états suffisamment clairs pour éviter que la page déduise implicitement si une requête est terminée à partir d'un tableau vide.

Pour les appels effectués dans un effet, nettoyer l'effet (annulation via `AbortSignal` lorsque le client le permet, ou invalidation du résultat) afin d'éviter les mises à jour après démontage ou à la suite d'une requête périmée. Les actions initiées par l'utilisateur exposent également leur état de soumission si l'interface doit prévenir les doubles envois.

## Intégration du backend

À la date de rédaction, les modules `features/*/api.ts` retournent majoritairement des données simulées via des délais. Le code de `src/` ne réalise pas encore d'appel HTTP ; Axios figure dans les dépendances, mais aucun client HTTP partagé n'est actuellement utilisé. Le flux réel vers le backend devra donc être ajouté, et non supposé déjà en place.

Toute nouvelle page doit rester pleinement fonctionnelle avant l'implémentation de son backend. Dans ce cas, placer ses données statiques dans un sous-dossier `mocks/` de la feature concernée (`src/features/<domaine>/mocks/`) et les utiliser depuis `api.ts`. La page et ses hooks doivent continuer à passer par cette API, sans importer directement les mocks. Quand le backend sera disponible, remplacer l'implémentation de `api.ts` par les appels réseau en conservant autant que possible les mêmes fonctions et types : les mocks pourront alors être retirés sans modifier la page ni ses composants.

Pour connecter un domaine au backend :

1. Définir les fonctions publiques du domaine dans son `api.ts` (par exemple une lecture typée et les mutations nécessaires). Conserver une interface simple et indépendante de React.
2. Remplacer dans ce module l'utilisation des mocks statiques par un appel au client HTTP commun, sans faire remonter Axios ni les détails HTTP jusqu'aux composants.
3. Si plusieurs domaines ont besoin des mêmes paramètres réseau, créer un client commun dans `src/lib/` : base URL issue de la configuration Vite (`import.meta.env` et variable préfixée par `VITE_`), délais d'attente et traitement cohérent des réponses/erreurs. Ne pas dupliquer ces règles dans chaque domaine.
4. Déclarer les types des données réseau et convertir la réponse vers les types utilisés par l'interface lorsque nécessaire. Ne pas considérer une réponse JSON comme sûre uniquement parce qu'elle est annotée en TypeScript.
5. Laisser le hook piloter l'appel et son cycle de vie ; laisser la page et les composants gérer uniquement l'affichage et les interactions.

Ne jamais placer de secret dans une variable `VITE_*` : ces variables sont intégrées au code livré au navigateur. Les contrôles d'accès et autorisations doivent être appliqués par le backend ; une route gardée côté frontend n'est pas une frontière de sécurité.

## Conventions React et TypeScript

- Écrire les composants React en `.tsx`, les modules TypeScript sans JSX en `.ts`.
- Définir des props explicites avec des `interface` ou des `type`; utiliser des unions littérales pour les variantes finies.
- Utiliser des composants fonctionnels et des hooks. Maintenir les hooks au niveau supérieur du composant ou d'un hook personnalisé.
- Garder chaque composant focalisé sur une responsabilité lisible. Extraire un composant lorsqu'il a un rôle réutilisable ou clarifie sensiblement la composition.
- Passer les données et actions nécessaires via les props. Ne pas ajouter un état global tant qu'un état local au hook/page suffit ; si un état doit être partagé, documenter son propriétaire et les consommateurs.
- Préférer l'état dérivé à une copie redondante : ne pas stocker séparément une valeur qui peut être calculée de façon fiable depuis un état existant.
- Utiliser l'alias `@/` pour les imports depuis `src/` (configuré dans Vite et TypeScript). Les imports relatifs restent adaptés aux fichiers voisins d'un même domaine.
- Éviter les assertions de type qui masquent une incertitude sur les données. Valider ou convertir les réponses externes à la frontière API.
- Donner aux erreurs un traitement explicite et un message exploitable par l'interface. Ne pas avaler une erreur réseau ni retourner une valeur de repli qui ressemble à une réponse valide.

## Styles et interface

- Utiliser Tailwind CSS v4 pour les styles des pages et composants : composer les classes utilitaires dans `className`, y compris les variantes responsive et d'état (`sm:`, `hover:`, `focus-visible:`, `disabled:`).
- Garder le CSS dans `src/styles/` pour les règles globales, les jetons et les cas difficiles à exprimer clairement avec des utilitaires (par exemple une animation ou un sélecteur complexe). Ne pas créer une feuille CSS par page ou par domaine par défaut.
- Éviter les styles en ligne pour la présentation. Réutiliser les composants `components/ui/` pour partager des contrôles et leurs variantes visuelles.
- Un composant générique reçoit ses variantes et son état via des props, au lieu de dépendre d'un écran précis.
- Préserver l'accessibilité des éléments interactifs : élément HTML approprié, libellé, état désactivé et comportement clavier.

## Ajout d'une nouvelle tranche d'interface

1. Déclarer la route dans `src/App.tsx` et déterminer si elle relève de la structure commune ou d'un écran autonome.
2. Créer la page dans `src/pages/` et les éléments propres au domaine dans `src/features/<domaine>/`.
3. Définir les types d'interface et les types d'entrée/sortie de l'API dans le domaine.
4. Placer les données statiques temporaires dans `features/<domaine>/mocks/` et les exposer via `api.ts`, puis orchestrer chargement, erreurs et actions dans un hook. À l'implémentation du backend, remplacer la source dans `api.ts` sans faire dépendre la page ou ses composants des mocks.
5. Composer la page avec ce hook et des composants d'affichage ; utiliser les composants partagés pour les éléments génériques et les états de feedback, et Tailwind CSS pour leur mise en forme.
6. Vérifier les états chargement/erreur/vide/données, le comportement des mutations, le typage, le rendu responsive et les règles de lint.

## Vérification locale

Les scripts existants sont définis dans `frontend/package.json` :

```bash
npm run build
npm run lint
```

Exécuter au minimum le build TypeScript/Vite et le lint après une modification du frontend.