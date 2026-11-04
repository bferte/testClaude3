# Text to speech ElevenLabs

Petite application locale (Streamlit) qui transforme un texte en voix grâce à l'API
[ElevenLabs](https://elevenlabs.io/docs/api-reference/authentication).

## Fonctionnalités
- saisie de la clé API (champ masqué, jamais enregistrée) ou lecture de la variable `ELEVENLABS_API_KEY` ;
- choix de la voix (voix de votre compte), du modèle (par défaut `eleven_multilingual_v2`, adapté au français)
  et du format (MP3 ou PCM) ;
- réglages de stabilité, similarité, style et vitesse ;
- lecture dans le navigateur, téléchargement du fichier, historique de la session.

## Obtenir une clé API
Sur elevenlabs.io : *Profil > API Keys > Create API Key*. La clé est envoyée dans l'en-tête `xi-api-key`.
⚠️ Le texte saisi est envoyé aux serveurs d'ElevenLabs et consomme des crédits de votre compte.

## Lancer
**Windows** : double-cliquer sur `lancer_tts.bat` (le premier lancement installe les composants).
L'appli s'ouvre sur http://localhost:8502.

**Autre** :
```bash
pip install -r requirements.txt
export ELEVENLABS_API_KEY=sk_...   # facultatif
streamlit run app_tts.py --server.port 8502
```

## Tests
```bash
pip install pytest
python -m pytest tests
```
Les tests simulent l'API : ils ne consomment aucun crédit.
