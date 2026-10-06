#!/usr/bin/env bash
# Génère la voix off (Piper, voix fr-siwis-medium, CC-BY 4.0) et l'assemble avec les images rendues.
# Usage : voix_off.sh <modele.onnx> <dossier_images> <sortie.mp4>
set -euo pipefail
MODEL=$1; FRAMES=$2; OUT=$3; DIR=$(cd "$(dirname "$0")" && pwd); TMP=$(mktemp -d)
STARTS=(0.5 3.6 7.6 12.8 16.85 19.3 25.8 29.6)   # début de chaque phrase (s)
i=0; IN=""; F=""
while IFS= read -r line; do
  echo "$line" | piper -m "$MODEL" --length-scale 0.95 --sentence-silence 0 -f "$TMP/l$i.wav" 2>/dev/null
  ms=$(awk "BEGIN{print int(${STARTS[$i]}*1000)}")
  IN="$IN -i $TMP/l$i.wav"; F="$F[$i:a]aresample=48000,adelay=${ms}|${ms}[a$i];"; i=$((i+1))
done < "$DIR/voix_off.txt"
MIX=$(for j in $(seq 0 $((i-1))); do printf "[a%d]" "$j"; done)
ffmpeg -v error -y $IN -filter_complex "${F}${MIX}amix=inputs=$i:normalize=0,highpass=f=70,acompressor=threshold=-20dB:ratio=3:attack=5:release=120,apad=whole_dur=33.9,loudnorm=I=-16:TP=-1.5:LRA=7" -ac 2 -t 33.9 "$TMP/voix.wav"
ffmpeg -v error -y -framerate 30 -i "$FRAMES/%04d.jpg" -i "$TMP/voix.wav" -c:v libx264 -preset slow -crf 20 -pix_fmt yuv420p -c:a aac -b:a 160k -shortest -movflags +faststart "$OUT"
