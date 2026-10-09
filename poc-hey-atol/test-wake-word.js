// Test de la détection sans micro : node poc-hey-atol/test-wake-word.js
const W = require("./wake-word.js");
const oui = ["Hey Atol","hey atoll","Hé Atol !","et atol","eh atole","hey a tôle","Hé, à tol","heyatoll","Hey Atol quels sont vos horaires","bonjour hey atol","Hey attol","hey atall","hay atoll", "et a taule"];
const non = ["et à tout à l'heure","hé à toi","les atolls du pacifique","hôtel","bonjour je voudrais des lunettes","et à Toulouse","atol","Atol les opticiens", "et alors", "elle a tort"];
let ok=true;
for (const t of oui){const r=W.detecter(t); if(!r){ok=false;console.log("RATÉ  ",t)} else console.log("ok    ",t,"->",r.methode,"| suite:",r.suite)}
for (const t of non){const r=W.detecter(t); if(r){ok=false;console.log("FAUX+ ",t,r)} else console.log("ok non",t)}
process.exit(ok?0:1)
