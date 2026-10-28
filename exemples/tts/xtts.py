import os, sys, time
# L'utilisateur a accepté la licence CPML (usage non commercial).
os.environ["COQUI_TOS_AGREED"] = "1"
from TTS.api import TTS

out = sys.argv[1]
text = "Bonjour, je suis Nicolas, et je parle pour faire un test."
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
for spk in ["Damien Black", "Viktor Menelaos", "Andrew Chipper", "Zacharie Aimilios"]:
    t = time.time()
    tts.tts_to_file(text=text, speaker=spk, language="fr",
                    file_path=f"{out}/xtts_{spk.split()[0].lower()}.wav")
    print(spk, round(time.time() - t, 1), "s", flush=True)
