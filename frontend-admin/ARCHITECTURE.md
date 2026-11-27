# Architecture et conventions de développement — MARVEL Front-office Admin

## 1. Objectif du document

Ce document définit l'architecture technique et les conventions de développement à respecter dans le frontend d'administration de MARVEL.

Il sert de référence pour :

- organiser les fichiers et les fonctionnalités ;
- garantir une séparation claire des responsabilités ;
- maintenir un code lisible, réutilisable et évolutif ;
- assurer une communication cohérente avec le backend ;
- éviter les duplications et les incohérences de typage ;
- faciliter le travail collaboratif et les revues de code.

Toute nouvelle fonctionnalité et toute modification du code existant doivent respecter ces conventions.

---

## 2. Stack technique

Le frontend-admin repose sur les technologies suivantes :

| Technologie | Utilisation |
|---|---|
| React | Construction de l'interface |
| TypeScript | Typage statique |
| Vite | Serveur de développement et build |
| Tailwind CSS | Stylisation |
| React Router | Navigation et routage |
| React Context | Gestion des contextes globaux |
| i18next / react-i18next | Internationalisation |
| Zod | Validation des données lorsque nécessaire |
| React Hook Form | Gestion des formulaires complexes |

Les composants génériques du template TailAdmin sont conservés lorsqu'ils sont utiles. Ils doivent être personnalisés et réutilisés plutôt que remplacés systématiquement.

---

## 3. Organisation générale du projet

L'organisation principale du dossier `src/` est la suivante :

```text
src/
├── app/
│   ├── auth/
│   ├── providers/
│   ├── router/
│   ├── api-client.ts
│   └── config.ts
│
├── assets/
│   ├── images/
│   └── ...
│
├── components/
│   ├── ui/
│   └── shared/
│
├── features/
│   ├── auth/
│   ├── dashboard/
│   ├── errors/
│   └── ...
│
├── layouts/
├── hooks/
├── icons/
├── i18n/
├── messages/
├── utils/
│
├── App.tsx
└── main.tsx
```

Cette arborescence représente l'organisation cible. Les modules qui ne sont pas encore implémentés peuvent être ajoutés progressivement.

### 3.1. Responsabilité des dossiers

| Dossier | Responsabilité |
|---|---|
| `app/` | Configuration globale, authentification, providers, routage et client HTTP |
| `assets/` | Images, illustrations et ressources statiques |
| `components/ui/` | Composants UI génériques issus du template ou personnalisés |
| `components/shared/` | Composants partagés entre plusieurs fonctionnalités |
| `features/` | Fonctionnalités métier organisées par domaine |
| `layouts/` | Structures générales des pages |
| `hooks/` | Hooks transversaux non spécifiques à un domaine |
| `icons/` | Icônes et composants d'icônes |
| `i18n/` | Configuration de l'internationalisation |
| `messages/` | Fichiers de traduction |
| `utils/` | Fonctions utilitaires transversales |

Un fichier doit être placé dans le dossier correspondant à sa responsabilité réelle.

Il ne faut pas créer de nouveaux dossiers globaux pour des éléments qui appartiennent clairement à une fonctionnalité métier.

---

## 4. Architecture des fonctionnalités

Chaque domaine métier doit être organisé dans un dossier indépendant sous `src/features/`.

### 4.1. Structure standard d'une fonctionnalité

```text
features/
└── campaigns/
    ├── api.ts
    ├── types.ts
    ├── index.ts
    │
    ├── components/
    │   ├── campaign-table.tsx
    │   ├── campaign-form.tsx
    │   └── campaign-card.tsx
    │
    ├── hooks/
    │   ├── use-campaigns.ts
    │   └── use-campaign.ts
    │
    ├── pages/
    │   ├── campaigns-page.tsx
    │   └── campaign-details-page.tsx
    │
    └── mocks/
        └── campaigns.mock.ts
```

Tous les sous-dossiers ne sont pas obligatoires.

Ils doivent être créés uniquement lorsqu'ils sont nécessaires.

### 4.2. Rôle des fichiers

| Élément | Responsabilité |
|---|---|
| `api.ts` | Communication avec le backend et accès aux données |
| `types.ts` | Types, interfaces et contrats propres au domaine |
| `hooks/` | Logique métier, chargement et gestion des états |
| `pages/` | Composition des écrans et coordination des composants |
| `components/` | Présentation et interactions locales |
| `mocks/` | Données fictives utilisées en mode mock |
| `index.ts` | Exports publics de la fonctionnalité |

### 4.3. Principe fondamental

Le flux de données doit respecter l'organisation suivante :

```text
Backend
   ↓
api.ts
   ↓
Hooks
   ↓
Pages
   ↓
Components
```

Les composants ne doivent pas accéder directement au backend.

Les pages ne doivent pas contenir les appels HTTP ni implémenter la logique métier.

Les hooks ne doivent pas gérer la présentation détaillée des composants.

Chaque couche doit rester indépendante autant que possible.

---

## 5. Conventions de communication avec le backend

### 5.1. Centralisation des requêtes

Toutes les requêtes HTTP doivent être centralisées dans le fichier `api.ts` de la fonctionnalité concernée.

Exemple :

```ts
// features/campaigns/api.ts

import { apiClient } from "@/app/api-client";
import type {
  Campaign,
  CreateCampaignPayload,
  UpdateCampaignPayload,
} from "./types";

export async function getCampaigns(): Promise<Campaign[]> {
  return apiClient.get<Campaign[]>("/campaigns");
}

export async function getCampaignById(
  id: string,
): Promise<Campaign> {
  return apiClient.get<Campaign>(`/campaigns/${id}`);
}

export async function createCampaign(
  payload: CreateCampaignPayload,
): Promise<Campaign> {
  return apiClient.post<Campaign>("/campaigns", payload);
}

export async function updateCampaign(
  id: string,
  payload: UpdateCampaignPayload,
): Promise<Campaign> {
  return apiClient.patch<Campaign>(
    `/campaigns/${id}`,
    payload,
  );
}
```

Les noms et méthodes HTTP doivent naturellement correspondre aux véritables endpoints du backend.

### 5.2. Une fonction par opération

Chaque fonction de `api.ts` doit représenter une opération identifiable du backend.

Exemples :

- `getCampaigns()`
- `getCampaignById(id)`
- `createCampaign(payload)`
- `updateCampaign(id, payload)`
- `publishCampaign(id)`
- `closeCampaign(id)`

Il faut éviter les fonctions génériques qui regroupent plusieurs opérations métier sans justification.

### 5.3. Utilisation du client HTTP commun

Toutes les requêtes doivent passer par le client HTTP centralisé dans `app/api-client.ts`.

Il est interdit de créer un client HTTP indépendant dans une fonctionnalité ou d'utiliser directement `fetch()` dans les composants, les pages ou les hooks.

Le client commun est responsable notamment :

- de la construction des URL ;
- de la gestion des cookies et des informations d'authentification ;
- de la sérialisation des données ;
- de la gestion des réponses HTTP ;
- de la remontée des erreurs.

Les comportements communs doivent être modifiés dans le client centralisé plutôt que dupliqués dans chaque fonctionnalité.

### 5.4. Respect du contrat backend

Les requêtes et les réponses doivent respecter les schémas réellement exposés par l'API.

Il est interdit de :

- inventer un endpoint ;
- inventer un champ de réponse ;
- modifier arbitrairement le nom d'un champ backend ;
- supposer qu'une opération existe sans vérifier le routeur backend ;
- utiliser des données fictives pour masquer une erreur API.

Si une fonctionnalité n'est pas encore disponible dans le backend, elle doit être explicitement identifiée comme non connectée.

### 5.5. Transformation des données

Si les données du backend doivent être adaptées pour l'affichage, cette transformation doit être effectuée dans le hook ou dans une fonction dédiée.

Elle ne doit pas être répétée dans plusieurs composants.

Les types correspondant aux réponses API doivent rester distincts des types de présentation lorsque leurs structures diffèrent.

---

## 6. Conventions TypeScript

### 6.1. Typage obligatoire

TypeScript doit être utilisé de manière stricte.

Il faut typer :

- les paramètres des fonctions ;
- les valeurs de retour ;
- les props des composants ;
- les états React lorsque leur type n'est pas déductible ;
- les données provenant de l'API ;
- les objets transmis entre les différentes couches.

Il faut éviter les types implicites lorsque ceux-ci rendent le code ambigu.

### 6.2. Éviter `any`

L'utilisation de `any` est interdite sauf cas exceptionnel dûment justifié.

Préférer :

- `unknown` lorsqu'une donnée est réellement inconnue ;
- des interfaces et types précis ;
- les unions discriminées lorsque plusieurs formes de données sont possibles ;
- les génériques pour les fonctions réutilisables.

Les données de type `unknown` doivent être vérifiées avant leur utilisation.

### 6.3. Séparer les types métier et les types de présentation

Un type représentant une entité backend ne doit pas être modifié uniquement pour satisfaire les besoins d'un composant.

Exemple :

```ts
// types.ts

export interface Campaign {
  id_campaign: string;
  title: string;
  description: string;
  goal: number | null;
  status: string;
}
```

Si un tableau a besoin de propriétés supplémentaires pour gérer les actions disponibles, créer un type de présentation distinct :

```ts
// Dans le composant ou dans un fichier de types dédié.

type CampaignRow = Campaign & {
  canPublish: boolean;
  canClose: boolean;
};
```

Puis utiliser ce type dans les colonnes :

```ts
const columns: Column<CampaignRow>[] = [
  // ...
];
```

Les propriétés `canPublish` et `canClose` ne doivent pas être ajoutées artificiellement au type `Campaign` si elles ne font pas partie du contrat métier.

### 6.4. Interfaces et types

Utiliser :

- `interface` pour les structures d'objets extensibles ;
- `type` pour les unions, intersections, alias et types dérivés.

Exemples :

```ts
export interface Campaign {
  id_campaign: string;
  title: string;
}

export type CampaignStatus =
  | "draft"
  | "published"
  | "closed";

export type CampaignRow = Campaign & {
  canPublish: boolean;
};
```

### 6.5. Typage des props

Les props doivent être explicitement typées.

Exemple :

```tsx
interface CampaignCardProps {
  campaign: Campaign;
  onSelect: (id: string) => void;
}

export function CampaignCard({
  campaign,
  onSelect,
}: CampaignCardProps) {
  return (
    <button onClick={() => onSelect(campaign.id_campaign)}>
      {campaign.title}
    </button>
  );
}
```

Éviter les objets de props anonymes trop complexes lorsque le composant possède plusieurs propriétés.

---

## 7. Hooks et logique métier

### 7.1. Responsabilité des hooks

Les hooks spécifiques à une fonctionnalité doivent être placés dans son dossier `hooks/`.

Ils sont responsables notamment :

- du chargement des données ;
- de la gestion des états de chargement ;
- de la gestion des erreurs ;
- de l'exécution des opérations métier ;
- de la mise à jour des données après une opération ;
- de la préparation des données destinées à l'affichage.

### 7.2. Exemple de hook

```ts
// features/campaigns/hooks/use-campaigns.ts

import { useCallback, useEffect, useState } from "react";
import * as campaignApi from "../api";
import type { Campaign } from "../types";

export function useCampaigns() {
  const [rows, setRows] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await campaignApi.getCampaigns();
      setRows(data);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Une erreur est survenue.",
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  return {
    rows,
    loading,
    error,
    reload,
  };
}
```

Cet exemple doit être adapté au contrat réel de l'API et aux besoins du module.

### 7.3. Règles concernant les hooks

- Un hook personnalisé doit commencer par `use`.
- Un hook doit avoir une responsabilité identifiable.
- Les appels API doivent provenir de `api.ts`.
- Les hooks doivent gérer proprement les erreurs asynchrones.
- Les états doivent être initialisés avec des valeurs cohérentes.
- Les dépendances de `useEffect`, `useCallback` et `useMemo` doivent être correctement déclarées.
- Il ne faut pas désactiver les règles React Hooks pour contourner un problème.
- Les opérations déclenchées par une action utilisateur doivent être exécutées dans un gestionnaire adapté, et non automatiquement dans un effet.

Les hooks globaux sont réservés aux besoins réellement transversaux.

---

## 8. Pages et composants

### 8.1. Pages

Les pages sont placées dans `features/<feature>/pages/`.

Elles doivent :

- utiliser les hooks nécessaires ;
- coordonner les composants de la fonctionnalité ;
- gérer les interactions au niveau de l'écran ;
- transmettre les données et les callbacks aux composants ;
- gérer les états globaux de la page lorsque cela est nécessaire.

Elles ne doivent pas :

- effectuer directement des requêtes HTTP ;
- contenir des règles métier complexes ;
- dupliquer la logique déjà présente dans les hooks ;
- contenir des composants volumineux qui devraient être extraits.

### 8.2. Composants métier

Les composants spécifiques à une fonctionnalité doivent être placés dans `features/<feature>/components/`.

Ils doivent être principalement présentatifs.

Exemple :

```tsx
interface CampaignTableProps {
  rows: CampaignRow[];
  loading: boolean;
  onPublish: (id: string) => void;
  onClose: (id: string) => void;
}

export function CampaignTable({
  rows,
  loading,
  onPublish,
  onClose,
}: CampaignTableProps) {
  // Affichage et interactions transmises par les props.
}
```

Un composant ne doit pas appeler directement `api.ts`.

Il reçoit les données et les callbacks nécessaires par ses props.

### 8.3. Composants partagés

Les composants réutilisables entre plusieurs fonctionnalités doivent être placés dans `components/shared/`.

Exemples :

- tableaux génériques ;
- en-têtes de page ;
- panneaux de données ;
- indicateurs de statut ;
- composants de pagination ;
- états vides ;
- messages d'erreur.

Un composant ne doit être déplacé dans `shared/` que s'il répond à un véritable besoin de réutilisation.

### 8.4. Composants UI génériques

Les composants de base sont placés dans `components/ui/`.

Exemples :

- Button ;
- Input ;
- Checkbox ;
- Select ;
- Dialog ;
- Badge ;
- Table ;
- Tooltip.

Ces composants doivent rester indépendants du domaine métier.

Ils ne doivent pas contenir de logique spécifique aux campagnes, aux dons, à la trésorerie ou aux autres modules.

### 8.5. Personnalisation des composants

Lorsqu'un composant générique ne répond pas exactement au besoin d'une fonctionnalité :

1. conserver le composant générique ;
2. créer un composant métier dans la fonctionnalité concernée ;
3. utiliser le composant générique comme base ;
4. transmettre les données et les callbacks nécessaires.

Il ne faut pas dupliquer entièrement un composant générique uniquement pour modifier son apparence ou son comportement local.

---

## 9. Gestion des données fictives (Mock)

### 9.1. Organisation

Les données fictives doivent être placées dans :

```text
features/
└── campaigns/
    └── mocks/
        └── campaigns.mock.ts
```

### 9.2. Règles

Les fichiers `mocks/` doivent contenir uniquement des données fictives sous forme d'objets, de tableaux ou de constantes simples.

Ils ne doivent contenir :

- aucun appel API ;
- aucune logique métier ;
- aucun hook React ;
- aucun composant ;
- aucune manipulation du DOM.

Les données fictives doivent être consommées exclusivement par le fichier `api.ts` de leur fonctionnalité.

Exemple :

```ts
// features/campaigns/mocks/campaigns.mock.ts

import type { Campaign } from "../types";

export const mockCampaigns: Campaign[] = [
  {
    id_campaign: "CMP-001",
    title: "Solidarité hivernale",
    description: "Campagne de collecte hivernale.",
    goal: 1500000,
    status: "published",
  },
];
```

### 9.3. Séparation du mode Mock et du mode API

Chaque fonctionnalité doit gérer son propre mode de données.

Il ne faut pas créer un indicateur global `isStatic` qui modifierait simultanément le comportement de tous les modules.

Le choix du mode doit être explicite dans le fichier `api.ts` de chaque fonctionnalité.

Exemple conceptuel :

```ts
const USE_MOCK = false;

export async function getCampaigns(): Promise<Campaign[]> {
  if (USE_MOCK) {
    return mockCampaigns;
  }

  return apiClient.get<Campaign[]>("/campaigns");
}
```

Le mode Mock ne doit jamais être activé automatiquement à la suite d'une erreur API.

Une erreur réseau, une erreur serveur ou une réponse invalide doit rester visible comme une erreur.

---

## 10. Authentification et autorisations

### 10.1. Authentification

L'authentification est centralisée dans `app/auth/` et dans la fonctionnalité `features/auth/`.

Elle doit notamment gérer :

- la connexion ;
- la récupération de la session ;
- la déconnexion ;
- la vérification de l'utilisateur connecté ;
- la récupération des rôles actifs ;
- la protection des routes.

Le frontend utilise le mécanisme d'authentification défini par le backend.

Lorsque celui-ci utilise un cookie HttpOnly, le frontend ne doit pas tenter de lire ou de stocker directement le jeton dans `localStorage` ou `sessionStorage`.

Les requêtes doivent utiliser le client HTTP commun configuré pour transmettre les cookies.

### 10.2. Protection des routes

La protection des routes doit être centralisée.

Les composants de protection doivent distinguer :

- un utilisateur non authentifié ;
- un utilisateur authentifié sans rôle autorisé ;
- un utilisateur authentifié avec un rôle autorisé.

Un utilisateur non authentifié doit être redirigé vers la page de connexion.

Un utilisateur authentifié sans permission doit être redirigé vers une page d'accès refusé ou vers l'espace public selon le comportement défini par l'application.

### 10.3. Gestion des rôles

Les rôles et permissions doivent être centralisés dans `app/auth/permissions.ts`.

Les rôles autorisés pour le back-office sont :

- `Administrator`
- `Collection_Manager`
- `Stock_Manager`
- `Treasurer`

Le rôle `Volunteer` ne fait pas partie des rôles autorisés par le guard actuel.

Les permissions doivent être vérifiées à deux niveaux :

1. au niveau du routage ;
2. au niveau des actions disponibles dans l'interface.

Masquer un bouton ne constitue pas une protection de sécurité. Le backend reste responsable de l'autorisation réelle de chaque opération.

Il est interdit de disperser des comparaisons de rôles arbitraires dans plusieurs composants.

---

## 11. Gestion des états et des erreurs

### 11.1. États de chargement

Toute opération asynchrone doit prévoir un état de chargement lorsque celui-ci est pertinent.

Exemples :

- `loading` pour le chargement initial ;
- `submitting` pour une soumission de formulaire ;
- `isUpdating` pour une opération de modification.

Les boutons déclenchant une opération doivent empêcher les soumissions répétées lorsque cela est nécessaire.

### 11.2. Gestion des erreurs

Les erreurs doivent être traitées à proximité de l'opération qui les déclenche.

Les hooks doivent transmettre une information exploitable par les pages.

Les pages doivent afficher un message compréhensible par l'utilisateur.

Il faut éviter :

- les erreurs silencieusement ignorées ;
- les `catch` vides ;
- les messages techniques bruts affichés directement à l'utilisateur ;
- les notifications de succès affichées avant la confirmation de l'opération par le backend.

### 11.3. États d'interface à prévoir

Lorsqu'ils sont pertinents, les écrans doivent gérer :

- le chargement ;
- les données disponibles ;
- l'absence de données ;
- les erreurs ;
- l'accès refusé ;
- les opérations en cours.

Un écran ne doit pas rester vide lorsqu'une requête échoue.

---

## 12. Conventions de nommage

Les noms doivent être explicites, cohérents et en anglais dans le code.

| Élément | Convention | Exemple |
|---|---|---|
| Dossiers | kebab-case | `campaigns/` |
| Fichiers React | kebab-case | `campaign-table.tsx` |
| Fichiers TypeScript | kebab-case | `use-campaigns.ts` |
| Composants React | PascalCase | `CampaignTable` |
| Interfaces et types | PascalCase | `CampaignPayload` |
| Fonctions | camelCase | `getCampaigns` |
| Variables | camelCase | `campaignRows` |
| Constantes | UPPER_SNAKE_CASE | `BACKOFFICE_ROLES` |
| Hooks | `use` + camelCase | `useCampaigns` |
| Enums ou unions | PascalCase | `CampaignStatus` |

Les noms doivent décrire clairement la responsabilité de l'élément.

Éviter les noms trop génériques tels que :

- `data`
- `item`
- `handle`
- `response`
- `temp`
- `value`

lorsqu'un nom métier plus précis est possible.

---

## 13. Conventions d'importation

### 13.1. Alias `@`

L'alias `@` doit être utilisé pour les imports provenant d'autres dossiers ou couches du projet.

Exemple :

```ts
import { Button } from "@/components/ui/button";
import { useCampaigns } from "@/features/campaigns/hooks/use-campaigns";
```

### 13.2. Imports relatifs

Les imports relatifs sont réservés aux fichiers du même niveau ou de la même fonctionnalité lorsque cela améliore la lisibilité.

Exemple :

```ts
import type { Campaign } from "../types";
import { getCampaigns } from "../api";
```

Éviter les chemins relatifs longs et difficiles à maintenir.

### 13.3. Imports de types

Utiliser `import type` lorsqu'un import sert uniquement au typage.

Exemple :

```ts
import type { Campaign } from "./types";
```

Cela permet de distinguer clairement les dépendances utilisées à l'exécution des dépendances utilisées uniquement par TypeScript.

### 13.4. Nettoyage

Tout import inutilisé doit être supprimé.

Les imports non utilisés provoquent des erreurs lorsque les règles TypeScript ou ESLint correspondantes sont activées.

---

## 14. Conventions React

### 14.1. Composants fonctionnels

Tous les composants doivent être écrits sous forme de composants fonctionnels React.

Éviter les composants de classe pour les nouveaux développements.

### 14.2. Hooks React

Les hooks React doivent respecter les règles officielles :

- les appeler uniquement au niveau supérieur d'un composant ou d'un hook personnalisé ;
- ne jamais les appeler dans une condition, une boucle ou une fonction imbriquée ;
- respecter l'ordre d'appel des hooks ;
- déclarer correctement les dépendances des effets.

### 14.3. Gestion des effets

`useEffect` doit être utilisé uniquement lorsqu'un effet secondaire est réellement nécessaire.

Ne pas utiliser `useEffect` pour :

- calculer une valeur dérivée ;
- synchroniser deux états qui pourraient être évités ;
- exécuter une opération qui devrait être déclenchée par un événement utilisateur.

Préférer une variable calculée ou `useMemo` lorsque cela est pertinent.

### 14.4. État local et état partagé

Utiliser `useState` pour les états locaux d'un composant ou d'une page.

Utiliser Context uniquement lorsque plusieurs composants ont réellement besoin d'un même état global.

Éviter de remonter inutilement des états vers des composants parents éloignés.

### 14.5. Clés React

Toute liste rendue avec `map()` doit posséder une clé stable et unique.

Exemple :

```tsx
{campaigns.map((campaign) => (
  <CampaignCard
    key={campaign.id_campaign}
    campaign={campaign}
  />
))}
```

Éviter l'utilisation de l'index comme clé lorsque les éléments peuvent être ajoutés, supprimés ou réordonnés.

---

## 15. Formulaires et validation

Les formulaires doivent être contrôlés et validés avant l'envoi.

Pour les formulaires simples, les hooks React peuvent suffire.

Pour les formulaires complexes, utiliser React Hook Form et Zod lorsque cela apporte une réelle valeur.

Les règles à respecter :

- définir des types précis pour les données du formulaire ;
- valider les champs obligatoires ;
- vérifier les formats et contraintes métier ;
- afficher les erreurs près des champs concernés ;
- désactiver le bouton pendant une soumission en cours ;
- ne pas envoyer les champs non autorisés ;
- respecter exactement le schéma attendu par le backend.

Les données envoyées doivent être préparées dans la couche appropriée et non construites directement dans un composant de présentation.

---

## 16. Styles et interface utilisateur

### 16.1. Tailwind CSS

Tailwind CSS est la solution de stylisation principale.

Les classes doivent rester lisibles et cohérentes avec les conventions du projet.

Éviter de multiplier les styles inline lorsque des classes Tailwind peuvent être utilisées.

### 16.2. Cohérence visuelle

Les nouveaux écrans doivent respecter le système visuel existant :

- palette de couleurs ;
- typographie ;
- espacements ;
- bordures ;
- rayons ;
- ombres ;
- états de survol ;
- états actifs ;
- responsive design ;
- thème clair et sombre.

Il faut privilégier les composants UI existants plutôt que de recréer des éléments déjà disponibles.

### 16.3. Responsive design

Tous les écrans doivent rester utilisables sur :

- desktop ;
- tablette ;
- mobile.

Les tableaux, formulaires, menus et panneaux doivent être adaptés aux petits écrans.

### 16.4. Accessibilité

Les composants interactifs doivent être accessibles :

- utiliser des éléments HTML sémantiquement adaptés ;
- associer les labels aux champs ;
- fournir des textes alternatifs aux images pertinentes ;
- conserver un contraste suffisant ;
- rendre les interactions accessibles au clavier ;
- utiliser les attributs ARIA lorsque nécessaire.

---

## 17. Internationalisation

Le projet utilise i18next et react-i18next.

Les langues disponibles sont :

- anglais (`en`) ;
- français (`fr`) ;
- arabe (`ar`).

L'arabe doit conserver la prise en charge RTL.

Les textes visibles par l'utilisateur doivent être externalisés dans les fichiers de traduction.

Exemple :

```tsx
import { useTranslation } from "react-i18next";

export function CampaignHeading() {
  const { t } = useTranslation();

  return <h1>{t("campaigns.title")}</h1>;
}
```

Éviter de coder en dur les textes dans les composants lorsqu'ils doivent être traduits.

Les clés de traduction doivent être explicites et organisées par domaine.

Toute nouvelle fonctionnalité doit ajouter les traductions nécessaires dans les langues prises en charge, ou signaler clairement les traductions encore manquantes.

---

## 18. Configuration et variables d'environnement

Les variables d'environnement doivent être centralisées dans la configuration de l'application.

Les variables exposées au frontend Vite doivent utiliser le préfixe `VITE_`.

Exemple :

```env
VITE_API_URL=
VITE_PUBLIC_URL=http://localhost:5173
```

Les valeurs par défaut doivent être définies de manière cohérente dans `app/config.ts`.

Règles :

- ne jamais coder en dur une URL d'environnement dans une fonctionnalité ;
- ne jamais exposer de secret dans une variable `VITE_` ;
- documenter les nouvelles variables dans `.env.example` ;
- ne jamais versionner un fichier `.env` contenant des informations sensibles ;
- vérifier la configuration avant le déploiement.

---

## 19. Gestion des routes

Les routes doivent être centralisées dans `app/router/`.

Les règles d'accès doivent être définies à l'aide des guards et du système de permissions centralisé.

Les pages doivent être importées depuis les exports publics des fonctionnalités lorsque cela est pertinent.

Exemple :

```ts
import { CampaignsPage } from "@/features/campaigns";
```

Éviter de déclarer les mêmes routes dans plusieurs endroits.

Toute nouvelle route doit être associée à :

- une page existante ;
- une règle d'accès ;
- une permission appropriée ;
- un comportement cohérent en cas d'accès refusé.

---

## 20. Utilitaires transversaux

Les fonctions réellement réutilisables entre plusieurs fonctionnalités doivent être placées dans `utils/`.

Exemples :

- formatage des dates ;
- formatage des montants ;
- normalisation de chaînes ;
- fonctions de conversion ;
- helpers de validation génériques.

Une fonction spécifique à une fonctionnalité doit rester dans cette fonctionnalité.

Il faut éviter de transformer `utils/` en dossier contenant toute la logique non classée.

---

## 21. Qualité du code et bonnes pratiques

Les règles suivantes sont obligatoires :

1. Respecter la séparation des responsabilités.
2. Éviter les duplications de code.
3. Préférer les fonctions courtes avec une responsabilité claire.
4. Utiliser des noms explicites.
5. Éviter les composants trop volumineux.
6. Éviter les conditions imbriquées excessives.
7. Ne pas laisser de code mort ou commenté inutilement.
8. Supprimer les imports et variables inutilisés.
9. Ne pas utiliser `any` sans justification.
10. Ne pas contourner les erreurs TypeScript avec `@ts-ignore`.
11. Ne pas désactiver les règles ESLint ou React Hooks pour faire passer le build.
12. Ne pas mélanger les données fictives et les données réelles.
13. Ne pas dupliquer les appels API.
14. Ne pas introduire de dépendance supplémentaire sans nécessité.
15. Ne pas modifier le contrat backend pour simplifier arbitrairement le frontend.
16. Ne pas ajouter de logique métier dans les composants UI génériques.

### 21.1. Gestion des commentaires

Les commentaires doivent expliquer une décision ou une règle difficile à comprendre.

Ils ne doivent pas simplement répéter le code.

Préférer du code explicite à des commentaires nombreux.

---

## 22. Vérifications avant validation du code

Avant chaque commit, les vérifications suivantes doivent être effectuées depuis `frontend-admin/`.

### 22.1. Build

```bash
npm run build
```

Le build doit se terminer sans erreur TypeScript ni erreur Vite.

### 22.2. Lint

```bash
npm run lint
```

Les erreurs de lint doivent être corrigées.

Les avertissements doivent être examinés et résolus lorsqu'ils révèlent un problème de qualité ou de maintenabilité.

### 22.3. Formatage

```bash
npm run format
```

Le code doit respecter le formatage utilisé dans le projet.

### 22.4. Vérification fonctionnelle

Après les vérifications statiques, tester les écrans concernés :

- affichage initial ;
- chargement des données ;
- état vide ;
- gestion des erreurs ;
- formulaires ;
- actions utilisateur ;
- navigation ;
- permissions ;
- responsive design ;
- thème clair et sombre lorsque concerné.

Le build seul ne garantit pas le bon fonctionnement d'une fonctionnalité.

---

## 24. Checklist pour toute nouvelle fonctionnalité

Avant de considérer une fonctionnalité comme terminée, vérifier les points suivants :

### Architecture

- [ ] La fonctionnalité est organisée dans `features/<domain>/`.
- [ ] Les fichiers sont placés dans les bons sous-dossiers.
- [ ] Les responsabilités API, hooks, pages et composants sont séparées.
- [ ] Les types sont centralisés dans `types.ts` lorsque nécessaire.
- [ ] Les exports publics sont mis à jour si nécessaire.

### Backend et données

- [ ] Les endpoints existent réellement dans le backend.
- [ ] Les requêtes sont définies dans `api.ts`.
- [ ] Les appels utilisent le client HTTP commun.
- [ ] Les contrats de requête et de réponse sont respectés.
- [ ] Les mocks sont isolés dans `mocks/`.

### React et TypeScript

- [ ] Les composants possèdent des props typées.
- [ ] Les hooks respectent les règles React.
- [ ] Aucun import inutilisé ne subsiste.
- [ ] Aucun `any` injustifié n'est utilisé.
- [ ] Les listes utilisent des clés stables.
- [ ] Les erreurs asynchrones sont gérées.

### Interface et permissions

- [ ] Les états de chargement, d'erreur et d'absence de données sont traités.
- [ ] Les composants UI existants sont réutilisés.
- [ ] L'affichage est responsive.
- [ ] Les rôles et permissions sont respectés.
- [ ] Les traductions nécessaires sont ajoutées.
- [ ] Les formulaires sont validés.

### Validation finale

- [ ] `npm run build` réussit.
- [ ] `npm run lint` réussit.
- [ ] `npm run format` a été exécuté.
- [ ] Les parcours fonctionnels concernés ont été testés.
- [ ] Le commit est cohérent et correctement nommé.

---

## 25. Principe général

L'objectif de cette architecture est de maintenir un frontend modulaire, prévisible et facile à faire évoluer.

Chaque fonctionnalité doit pouvoir être développée, corrigée et testée indépendamment des autres domaines, tout en respectant les composants, les services transversaux et les règles communes de l'application.

**En cas de doute, privilégier la séparation des responsabilités, la réutilisation du code existant, le respect du contrat backend et la simplicité de l'implémentation.**