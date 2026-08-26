// Namespace `integrations` (P3 gestión): pantalla de medios de cobro (MercadoPago) y
// facturación electrónica (ARCA). Los doc-types/condición fiscal viven en
// @/lib/invoice-labels y quedan en español a propósito (no se migran acá).
export const integrations = {
  title: "Integraciones",
  subtitle: "Conectá tus medios de cobro.",
  // Toasts del callback OAuth de MercadoPago (?mp=ok|error).
  mpConnectedToast: "MercadoPago conectado.",
  mpConnectError: "No pudimos conectar MercadoPago. Probá de nuevo.",
  mp: {
    title: "MercadoPago",
    description:
      "Conectá la cuenta de tu local. Los cobros por MercadoPago/QR caen directo a tu cuenta.",
    connected: "Conectado",
    sandboxSuffix: " · sandbox",
    notConnected: "No conectado.",
    connect: "Conectar con MercadoPago",
    disconnect: "Desconectar",
    disconnecting: "Desconectando…",
    disconnectedToast: "MercadoPago desconectado.",
    startError: "No pudimos iniciar la conexión.",
    disconnectError: "No pudimos desconectar.",
  },
  afip: {
    title: "ARCA · Facturación electrónica",
    description:
      "Cargá el certificado de tu CUIT (WSFEv1) para emitir facturas con CAE. Se guarda cifrado.",
    connected: "Conectado · CUIT {{cuit}} · PV {{pos}}",
    homologationSuffix: " · homologación",
    cuitLabel: "CUIT",
    posLabel: "Punto de venta",
    fiscalConditionLabel: "Condición fiscal",
    certificateLabel: "Certificado (PEM)",
    privateKeyLabel: "Clave privada (PEM)",
    connect: "Conectar ARCA",
    connecting: "Conectando…",
    connectedToast: "ARCA conectado.",
    disconnect: "Desconectar",
    disconnecting: "Desconectando…",
    disconnectedToast: "ARCA desconectado.",
    invalidCuit: "El CUIT debe tener 11 dígitos.",
    invalidPos: "Punto de venta inválido.",
    invalidPem: "Pegá el certificado y la clave privada en formato PEM.",
    connectError: "No pudimos conectar ARCA.",
    disconnectError: "No pudimos desconectar.",
  },
} as const
