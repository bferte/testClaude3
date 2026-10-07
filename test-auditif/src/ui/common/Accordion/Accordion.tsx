'use client'

import { useContext, useState } from "react"
import { ChevronDownIcon } from "lucide-react"

import { AccordionContext } from "./AccordionContext"
import { AccordionProps, AccordionItemProps } from "./Accordion.types"

import classNameModule from "@classname"
import styles from "./Accordion.module.scss"
const className = classNameModule(styles)

/**
 * 
 * Accordion component for collapsible content sections.
 * 
 * Usage:
 * ```tsx
 * <Accordion>
 *   <Accordion.Item id="item1" label="Section 1">
 *     Content for section 1
 *   </Accordion.Item>
 *   <Accordion.Item id="item2" label="Section 2">
 *     Content for section 2
 *   </Accordion.Item>
 * </Accordion>
 * ```
 * 
 * Features:
 * - Only one section can be open at a time
 * - Sections can be toggled open/closed by clicking on the header
 * - Can specify a default opened item with the defaultOpenedItem prop
 */
export const Accordion = ({ children, defaultOpenedItem = null }: AccordionProps) => {
  const [openedItem, setOpenedItem] = useState<string | null>(defaultOpenedItem)

  return (
    <AccordionContext.Provider value={{ openedItem, setOpenedItem }}>
      <div {...className("Accordion")}>{children}</div>
    </AccordionContext.Provider>
  )
}

const AccordionItem = ({ label, children, id, className: customClassName }: AccordionItemProps) => {
  const { openedItem, setOpenedItem } = useContext(AccordionContext)
  const isOpen = openedItem === id

  const handleClick = () => setOpenedItem(openedItem === id ? null : id)

  return (
    <div {...className("AccordionItem", customClassName)}>
      <header
        onPointerDown={(e) => e.preventDefault()}
        onClick={handleClick}
        {...className({ isOpen })}
      >
        <div>{label}</div>
        <ChevronDownIcon size={15} {...className("Chevron", { isOpen })} />
      </header>
      {isOpen && <div {...className("content")}>{children}</div>}
    </div>
  )
}

Accordion.Item = AccordionItem
