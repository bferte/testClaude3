# L'Atolien, galerie 3D

- `index.html` : la scène three.js (chargée depuis cdn.jsdelivr.net). À servir en HTTP local, par exemple `python3 -m http.server` dans ce dossier, puis ouvrir http://localhost:8000/.
- `index.html?render` : mode rendu, chaque image est calculée à partir du temps (`window.renderAt(t)`), sans horloge.
- `render.js` : capture Playwright en 1920×1080, 30 i/s (`node render.js full frames`), puis `ffmpeg -framerate 30 -i frames/%05d.jpg ...`.
  Il attend un serveur sur http://127.0.0.1:8765 et sert three.js depuis `node_modules/three` (`npm i three@0.170.0`).
- `images/` : 17 visuels d'articles de L'Atolien. `fonts/` : Inter (licence OFL).
