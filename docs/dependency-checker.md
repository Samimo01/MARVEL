# Python Dependency Checker

## 1. Présentation

Le Python Dependency Checker est un workflow GitHub Actions permettant de surveiller automatiquement les dépendances Python du backend de MARVEL.

Son objectif est de renforcer la sécurité du projet et de faciliter la maintenance des bibliothèques utilisées.

Il effectue deux contrôles principaux :

- **Détection des vulnérabilités :** identifier les dépendances présentant des vulnérabilités de sécurité connues.
- **Détection des mises à jour :** identifier les dépendances pour lesquelles une version plus récente est disponible.

## 2. Technologies utilisées

| Outil | Rôle |
|---|---|
| Python 3.12 | Environnement d'exécution |
| pip | Installation et gestion des dépendances |
| pip-audit | Détection des vulnérabilités connues |
| pip list --outdated | Détection des versions obsolètes |
| GitHub Actions | Automatisation des vérifications |

## 3. Fonctionnement

Le workflow est défini dans :

`.github/workflows/dependency-checker.yml`

Il analyse les dépendances déclarées dans :

`backend/requirements.txt`

Les différentes étapes sont :

1. Récupération du code source avec `actions/checkout`.
2. Configuration de Python 3.12.
3. Installation des dépendances du backend.
4. Recherche des versions plus récentes avec `pip list --outdated`.
5. Installation de `pip-audit`.
6. Audit de sécurité avec `pip-audit`.

## 4. Déclenchement automatique

Le workflow peut être déclenché de quatre manières :

| Événement | Condition |
|---|---|
| Push | Modification de `backend/requirements.txt` ou du workflow |
| Pull Request | Modification de l'un de ces deux fichiers |
| Schedule | Tous les lundis à 03h00 UTC |
| Manuel | Depuis l'onglet Actions de GitHub avec Run workflow |

**Remarque :** le déclenchement planifié utilise l'heure UTC et s'exécute sur la branche par défaut du dépôt. Le workflow doit donc être intégré à cette branche pour bénéficier de la vérification hebdomadaire.

## 5. Gestion des résultats

### 5.1 Dépendances obsolètes

La commande :

`python -m pip list --outdated --format=columns`

affiche les packages installés pour lesquels une version plus récente est disponible.

Cette vérification est informative : elle ne met pas automatiquement les dépendances à jour et ne fait pas échouer le workflow lorsqu'une mise à jour est disponible.

### 5.2 Vulnérabilités de sécurité

La commande :

`pip-audit -r backend/requirements.txt`

analyse les dépendances déclarées et leurs versions résolues afin de détecter les vulnérabilités connues.

Si une vulnérabilité est détectée, l'audit retourne une erreur et le job échoue.

## 6. Consultation des résultats

Pour consulter les résultats :

1. Accéder au dépôt GitHub MARVEL.
2. Ouvrir l'onglet **Actions**.
3. Sélectionner **Python Dependency Checker**.
4. Ouvrir une exécution.
5. Consulter les étapes **Check outdated dependencies** et **Security audit**.

Les résultats permettent de connaître les mises à jour disponibles et les éventuelles vulnérabilités détectées.

## 7. Localisation des fichiers

- Workflow : `.github/workflows/dependency-checker.yml`
- Dépendances analysées : `backend/requirements.txt`
- Documentation : `docs/dependency-checker.md`

## 8. Limites actuelles

- Le workflow détecte les mises à jour, mais ne les installe pas automatiquement dans le projet.
- L'audit dépend des bases de données de vulnérabilités disponibles.
- Une exécution réussie ne signifie pas nécessairement que toutes les dépendances sont à jour.
- Les résultats doivent être examinés avant toute mise à jour des dépendances.

## 9. Conclusion

Le Python Dependency Checker contribue à améliorer la sécurité et la maintenabilité du backend MARVEL grâce à une surveillance automatisée des dépendances Python via GitHub Actions.