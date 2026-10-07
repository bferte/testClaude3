const DEFAULT_CONFIG: ClassNameModuleConfig = {
  globalPrefix: ":",
  keepUnfoundValues: false,
  logUnfoundValues: false,
};

/**
 * Use CSS modules classname easily.
 *
 * Usage :
 *
 * ```tsx
 *  import styles from './styles.module.css';
 *  const className = classNameModule(styles)
 * ```
 *
 * ```tsx
 *  <div {...className('Component', {active: true, type: 'user'})} />
 * ```
 *
 * Documentation : https://github.com/anthonyjeamme/classname
 */
const classNameModule = (
  styles: Record<string, string>,
  config: Partial<ClassNameModuleConfig> = DEFAULT_CONFIG
) => {
  const mergedConfig = { ...DEFAULT_CONFIG, ...config };

  return (...list: TClassNameList) => ({
    className: transformList(list)
      .map((item) => bindItem(styles, item, mergedConfig))
      .filter(Boolean)
      .join(" "),
  });
};

export default classNameModule;

/**
 * Resolves the class name based on the provided styles and configuration.
 * It serves to apply the correct styling while avoiding unintended style conflicts.
 */
const bindItem = (
  styles: Record<string, string>,
  item: string,
  config: ClassNameModuleConfig
) => {
  const { globalPrefix, keepUnfoundValues, logUnfoundValues } = config;
  if (item.startsWith(globalPrefix)) return item.slice(1);

  const styleItem = styles[item];
  if (styleItem) return styleItem;

  if (logUnfoundValues)
    console.warn(`"${item}" is not found in the provided styles.`);

  return keepUnfoundValues ? item : undefined;
};

/**
 * Convert input entries into list of string.
 */
const transformList = (list: TClassNameList): string[] =>
  list.flatMap((item) => {
    if (typeof item === "string") return item;
    if (item == null) return [];
    return transformObject(item);
  });

/**
 * Convert input object into list of string.
 * For example :
 *  { active: true, type: 'user' } is transformed into ['active', 'type-user']
 */
const transformObject = (obj: TClassNameObject): string[] =>
  Object.entries(obj).flatMap(([key, value]) => {
    if (value == null) return [];
    return value === true ? key : `${key}-${value}`;
  });

export interface ClassNameModuleConfig {
  globalPrefix: string;
  keepUnfoundValues: boolean;
  logUnfoundValues: boolean;
}

export interface TClassNameObject {
  [key: string]: boolean | string | null | undefined;
}

type TClassNameItem = string | TClassNameObject;

export type TClassNameList = (TClassNameItem | undefined | null)[];
