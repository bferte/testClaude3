# Chartes d'enseigne

L'outil lit ses couleurs et polices dans des variables CSS. `../charte.css` est chargé après le style
par défaut et peut les redéfinir ; `../logo.svg`, s'il existe, s'affiche dans l'en-tête.

La charte active (`charte.css`) est la charte Atol reprise de l'artefact « AS3PRO · RA et Gestion des
devis » (`chartes/atol.css`). Vider `charte.css` rend l'apparence neutre d'origine.

Pour passer à la charte d'une autre enseigne :

1. compléter `chartes/<enseigne>.css` avec les valeurs **officielles** du kit de marque ;
2. copier ce fichier dans `charte.css` ;
3. déposer le logo officiel en `logo.svg`.

Variables disponibles : `--accent`, `--accent-ink`, `--ink`, `--muted`, `--bg`, `--panel`, `--line`,
`--warn`, `--good`, `--frame`, `--ramp-0`, `--ramp-1`, `--ramp-2`, `--font-display`, `--font-body`,
`--font-data`. Garder un dégradé `--ramp-*` bien contrasté : c'est lui qui montre les épaisseurs.
