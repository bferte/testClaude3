"use client";

import { ChevronDownIcon, XIcon } from "lucide-react";
import { useEffect, useRef } from "react";

import { useDropdown } from "@hooks/common";

import classNameModule from "@classname";
import styles from "./YearPicker.module.scss";
const className = classNameModule(styles);

/**
 * YearPicker component for selecting a year.
 * 
 * Usage:
 * ```tsx
 * <YearPicker value={2024} onChange={(value) => {}} />
 * 
 * The value and onChange props are required.
 * 
 * Used in the IntroductionStep component.
 */
export const YearPicker = ({ value, onChange }: YearPickerProps) => {
  const [dropdownIsOpen, toggleDropdown, rootRef] = useDropdown();
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (dropdownIsOpen) {
      const dropdownElement = dropdownRef.current;

      if (!dropdownElement) return;

      requestAnimationFrame(() => {
        dropdownElement.querySelector("[aria-selected=true]")?.scrollIntoView({
          block: "center",
        });
      });
    }
  }, [dropdownIsOpen]);

  useEffect(() => {
    if (dropdownIsOpen) {
      const handleKeyDown = (e: KeyboardEvent) => {
        if (e.key === "Escape") {
          toggleDropdown();
        }
      };

      document.addEventListener("keydown", handleKeyDown);
      return () => {
        document.removeEventListener("keydown", handleKeyDown);
      };
    }
  }, [dropdownIsOpen]);

  useEffect(() => {
    if (dropdownIsOpen) {
      const handleKeyDown = (e: KeyboardEvent) => {
        if (e.key === "ArrowUp") {
          onChange(Math.min(new Date().getFullYear(), value + 1));
          requestAnimationFrame(() => {
            dropdownRef.current
              ?.querySelector("[aria-selected=true]")
              ?.scrollIntoView({
                block: "nearest",
              });
          });
        } else if (e.key === "ArrowDown") {
          onChange(Math.max(new Date().getFullYear() - 99, value - 1));
          requestAnimationFrame(() => {
            dropdownRef.current
              ?.querySelector("[aria-selected=true]")
              ?.scrollIntoView({
                block: "nearest",
              });
          });
        }
      };

      window.addEventListener("keydown", handleKeyDown);
      return () => {
        window.removeEventListener("keydown", handleKeyDown);
      };
    }
  }, [dropdownIsOpen, value]);

  return (
    <div {...className("YearPicker")} ref={rootRef}>
      <button
        aria-labelledby="selected-year"
        aria-expanded={dropdownIsOpen}
        onClick={() => toggleDropdown()}
        onKeyDown={(e) => {
          if (e.key === "ArrowUp") {
            onChange(Math.min(new Date().getFullYear(), value + 1));
            requestAnimationFrame(() => {
              dropdownRef.current
                ?.querySelector("[aria-selected=true]")
                ?.scrollIntoView({
                  block: "nearest",
                });
            });
          } else if (e.key === "ArrowDown") {
            onChange(Math.max(new Date().getFullYear() - 99, value - 1));
            requestAnimationFrame(() => {
              dropdownRef.current
                ?.querySelector("[aria-selected=true]")
                ?.scrollIntoView({
                  block: "nearest",
                });
            });
          }
        }}
      >
        <span id="selected-year">{value}</span>

        <ChevronDownIcon size={16} />
      </button>

      {dropdownIsOpen && (
        <div {...className("dropdown")} ref={dropdownRef}>
          <header>
            <button
              onClick={() => toggleDropdown()}
              aria-label="Fermer le sélecteur d'année"
            >
              <XIcon size={20} />
            </button>
          </header>
          <div role="listbox">
            {Array.from({ length: 100 }).map((_, i) => {
              const year = new Date().getFullYear() - i;

              return (
                <button
                  id={year.toString()}
                  role="option"
                  aria-selected={value === year}
                  {...className({ active: value === year })}
                  key={i}
                  onClick={() => {
                    toggleDropdown();
                    onChange(year);
                  }}
                >
                  {year}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

type YearPickerProps = {
  value: number;
  onChange: (value: number) => void;
};
