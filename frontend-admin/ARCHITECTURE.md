# Architecture du frontend-admin MARVEL

## Organisation

- `app/` : composition de l’application, providers globaux et configuration du routeur.
- `assets/` : ressources statiques importées par Vite (images et favicon).
- `components/ui/` : primitives UI réutilisables issues de la base TailAdmin.
- `components/shared/` : composants transversaux partagés entre plusieurs fonctionnalités.
- `features/` : fonctionnalités métier organisées par domaine.
- `layouts/` : structures de page, dont le layout administrateur et sa navigation.
- `i18n/` et `messages/` : configuration et ressources de traduction.
- `hooks/`, `icons/`, `utils/` : utilitaires transversaux.

## Fonctionnalités présentes

- `features/dashboard` : page d’accueil de l’administration MARVEL.
- `features/profile` : profil et sections associées, conservés depuis le template.
- `features/errors` : page 404.

## Internationalisation

Les langues disponibles sont l’anglais (`en`), le français (`fr`) et l’arabe (`ar`). L’arabe conserve la prise en charge RTL existante. Le français contient les traductions des zones actuellement exposées ; les espaces de démonstration non utilisés restent en fallback anglais et seront traduits lors de leur éventuelle réintroduction.

## Assets

Le contenu du dossier `public/` a été supprimé (sauf favicon.png). Les images encore utilisées par les écrans conservés sont dans `src/assets/` et importées explicitement afin que Vite les traite pendant le build. Les ressources de démonstration non référencées ont été écartées.
