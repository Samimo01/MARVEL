# MARVEL — Espace administrateur

Frontend de l’espace d’administration de MARVEL, construit avec React, TypeScript, Vite et Tailwind CSS.

## Prérequis

- Node.js 22.22 ou supérieur
- npm

## Installation

```bash
npm ci
```

## Développement

```bash
npm run dev
```

## Vérifications

```bash
npm run lint
npm run build
```

## Architecture

L’application suit une organisation modulaire par fonctionnalités. Voir [ARCHITECTURE.md](./ARCHITECTURE.md) pour le rôle des dossiers et les conventions de séparation.

## Internationalisation

Langues disponibles : anglais (`en`), français (`fr`) et arabe (`ar`). L’arabe conserve le support de l’affichage RTL.

## Assets

Les ressources statiques utilisées par l’application sont stockées dans `src/assets/` et importées depuis les composants. Le dossier `public/` n’est utilisé que pour favicon.png.
