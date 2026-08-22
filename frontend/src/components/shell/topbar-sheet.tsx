import { useLayoutEffect, useState, type ReactNode, type RefObject } from "react"
import { AnimatePresence, motion } from "motion/react"

import { useIsMobile } from "@/lib/use-is-mobile"
import { useReduceMotion } from "@/lib/reduce-motion"

// Contenedor de los menús del topbar (correo, calendario): en desktop es un
// dropdown anclado al ícono; en mobile es un modal centrado con fondo, para que
// quede prolijo y proporcional en pantalla. Anima apertura/cierre (estilo iOS) y
// respeta "reducir movimiento". El contenido lo pone cada menú.
const PANEL =
  "overflow-hidden border border-black/10 bg-white/95 shadow-xl backdrop-blur-2xl " +
  "dark:border-white/10 dark:bg-black/85"

export function TopbarSheet({
  open,
  onClose,
  children,
  mobileAsModal = true,
  anchorRef,
}: {
  open: boolean
  onClose: () => void
  children: ReactNode
  // En mobile: true → modal centrado con fondo; false → dropdown anclado (igual que
  // desktop). Por defecto modal.
  mobileAsModal?: boolean
  // Ref al contenedor del botón: el modal en mobile arranca justo debajo (igual que
  // el dropdown), para que coincida en altura con los otros menús del topbar.
  anchorRef?: RefObject<HTMLElement | null>
}) {
  const reduce = useReduceMotion()
  const isMobile = useIsMobile()
  const [top, setTop] = useState(72)

  useLayoutEffect(() => {
    if (!open || !isMobile || !mobileAsModal) return
    const el = anchorRef?.current
    if (el) setTop(Math.round(el.getBoundingClientRect().bottom + 8))
  }, [open, isMobile, mobileAsModal, anchorRef])

  return (
    <AnimatePresence>
      {open ? (
        isMobile && mobileAsModal ? (
          <motion.div
            key="overlay"
            className="fixed inset-0 z-50 flex items-start justify-center bg-black/40 px-4 pb-4"
            initial={reduce ? false : { opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={reduce ? { duration: 0 } : { duration: 0.2, ease: [0.32, 0.72, 0, 1] }}
            onClick={onClose}
          >
            <motion.div
              role="dialog"
              aria-modal="true"
              onClick={(e) => e.stopPropagation()}
              style={{ marginTop: top }}
              initial={reduce ? false : { opacity: 0, scale: 0.96, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={reduce ? { opacity: 0 } : { opacity: 0, scale: 0.97, y: 10 }}
              transition={reduce ? { duration: 0 } : { duration: 0.24, ease: [0.32, 0.72, 0, 1] }}
              className={`flex max-h-[85dvh] w-full max-w-sm flex-col rounded-2xl ${PANEL}`}
            >
              {children}
            </motion.div>
          </motion.div>
        ) : (
          <motion.div
            key="dropdown"
            role="menu"
            initial={reduce ? false : { opacity: 0, scale: 0.94, y: -6 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={reduce ? { opacity: 0 } : { opacity: 0, scale: 0.96, y: -6 }}
            transition={reduce ? { duration: 0 } : { duration: 0.2, ease: [0.32, 0.72, 0, 1] }}
            style={{ transformOrigin: "top right" }}
            className={`absolute right-0 top-full z-40 mt-2 w-80 max-w-[calc(100vw-2rem)] rounded-xl ${PANEL}`}
          >
            {children}
          </motion.div>
        )
      ) : null}
    </AnimatePresence>
  )
}
