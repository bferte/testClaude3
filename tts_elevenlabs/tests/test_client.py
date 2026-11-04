import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from elevenlabs_client import ClientElevenLabs, ErreurElevenLabs  # noqa: E402


def reponse(status=200, json_data=None, content=b""):
    r = MagicMock(spec=requests.Response)
    r.status_code, r.ok, r.content, r.text = status, status < 400, content, ""
    r.json.return_value = json_data
    return r


def client_avec(*reponses):
    session = requests.Session()
    session.request = MagicMock(side_effect=list(reponses))
    return ClientElevenLabs("ma-cle", session=session), session


def test_cle_dans_en_tete():
    client, session = client_avec()
    assert session.headers["xi-api-key"] == "ma-cle"


def test_cle_manquante():
    with pytest.raises(ErreurElevenLabs):
        ClientElevenLabs("  ")


def test_liste_des_voix_triee():
    client, _ = client_avec(reponse(json_data={"voices": [
        {"voice_id": "2", "name": "Zoé", "category": "premade", "labels": {"accent": "french"}},
        {"voice_id": "1", "name": "adam"}]}))
    voix = client.voix()
    assert [v.id for v in voix] == ["1", "2"]
    assert voix[1].libelle == "Zoé (french, premade)"


def test_synthese_envoie_le_bon_corps():
    client, session = client_avec(reponse(content=b"ID3audio"))
    audio = client.synthetiser("Bonjour", "voix1", format_sortie="mp3_22050_32", vitesse=1.1)
    assert audio == b"ID3audio"
    methode, url = session.request.call_args.args
    kwargs = session.request.call_args.kwargs
    assert (methode, url) == ("POST", "https://api.elevenlabs.io/v1/text-to-speech/voix1")
    assert kwargs["params"] == {"output_format": "mp3_22050_32"}
    assert kwargs["json"]["text"] == "Bonjour"
    assert kwargs["json"]["voice_settings"]["speed"] == 1.1


def test_texte_vide_refuse_sans_appel():
    client, session = client_avec()
    with pytest.raises(ErreurElevenLabs, match="vide"):
        client.synthetiser("   ", "voix1")
    session.request.assert_not_called()


def test_cle_refusee():
    client, _ = client_avec(reponse(401, {"detail": {"status": "invalid_api_key", "message": "Invalid API key"}}))
    with pytest.raises(ErreurElevenLabs, match="401.*Invalid API key"):
        client.voix()


def test_erreur_reseau():
    client, session = client_avec()
    session.request.side_effect = requests.ConnectionError("hors ligne")
    with pytest.raises(ErreurElevenLabs, match="joindre"):
        client.modeles()
