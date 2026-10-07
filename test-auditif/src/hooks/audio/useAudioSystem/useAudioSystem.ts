import { useRef, useState } from "react";

type AudioSystemProps = {
  audios: AudioSystemPropsAudio[];
  side?: "left" | "right" | "both";
};

type AudioSystemPropsAudio = {
  id: string;
  url: string;
  canal: string;
};

type PlayParams = {
  loop?: boolean;
};

/**
 * Audio system hook with multiple audio channels.
 * Each audio is connected to a channel and each channel
 * volume can be controlled individually.
 */
export function useAudioSystem({ audios, side = "both" }: AudioSystemProps) {
  const [isReady, setIsReady] = useState(false);
  const audioContextRef = useRef<AudioContext>();
  const dataRef = useRef<
    Record<
      string,
      {
        canal: string;
        buffer: AudioBuffer;
      }
    >
  >({});

  const playingAudioSourcesRef = useRef<Record<string, AudioBufferSourceNode>>(
    {}
  );

  const gainNodesRef = useRef<Record<string, GainNode>>({});

  return {
    isReady,
    setup,
    play,
    stop,
    setCanalVolume,
    stopAll,
  };

  /**
   *
   */
  function stopAll() {
    for (const audio of Object.values(playingAudioSourcesRef.current)) {
      audio.stop();
    }

    audioContextRef.current?.close();
  }

  /**
   * Load audio buffers and setup gain nodes.
   */
  async function setup() {
    const audioContext = new AudioContext();
    audioContextRef.current = audioContext;

    const gainNodeIds = Array.from(
      new Set(audios.map(({ canal }) => canal))
    ).sort();

    for (const gainNodeId of gainNodeIds) {
      const node = audioContext.createGain();
      node.connect(audioContext.destination);
      gainNodesRef.current[gainNodeId] = node;
    }

    for (const { id, url, canal } of audios) {
      const buffer = await loadAudioBuffer(url);

      dataRef.current[id] = {
        buffer,
        canal,
      };
    }

    setIsReady(true);
  }

  /**
   * Play an audio item from his id. If already playing, it will stop the previous one.
   */
  async function play(id: string, params?: PlayParams) {
    const audioContext = audioContextRef.current;
    if (!audioContext) throw new Error("Please setup");

    if (audioContext.state === "suspended") await audioContext.resume();

    const item = dataRef.current[id];
    if (!item) throw new Error(`No audio found with id: ${id}`);

    if (playingAudioSourcesRef.current[id]) {
      playingAudioSourcesRef.current[id].stop();
      delete playingAudioSourcesRef.current[id];
    }

    const source = createSourceFromBuffer(item.buffer, item.canal);
    if (params?.loop) source.loop = true;
    source.start(0);

    playingAudioSourcesRef.current[id] = source;
  }

  /**
   * Stop playing audio is playing.
   */
  function stop(id: string) {
    const playingAudioSources = playingAudioSourcesRef.current[id];

    if (!playingAudioSources) return;

    if (playingAudioSourcesRef.current[id]) {
      playingAudioSourcesRef.current[id].stop();
      delete playingAudioSourcesRef.current[id];
    }
  }

  /**
   * Create an audio source connected to a gain node.
   */
  function createSourceFromBuffer(buffer: AudioBuffer, canal: string) {
    const audioContext = audioContextRef.current;
    if (!audioContext) throw new Error("Please setup");

    const source = audioContext.createBufferSource();
    source.buffer = buffer;
    source.disconnect();

    const pannerNode = audioContext.createStereoPanner();
    pannerNode.connect(gainNodesRef.current[canal]);

    pannerNode.pan.value = side === "left" ? -1 : side === "right" ? 1 : 0;

    source.connect(pannerNode);
    pannerNode.connect(gainNodesRef.current[canal]);

    return source;
  }

  // Update a canal volume (gain node).
  function setCanalVolume(id: string, volume: number) {
    const gainItem = gainNodesRef.current[id];
    if (!gainItem) throw new Error(`No gain node found with id: ${id}`);
    gainItem.gain.value = Math.pow(volume, 2);
  }

  /**
   * Download audio buffer.
   */
  async function loadAudioBuffer(url: string) {
    const audioContext = audioContextRef.current;

    if (!audioContext) throw new Error("Please setup");

    const response = await fetch(url);
    const arrayBuffer = await response.arrayBuffer();
    return audioContext.decodeAudioData(arrayBuffer);
  }
}
