import classNameModule from "@classname";
import styles from "./Progress.module.scss";
const className = classNameModule(styles);


type ProgressProps = {
  value: number;
  max: number;
} & React.DetailedHTMLProps<React.HTMLAttributes<HTMLDivElement>, HTMLDivElement>;


/**
 * Visual component to display a progress bar.
 * 
 * Usage:
 * ```tsx
 * <Progress value={50} max={100} />
 * ```
 * 
 * The value and max props are required.
 * 
 */
export const Progress = ({
  value,
  max,
  className: classNameInput,
  ...htmlProps
}: ProgressProps) => {
  return (
    <div {...className("Progress", `:${classNameInput}`)} {...htmlProps}>
      {Array.from({ length: max }).map((_, i) => (
        <div key={i} {...className({ active: i < value })} />
      ))}
    </div>
  );
};