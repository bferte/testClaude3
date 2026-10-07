import { useEffect, useRef, useState } from "react";
import { timeout, getVocalCalibrationVolume } from "./useVocalPlayer.utils";

import { useAudioSystem } from "@hooks/audio";

/**
 * Manage audio players for vocal test : noise background and numbers audios.
 */
export const useVocalPlayer = () => {
  const audioSystem = useAudioSystem({
    audios: [
      {
        id: "noise",
        url: "/medias/vocal/noise.wav",
        canal: "default",
      },
      ...Array.from({ length: 9 }).map((_, index) => ({
        id: (index + 1).toString(),
        url: `/medias/vocal/${index + 1}.wav`,
        canal: "numbers",
      })),
    ],
    side: "both",
  });

  useEffect(() => {
    audioSystem.setup();
  }, []);

  const currentLoopIdRef = useRef(0);
  const [isPlaying, setIsPlaying] = useState(false);

  return {
    isPlaying,
    /**
     *
     */
    playSequence: async (numbers: [number, number, number], RNB: number) => {
      currentLoopIdRef.current++;
      await playSequence(numbers, RNB, currentLoopIdRef.current);
    },
  };

  /**
   * Noise is played in a loop. Is user is enought fast, we don't need to stop noise.
   * loopId is used to know if user is already on the next sequence.
   */
  async function playSequence(
    numbers: [number, number, number],
    RNB: number,
    loopId: number
  ) {
    const calibrationVolume = getVocalCalibrationVolume();

    const RNB_ADJUSTMENT_FACTOR = 0.3;

    const { noiseVolume, voiceVolume } = calculateVolumes(
      calibrationVolume,
      RNB * RNB_ADJUSTMENT_FACTOR
    );

    audioSystem.setCanalVolume("default", noiseVolume);
    audioSystem.setCanalVolume("numbers", voiceVolume);
    audioSystem.play("noise");

    setIsPlaying(true);

    await timeout(600);

    for (const number of numbers) {
      if (currentLoopIdRef.current !== loopId) return;

      audioSystem.play(number.toString());

      await timeout(1000);
    }

    await timeout(400);

    if (currentLoopIdRef.current === loopId) {
      setIsPlaying(false);
      audioSystem.stop("noise");
    }
  }
};

// Fonction pour convertir dB en volume linéaire
function dBToLinear(dB: number) {
  return Math.pow(10, dB / 20);
}

// Fonction pour convertir volume linéaire en dB
function linearToDB(volume: number) {
  return 20 * Math.log10(volume);
}

function calculateVolumes(calibrationVolumeLinear: number, rsbValue: number) {
  let noiseVolumeLinear = calibrationVolumeLinear; // Volume de base pour le bruit de fond
  let voiceVolumeLinear;

  noiseVolumeLinear = dBToLinear(
    linearToDB(calibrationVolumeLinear) - rsbValue
  );
  voiceVolumeLinear = dBToLinear(
    linearToDB(calibrationVolumeLinear) + rsbValue
  );

  return {
    noiseVolume: noiseVolumeLinear,
    voiceVolume: voiceVolumeLinear,
  };
}
