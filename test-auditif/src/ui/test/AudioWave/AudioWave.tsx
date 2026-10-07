import classNameModule from "@classname";
import styles from "./AudioWave.module.scss";
const className = classNameModule(styles);

/**
 * AudioWave component for displaying an audio wave.
 * 
 * Usage:
 * ```tsx
 * <AudioWave />
 * ```
 * 
 * Used in the AudioTest component.
 */
export const AudioWave = () => {
  return (
    <div {...className("AudioWave")}>
      {Array.from({ length: 15 }).map((_, index) => (
        <div
          key={index}
          style={{
            animationDelay: `${index * 0.1}s`,
          }}
        />
      ))}
    </div>
  );
};
