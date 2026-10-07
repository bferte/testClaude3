import { createContext } from "react"
import { AccordionContextType } from "./Accordion.types"

export const AccordionContext = createContext<AccordionContextType>({
    openedItem: null,
    setOpenedItem: () => { },
}) 