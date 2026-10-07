"use client";

import {
  useRef,
  useState,
  useEffect,
  forwardRef,
  useImperativeHandle,
} from "react";
import { usePathname } from "next/navigation";

import { generateOscillator } from "./AudioGenerator.utils";
import { DebugMessage } from "@ui/common";

/**
 * AudioGenerator component for playing audio.
 * 
 * Usage:
 * ```tsx
 * <AudioGenerator frequency={440} volume={0.5} autoPlay={true} side="left" />
 * ```
 * 
 * The frequency, volume, autoPlay and side props are required.
 * 
 */
export const AudioGenerator = forwardRef(
  (props: AudioGeneratorProps, ref: any) => {
    const oscillatorRef = useRef<OscillatorNode | null>(null);
    const gainRef = useRef<GainNode | null>(null);
    const [state, setState] = useState<"stopped" | "playing">("stopped");
    const [frequency, setFrequency] = useState(props.frequency);
    const [volume, setVolume] = useState(props.volume);

    useEffect(() => {
      if (props.autoPlay) {
        playAudio();
      }

      return () => {
        if (!oscillatorRef.current) return;

        oscillatorRef.current.stop();
      };
    }, []);

    useImperativeHandle(ref, () => {
      return {
        play: () => {
          playAudio();
        },
        stop: () => {
          stopAudio();
        },
        config: (config: Config) => {
          if (config.frequency !== undefined) changeFrequency(config.frequency);
          if (config.volume !== undefined) changeVolume(config.volume);
        },
      };
    });

    const pathname = usePathname();
    const debugMode = pathname.includes("test");

    if (debugMode) return <DebugMessage>{frequency}Hz</DebugMessage>;

    return null;

    function playAudio() {
      const { oscillator, gain } = generateOscillator(
        frequency,
        volume,
        props.side
      );

      oscillatorRef.current = oscillator;
      gainRef.current = gain;
      setState("playing");
    }

    function stopAudio() {
      if (!oscillatorRef.current) return;

      oscillatorRef.current?.stop();
      oscillatorRef.current = null;
      setState("stopped");
    }

    function changeFrequency(frequency: number) {
      setFrequency(frequency);
      if (!oscillatorRef.current) return;

      oscillatorRef.current.frequency.value = frequency;
    }

    function changeVolume(volume: number) {
      setVolume(volume);
      if (!gainRef.current) return;

      gainRef.current.gain.value = volume;
    }
  }
);

AudioGenerator.displayName = "AudioGenerator";

type AudioGeneratorProps = {
  frequency: number;
  volume: number;
  autoPlay?: boolean;
  side: "left" | "right" | "both";
};

export const useAudioGenerator = () => {
  const ref = useRef<{
    play: () => void;
    stop: () => void;
    config: (config: Config) => void;
  }>({
    play: () => undefined,
    stop: () => undefined,
    config: () => undefined,
  });

  return {
    ref,
    play: () => ref.current.play(),
    stop: () => ref.current.stop(),
    config: (config: Config) => ref.current.config(config),
  };
};

type Config = {
  frequency?: number;
  volume?: number;
};
