import 'package:flutter/widgets.dart';

import '../auth/session.dart';
import '../features/cashier/payment_dtos.dart';
import '../features/floor/floor_view.dart';
import '../features/invoices/invoice_repository.dart';
import '../features/order/order_dtos.dart';

/// i18n mínimo ES/EN sin codegen (F0). Fallback a español (paridad AR): el
/// idioma efectivo sale de `Localizations.localeOf(context)`, que el framework
/// resuelve contra `supportedLocales` (es primero). Los textos de error del
/// backend ya vienen en español, así que se muestran tal cual (el mapa EN por
/// `code` es un refinamiento posterior).
class Strings {
  const Strings(this.locale);

  final Locale locale;
  bool get _en => locale.languageCode == 'en';

  String get appName => 'Wellnod';

  // Login
  String get loginTitle => _en ? 'Sign in to Wellnod' : 'Ingresá a Wellnod';
  String get loginSubtitle =>
      _en ? 'The brain of your venue' : 'El cerebro de tu local';
  String get loginSlug => _en ? 'Venue (slug)' : 'Local (slug)';
  String get loginEmail => _en ? 'Email' : 'Email';
  String get loginPassword => _en ? 'Password' : 'Contraseña';
  String get loginSubmit => _en ? 'Sign in' : 'Ingresar';
  String get loginRequired =>
      _en ? 'Complete all the fields.' : 'Completá todos los campos.';

  // Home
  String greeting(String name) => _en ? 'Hi, $name' : 'Hola, $name';
  String get homeSubtitle => _en
      ? 'Your foundation is ready. Operational screens come next.'
      : 'Tu base está lista. Las pantallas operativas vienen en camino.';
  String get logout => _en ? 'Sign out' : 'Cerrar sesión';
  String get comingSoon => _en ? 'Coming soon' : 'Próximamente';

  // Tema
  String get themeLight => _en ? 'Light' : 'Claro';
  String get themeDark => _en ? 'Dark' : 'Oscuro';
  String get themeSystem => _en ? 'System' : 'Sistema';
  String get theme => _en ? 'Theme' : 'Tema';
  String get language => _en ? 'Language' : 'Idioma';

  // Nav (tabs del bottom nav)
  String get navHome => _en ? 'Home' : 'Inicio';
  String get navFloor => _en ? 'Floor' : 'Piso';
  String get navKitchen => _en ? 'Kitchen' : 'Cocina';
  String get navCashier => _en ? 'Cashier' : 'Caja';
  String get navFinance => _en ? 'Finance' : 'Finanzas';
  String get navMore => _en ? 'More' : 'Más';

  String role(Role r) {
    switch (r) {
      case Role.owner:
        return _en ? 'Owner' : 'Dueño';
      case Role.manager:
        return _en ? 'Manager' : 'Encargado';
      case Role.waiter:
        return _en ? 'Waiter' : 'Mozo';
      case Role.kitchen:
        return _en ? 'Kitchen' : 'Cocina';
      case Role.bar:
        return 'Bar';
      case Role.cashier:
        return _en ? 'Cashier' : 'Cajero';
    }
  }

  // Piso (Fase 1)
  String get floorTitle => _en ? 'Floor' : 'Piso';
  String get floorSubtitle =>
      _en ? 'Live tables by sector' : 'Mesas en vivo por sector';
  String get floorSearch => _en ? 'Search table' : 'Buscar mesa';
  String floorAttention(int count) =>
      _en ? 'Need attention · $count' : 'Requieren atención · $count';
  String get floorRequestBill => _en ? 'Ask for bill' : 'Pedir cuenta';
  String get floorEmpty => _en ? 'No tables' : 'Sin mesas';
  String paxLabel(int pax) => '· ${pax}p';
  String minutesLabel(int m) => "$m′";

  String get chipAll => _en ? 'All' : 'Todas';
  String get chipToServe => _en ? 'To serve' : 'A servir';
  String get chipToCharge => _en ? 'To charge' : 'A cobrar';
  String get chipMine => _en ? 'Mine' : 'Mías';
  String get chipFree => _en ? 'Free' : 'Libres';

  String floorState(FloorStatus s) {
    switch (s) {
      case FloorStatus.free:
        return _en ? 'Free' : 'Libre';
      case FloorStatus.open:
        return _en ? 'Open' : 'Abierta';
      case FloorStatus.inKitchen:
        return _en ? 'In kitchen' : 'En cocina';
      case FloorStatus.toServe:
        return _en ? 'To serve' : 'A servir';
      case FloorStatus.served:
        return _en ? 'Served' : 'Servida';
      case FloorStatus.toCharge:
        return _en ? 'To charge' : 'A cobrar';
      case FloorStatus.closed:
        return _en ? 'Closed' : 'Cerrada';
    }
  }

  // Comanda
  String get orderTitle => _en ? 'Order' : 'Comanda';
  String get orderTotal => _en ? 'Total' : 'Total';
  String get orderEmpty => _en ? 'No items yet' : 'Sin ítems todavía';
  String get addProducts => _en ? 'Add products' : 'Agregar productos';
  String get searchProduct => _en ? 'Search product' : 'Buscar producto';
  String get done => _en ? 'Done' : 'Listo';
  String marchCount(int n) => _en ? 'Send to kitchen ($n)' : 'Marchar ($n)';
  String get moveTable => _en ? 'Move to a free table' : 'Mover a mesa libre';
  String get mergeTable => _en ? 'Merge another table here' : 'Unir otra mesa acá';
  String get noFreeTables => _en ? 'No free tables' : 'No hay mesas libres';
  String get noOtherTables => _en ? 'No other tables' : 'No hay otras mesas';
  String tableLabel(int number) => _en ? 'Table $number' : 'Mesa $number';

  // Modo contingencia (sync)
  String pendingSync(int n) =>
      _en ? '$n to sync' : '$n por sincronizar';

  // Impresora ESC/POS
  String get printerTitle => _en ? 'Printer' : 'Impresora';
  String get printerCurrent => _en ? 'Current printer' : 'Impresora actual';
  String get printerNone => _en ? 'None' : 'Ninguna';
  String get printerPaired => _en ? 'Paired devices' : 'Dispositivos vinculados';
  String get printerRescan => _en ? 'Rescan' : 'Reescanear';
  String get printerTest => _en ? 'Test print' : 'Imprimir prueba';
  String get printerSaved => _en ? 'Printer saved' : 'Impresora guardada';
  String get printerBtOff =>
      _en ? 'Bluetooth is off' : 'El Bluetooth está apagado';
  String get printerNoDevices =>
      _en ? 'No paired printers' : 'No hay impresoras vinculadas';
  String get printerTestSent => _en ? 'Test sent' : 'Prueba enviada';
  String get printerNoPrinter =>
      _en ? 'No printer selected' : 'No hay impresora seleccionada';

  // KDS (Fase 2)
  String get kdsKitchen => _en ? 'Kitchen' : 'Cocina';
  String get kdsBar => 'Bar';
  String get kdsEmpty => _en ? 'No pending items' : 'Sin pedidos pendientes';
  String get kdsStart => _en ? 'Start' : 'Empezar';
  String get kdsReady => _en ? 'Ready' : 'Listo';
  String get kdsDelayed => _en ? 'Late' : 'Demora';
  String get kdsUnknownTable => _en ? 'Table —' : 'Mesa —';

  String itemStatusLabel(ItemStatus st) {
    switch (st) {
      case ItemStatus.pending:
        return _en ? 'Pending' : 'Pendiente';
      case ItemStatus.sent:
        return _en ? 'In kitchen' : 'En cocina';
      case ItemStatus.preparing:
        return _en ? 'Preparing' : 'Preparando';
      case ItemStatus.ready:
        return _en ? 'Ready' : 'Listo';
      case ItemStatus.served:
        return _en ? 'Served' : 'Servido';
      case ItemStatus.cancelled:
        return _en ? 'Cancelled' : 'Anulado';
    }
  }

  // Caja (Fase 3)
  String get cashierTitle => _en ? 'Register' : 'Caja';
  String get cashierClosed => _en ? 'Register closed' : 'Caja cerrada';
  String get cashierOpen => _en ? 'Open register' : 'Abrir caja';
  String get cashierClose => _en ? 'Close register' : 'Cerrar caja';
  String get cashierOpeningFloat => _en ? 'Opening float' : 'Fondo inicial';
  String get cashierArqueo => _en ? 'Z report' : 'Arqueo Z';
  String get cashierExpected => _en ? 'Expected' : 'Esperado';
  String get cashierCounted => _en ? 'Counted' : 'Contado';
  String get cashierDifference => _en ? 'Difference' : 'Diferencia';
  String get cashierTips => _en ? 'Tips' : 'Propinas';
  String get cashierCountPrompt =>
      _en ? 'Count cash per method' : 'Contá por método';
  String get cashierClosed2 => _en ? 'Register closed' : 'Caja cerrada';

  // Cobro
  String get cobro => _en ? 'Charge' : 'Cobrar';
  String get cobroRemaining => _en ? 'Remaining' : 'Restante';
  String get cobroAmount => _en ? 'Amount' : 'Monto';
  String get cobroTip => _en ? 'Tip' : 'Propina';
  String get cobroMethod => _en ? 'Method' : 'Método';
  String get cobroRegister => _en ? 'Register payment' : 'Registrar pago';
  String get cobroPayments => _en ? 'Payments' : 'Pagos';
  String get cobroPaid => _en ? 'Paid' : 'Pagado';
  String get cobroNoSession => _en ? 'No open register' : 'No hay caja abierta';
  String get cobroRefund => _en ? 'Refund' : 'Reembolsar';
  String get cobroReopen => _en ? 'Reopen order' : 'Reabrir orden';
  String get presetTotal => _en ? 'Total' : 'Total';

  String methodLabel(PaymentMethod m) => switch (m) {
        PaymentMethod.cash => _en ? 'Cash' : 'Efectivo',
        PaymentMethod.card => _en ? 'Card' : 'Tarjeta',
        PaymentMethod.transfer => _en ? 'Transfer' : 'Transferencia',
        PaymentMethod.mercadopago => 'MercadoPago',
        PaymentMethod.qr => 'QR',
      };

  // Fichaje (Fase 4)
  String get fichajeTitle => _en ? 'Time clock' : 'Fichaje';
  String get clockIn => _en ? 'Clock in' : 'Fichar entrada';
  String get clockOut => _en ? 'Clock out' : 'Fichar salida';
  String get notClockedIn => _en ? 'Not clocked in' : 'No estás fichado';
  String clockedInSince(String time) =>
      _en ? 'On shift since $time' : 'En turno desde $time';
  String get workedTime => _en ? 'Worked' : 'Trabajado';
  String get recentShifts => _en ? 'Recent shifts' : 'Turnos recientes';
  String durationLabel(int minutes) {
    final h = minutes ~/ 60;
    final m = minutes % 60;
    return h > 0 ? '${h}h ${m}m' : '${m}m';
  }

  // Propinas (Fase 4)
  String get tipsTitle => _en ? 'Tips' : 'Propinas';
  String get tipsEarned => _en ? 'Earned' : 'Ganado';
  String get tipsPaid => _en ? 'Paid' : 'Pagado';
  String get tipsPending => _en ? 'Pending' : 'Pendiente';
  String get tipsPay => _en ? 'Pay out' : 'Pagar';
  String get tipsEmpty => _en ? 'No tips' : 'Sin propinas';

  // Más (hub)
  String get moreTitle => _en ? 'More' : 'Más';

  // Home (Fase 5)
  String get homeToday => _en ? 'Today' : 'Hoy';
  String get homeNet => _en ? 'Profit' : 'Ganancia';
  String get homeSales => _en ? 'Sales' : 'Ventas';
  String get homeCollected => _en ? 'Collected' : 'Cobrado';
  String get homeActiveOrders => _en ? 'Active orders' : 'Órdenes activas';
  String get homeAvgTicket => _en ? 'Avg ticket' : 'Ticket promedio';
  String get askCopilot => _en ? 'Ask the copilot' : 'Preguntar al copiloto';

  // Copiloto (Fase 5)
  String get copilotTitle => _en ? 'Copilot' : 'Copiloto';
  String get copilotHint =>
      _en ? 'Ask about your business' : 'Preguntá sobre tu negocio';
  String get copilotEmpty => _en
      ? 'e.g. how much did I sell today? what is my most profitable dish?'
      : 'Ej: ¿cuánto vendí hoy? ¿cuál es mi plato más rentable?';

  // Pantallas pesadas (Fase 6, consulta)
  String get finanzasTitle => _en ? 'Finance' : 'Finanzas';
  String get finanzasCollected => _en ? 'Net collected' : 'Cobrado neto';
  String get finanzasCommissions => _en ? 'Commissions' : 'Comisiones';
  String get finanzasNotConfigured =>
      _en ? 'Set up your costs on the web' : 'Configurá tus costos en el web';
  String get comprobantesTitle => _en ? 'Invoices' : 'Comprobantes';
  String get comprobantesEmpty => _en ? 'No invoices' : 'Sin comprobantes';
  String get productosTitle => _en ? 'Products' : 'Productos';
  String get productosEmpty => _en ? 'No products' : 'Sin productos';
  String get productoUnavailable => _en ? 'Unavailable today' : 'No disponible hoy';
  String get consultaOnly => _en ? 'View only · edit on the web' : 'Solo consulta · editá en el web';
  String get insumosTitle => _en ? 'Ingredients' : 'Insumos';
  String get insumosEmpty => _en ? 'No ingredients' : 'Sin insumos';
  String get insumosBelowMin => _en ? 'Below minimum' : 'Bajo mínimo';
  String get insumosStock => _en ? 'Stock' : 'Stock';
  String get editPrice => _en ? 'Edit price' : 'Editar precio';
  String get newPrice => _en ? 'New price' : 'Nuevo precio';
  String get purchase => _en ? 'Purchase' : 'Comprar';
  String get waste => _en ? 'Waste' : 'Merma';
  String get qtyLabel => _en ? 'Quantity' : 'Cantidad';
  String get unitCostLabel => _en ? 'Unit cost' : 'Costo unitario';

  // Facturación AFIP (Fase 6)
  String get facturar => _en ? 'Invoice (AFIP)' : 'Facturar (AFIP)';
  String get docNumber => _en ? 'Document number' : 'N° de documento';
  String get docTypeLabel => _en ? 'Document type' : 'Tipo de documento';
  String get invoiceIssued => _en ? 'Invoice issued' : 'Comprobante emitido';
  String docTypeName(DocType t) => switch (t) {
        DocType.cuit => 'CUIT',
        DocType.cuil => 'CUIL',
        DocType.dni => 'DNI',
        DocType.consumidorFinal => _en ? 'Final consumer' : 'Consumidor final',
      };

  // Reportes (Fase 6, consulta)
  String get reportesTitle => _en ? 'Reports' : 'Reportes';
  String get repMargin => _en ? 'Gross margin' : 'Margen bruto';
  String get repOrders => _en ? 'Orders' : 'Órdenes';
  String get repTopProducts => _en ? 'Top products' : 'Top productos';
  String get repPaymentMix => _en ? 'Payment mix' : 'Mix de pagos';
  String repUnits(int n) => _en ? '$n units' : '$n u.';

  // Proveedores (Fase 6)
  String get proveedoresTitle => _en ? 'Suppliers' : 'Proveedores';
  String get proveedoresEmpty => _en ? 'No suppliers' : 'Sin proveedores';
  String get provNew => _en ? 'New supplier' : 'Nuevo proveedor';
  String get provName => _en ? 'Name' : 'Nombre';
  String get provContact => _en ? 'Contact' : 'Contacto';
  String get provPhone => _en ? 'Phone' : 'Teléfono';
  String get provNotes => _en ? 'Notes' : 'Notas';
  String get provActive => _en ? 'Active' : 'Activo';

  // CRM / Clientes (Fase 6)
  String get clientesTitle => _en ? 'Customers' : 'Clientes';
  String get clientesEmpty => _en ? 'No customers' : 'Sin clientes';
  String get clientesSearch => _en ? 'Search customer' : 'Buscar cliente';
  String get clienteNew => _en ? 'New customer' : 'Nuevo cliente';
  String get clienteEmail => 'Email';
  String get clienteNoContact => _en ? 'Do not contact' : 'No contactar';

  // Ajustes (Fase 6)
  String get ajustesTitle => _en ? 'Settings' : 'Ajustes';
  String get setLaborCost => _en ? 'Monthly labor cost' : 'Costo laboral mensual';
  String get setOtherFixed => _en ? 'Other monthly fixed' : 'Otros fijos mensuales';
  String get setTargetFoodCost => _en ? 'Target food cost %' : 'Food cost objetivo %';
  String get setVat => _en ? 'VAT %' : 'IVA %';
  String get setInflation => _en ? 'Monthly inflation %' : 'Inflación mensual %';
  String get setSeats => _en ? 'Seats' : 'Cubiertos';
  String get setOpenMinutes => _en ? 'Open minutes/day' : 'Minutos abiertos/día';
  String get setSave => _en ? 'Save' : 'Guardar';
  String get setSaved => _en ? 'Settings saved' : 'Ajustes guardados';
  String get cancel => _en ? 'Cancel' : 'Cancelar';
  String get passwordShow => _en ? 'Show password' : 'Mostrar contraseña';
  String get passwordHide => _en ? 'Hide password' : 'Ocultar contraseña';
  String get retry => _en ? 'Retry' : 'Reintentar';
  String get confirm => _en ? 'Confirm' : 'Confirmar';
  String get refundConfirmTitle =>
      _en ? 'Refund this payment?' : '¿Reembolsar este pago?';
  String get refundConfirmBody => _en
      ? 'The payment will be reversed. This affects the cash register.'
      : 'Se revierte el cobro. Impacta en la caja.';
  String get reopenConfirmTitle =>
      _en ? 'Reopen this order?' : '¿Reabrir esta orden?';
  String get reopenConfirmBody => _en
      ? 'Payments will be reversed so you can charge again.'
      : 'Se revierten los cobros para poder volver a cobrar.';
  String get setDelete => _en ? 'Delete' : 'Eliminar';
  String get setEdit => _en ? 'Edit' : 'Editar';
  String get ajustesSubtitle =>
      _en ? 'Manage your data and preferences.' : 'Gestioná tus datos y preferencias.';
  String get financeConfigTitle =>
      _en ? 'Finance settings' : 'Configuración de finanzas';
  String get financeConfigOpen =>
      _en ? 'Finance settings' : 'Configuración de finanzas';
  String get editSoon => _en ? 'Coming soon' : 'Próximamente';
  String get reduceMotion => _en ? 'Reduce motion' : 'Reducir movimiento';
  String get reduceMotionDesc => _en
      ? 'Turns off interface animations.'
      : 'Desactiva las animaciones de la interfaz.';

  // Ajustes › Caja y pagos (paridad con la web)
  String get cashRequireOpenTitle =>
      _en ? 'Require open cash session' : 'Apertura de caja obligatoria';
  String get cashRequireOpenDesc => _en
      ? "You can't take payments without an open cash session."
      : 'No se puede cobrar sin una caja abierta.';
  String get cashBlindTitle => _en ? 'Blind count' : 'Arqueo ciego';
  String get cashBlindDesc => _en
      ? 'On close, the cashier counts without seeing the expected total (the difference comes out honest).'
      : 'Al cerrar caja, el cajero cuenta sin ver el esperado (la diferencia sale honesta).';
  String get cashSaveError => _en
      ? "We couldn't save the setting."
      : 'No pudimos guardar el ajuste.';
  String get commissionsTitle =>
      _en ? 'Commissions by payment method' : 'Comisiones por medio de pago';
  String get commissionsDesc => _en
      ? 'What the gateway keeps from each payment. With this, Home shows the real profit after commissions. Empty = 0%.'
      : 'Lo que se queda la pasarela de cada cobro. Con esto, el Inicio te muestra la ganancia real después de comisiones. Vacío = 0%.';
  String get commissionsInvalid => _en
      ? 'Invalid commission (0 to 100%).'
      : 'Comisión inválida (entre 0 y 100%).';
  String get commissionsSaved =>
      _en ? 'Commissions saved.' : 'Comisiones guardadas.';
  String get commissionsSaveError => _en
      ? "We couldn't save the commissions."
      : 'No pudimos guardar las comisiones.';
  String get commissionsSave =>
      _en ? 'Save commissions' : 'Guardar comisiones';
  String payMethodLabel(String method) => switch (method) {
        'CARD' => _en ? 'Card' : 'Tarjeta',
        'MERCADOPAGO' => 'MercadoPago',
        'QR' => 'QR',
        'CASH' => _en ? 'Cash' : 'Efectivo',
        'TRANSFER' => _en ? 'Transfer' : 'Transferencia',
        _ => method,
      };

  // Ajustes › Salones y mesas
  String get sectorsTitle => _en ? 'Sectors' : 'Sectores';
  String get sectorsDesc => _en
      ? 'Dining room, terrace, bar… Organize your floor.'
      : 'Salón, terraza, barra… Organizá tu piso.';
  String get sectorsEmpty => _en ? 'No sectors yet.' : 'Sin sectores todavía.';
  String get sectorAdd => _en ? 'Add sector' : 'Agregar sector';
  String get sectorName => _en ? 'Sector name' : 'Nombre del sector';
  String get sectorSaved => _en ? 'Sector saved.' : 'Sector guardado.';
  String get sectorDeleted => _en ? 'Sector deleted.' : 'Sector eliminado.';
  String sectorDeleteConfirm(String name) =>
      _en ? 'Delete "$name"?' : '¿Eliminar "$name"?';
  String get sectorSaveError =>
      _en ? "We couldn't save the sector." : 'No pudimos guardar el sector.';

  // Ajustes › Equipo
  String get inviteTitle => _en ? 'Invite a user' : 'Invitar un usuario';
  String get inviteDesc => _en
      ? 'They get an email to join your venue with the chosen role.'
      : 'Le llega un email para sumarse a tu local con el rol elegido.';
  String get inviteEmail => _en ? 'Email' : 'Email';
  String get inviteRole => _en ? 'Role' : 'Rol';
  String get inviteSend => _en ? 'Send invitation' : 'Enviar invitación';
  String get inviteSent => _en ? 'Invitation sent.' : 'Invitación enviada.';
  String get inviteEmailInvalid =>
      _en ? 'Enter a valid email.' : 'Ingresá un email válido.';
  String get inviteError =>
      _en ? "We couldn't send the invitation." : 'No pudimos enviar la invitación.';

  // Ajustes › Datos del local (fiscal)
  String get fiscalTitle => _en ? 'Fiscal data' : 'Datos fiscales';
  String get fiscalCountry => _en ? 'Country' : 'País';
  String get fiscalCurrency => _en ? 'Currency' : 'Moneda';
  String get fiscalRegime => _en ? 'Tax regime' : 'Régimen fiscal';
  String get fiscalStreet => _en ? 'Street' : 'Calle';
  String get fiscalCity => _en ? 'City' : 'Ciudad';
  String get fiscalState => _en ? 'State / Province' : 'Provincia';
  String get fiscalZip => _en ? 'ZIP' : 'Código postal';
  String get fiscalSave => _en ? 'Save address' : 'Guardar dirección';
  String get fiscalSaved =>
      _en ? 'Fiscal address saved.' : 'Dirección fiscal guardada.';
  String get fiscalError =>
      _en ? "We couldn't save the address." : 'No pudimos guardar la dirección.';

  // Ajustes › Integraciones (Mercado Pago)
  String get mpTitle => 'Mercado Pago';
  String get mpDesc => _en
      ? 'Connect your account to collect online payments.'
      : 'Conectá tu cuenta para cobrar pagos online.';
  String get mpConnected => _en ? 'Connected' : 'Conectado';
  String get mpNotConnected => _en ? 'Not connected' : 'Sin conectar';
  String get mpConnect => _en ? 'Connect' : 'Conectar';
  String get mpDisconnect => _en ? 'Disconnect' : 'Desconectar';
  String get mpDisconnected =>
      _en ? 'Mercado Pago disconnected.' : 'Mercado Pago desconectado.';
  String get mpTestMode => _en ? 'Test mode' : 'Modo prueba';
  String get mpLiveMode => _en ? 'Live mode' : 'Modo producción';
  String get mpOpenError => _en
      ? "We couldn't open the connection page."
      : 'No pudimos abrir la página de conexión.';
  String get mpError => _en
      ? "We couldn't complete the operation."
      : 'No pudimos completar la operación.';

  // Recetas (Fase 6)
  String get recetaTitle => _en ? 'Recipe' : 'Receta';
  String get recetaEmpty => _en ? 'No recipe yet' : 'Sin receta todavía';
  String get recetaAdd => _en ? 'Add ingredient' : 'Agregar insumo';
  String get recetaPrep => _en ? 'Preparation' : 'Preparación';
  String get recetaSaved => _en ? 'Recipe saved' : 'Receta guardada';
}

extension StringsX on BuildContext {
  Strings get s => Strings(Localizations.localeOf(this));
}
