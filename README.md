# Observatoire des votes structurants

Ce dépôt contient le site statique de l’Observatoire et deux automatisations GitHub :

- **Publication du site** à chaque modification de la branche `main` ;
- **Contrôle hebdomadaire** des scrutins officiels récents de l’Assemblée nationale.

## Mise en ligne initiale

1. Créez un dépôt GitHub public, par exemple `observatoire-votes`.
2. Importez **tout le contenu de ce dossier**, y compris le dossier caché `.github`.
3. Dans le dépôt, ouvrez **Settings → Pages**.
4. Dans **Build and deployment → Source**, choisissez **GitHub Actions**.
5. Ouvrez l’onglet **Actions** et vérifiez que le workflow **Publier le site** est terminé en vert.
6. L’adresse du site apparaît dans **Settings → Pages**.

## Fonctionnement des données

- `index.html` contient le design et le fonctionnement du site.
- `data/db.json` contient les votes et les décomptes par groupe.
- Le navigateur charge automatiquement `data/db.json` lors de l’ouverture du site.

## Ajouter ou modifier un vote

1. Modifiez `data/db.json`.
2. Enregistrez la modification directement sur GitHub avec **Commit changes**.
3. Le workflow vérifie les doublons et les principales incohérences.
4. Si la vérification réussit, GitHub Pages republie le site.

## Contrôle hebdomadaire

Chaque lundi à 8 h 15, heure de Paris :

1. le workflow télécharge le jeu JSON officiel des scrutins de la XVIIe législature ;
2. il examine les dix derniers jours ;
3. il compare ces scrutins à ceux du site ;
4. il produit `reports/new_scrutins.md` et `reports/new_scrutins.json` ;
5. s’il détecte des nouveautés, il crée ou actualise une **Issue GitHub** intitulée
   `[Automatique] Scrutins récents à examiner`.

Le robot ne publie pas automatiquement les nouveaux scrutins : il faut encore valider leur intérêt éditorial, leur thème, leurs sous-thèmes et leur titre pédagogique.

## Lancer le contrôle manuellement

Dans GitHub :

1. ouvrez **Actions** ;
2. choisissez **Contrôle hebdomadaire des scrutins** ;
3. cliquez sur **Run workflow** ;
4. cliquez encore sur **Run workflow** dans le menu.

## Source officielle utilisée

`https://data.assemblee-nationale.fr/static/openData/repository/17/loi/scrutins/Scrutins.json.zip`

## À savoir sur les workflows planifiés

Dans un dépôt public sans activité pendant 60 jours, GitHub peut désactiver automatiquement les workflows planifiés. Une modification ou une réactivation dans l’onglet **Actions** suffit alors à les relancer.
