// Deep link a WhatsApp (wa.me) sin proveedor ni API. El teléfono debe venir en
// dígitos (con código de país). Devuelve null si no hay teléfono.
export function waLink(phone: string | null, text?: string): string | null {
  const digits = (phone ?? "").replace(/\D/g, "")
  if (!digits) return null
  const q = text ? `?text=${encodeURIComponent(text)}` : ""
  return `https://wa.me/${digits}${q}`
}
