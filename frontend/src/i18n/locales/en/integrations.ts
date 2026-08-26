// Namespace `integrations` (P3 management): payment methods (MercadoPago) and
// electronic invoicing (ARCA) screen. Doc-types/fiscal condition live in
// @/lib/invoice-labels and stay in Spanish on purpose (not migrated here).
export const integrations = {
  title: "Integrations",
  subtitle: "Connect your payment methods.",
  // Toasts from the MercadoPago OAuth callback (?mp=ok|error).
  mpConnectedToast: "MercadoPago connected.",
  mpConnectError: "We couldn't connect MercadoPago. Please try again.",
  mp: {
    title: "MercadoPago",
    description:
      "Connect your location's account. MercadoPago/QR payments land directly in your account.",
    connected: "Connected",
    sandboxSuffix: " · sandbox",
    notConnected: "Not connected.",
    connect: "Connect with MercadoPago",
    disconnect: "Disconnect",
    disconnecting: "Disconnecting…",
    disconnectedToast: "MercadoPago disconnected.",
    startError: "We couldn't start the connection.",
    disconnectError: "We couldn't disconnect.",
  },
  afip: {
    title: "ARCA · Electronic invoicing",
    description:
      "Upload your CUIT certificate (WSFEv1) to issue invoices with CAE. It's stored encrypted.",
    connected: "Connected · CUIT {{cuit}} · POS {{pos}}",
    homologationSuffix: " · testing",
    cuitLabel: "CUIT",
    posLabel: "Point of sale",
    fiscalConditionLabel: "Tax condition",
    certificateLabel: "Certificate (PEM)",
    privateKeyLabel: "Private key (PEM)",
    connect: "Connect ARCA",
    connecting: "Connecting…",
    connectedToast: "ARCA connected.",
    disconnect: "Disconnect",
    disconnecting: "Disconnecting…",
    disconnectedToast: "ARCA disconnected.",
    invalidCuit: "The CUIT must be 11 digits.",
    invalidPos: "Invalid point of sale.",
    invalidPem: "Paste the certificate and private key in PEM format.",
    connectError: "We couldn't connect ARCA.",
    disconnectError: "We couldn't disconnect.",
  },
} as const
