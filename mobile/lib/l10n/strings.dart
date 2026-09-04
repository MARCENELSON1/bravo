import 'package:flutter/widgets.dart';

import '../auth/session.dart';
import '../features/cashier/payment_dtos.dart';
import '../features/finance/finance_range.dart';
import '../features/home/daily_verdict.dart';
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
  // Autoservicio: liberar una mesa ya paga (no se cobra de nuevo).
  String get floorFree => _en ? 'Free table' : 'Liberar';
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
  String markServedCount(int n) =>
      _en ? 'Mark served ($n)' : 'Marcar servido ($n)';
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

  // Home v2 (paridad con el Inicio del web — 7 niveles)
  String dashGreeting(String? name) => name == null
      ? (_en ? 'Good day' : 'Buen día')
      : (_en ? 'Good day, $name' : 'Buen día, $name');
  String dashTodayLabel(DateTime now) {
    const wEn = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    const wEs = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado'];
    const mEn = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const mEs = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'];
    final wd = (_en ? wEn : wEs)[now.weekday % 7];
    final mo = (_en ? mEn : mEs)[now.month - 1];
    return '$wd, ${now.day} $mo ${now.year}';
  }
  String dashWeekdayShort(int weekday) {
    // weekday: 1=lunes … 7=domingo (DateTime). Devuelve 3 letras.
    const en = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    const es = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'];
    return (_en ? en : es)[(weekday - 1) % 7];
  }
  String get dashProfitToday => _en ? 'Your profit today' : 'Tu ganancia de hoy';
  String get dashProfitTentative => _en
      ? "Tentative — you haven't recorded expenses today."
      : 'Provisorio — todavía no cargaste egresos hoy.';
  String dashFeesDeducted(String amount) => _en
      ? "We already deducted $amount in card / MercadoPago fees."
      : 'Ya restamos $amount de comisiones de tarjeta / MercadoPago.';
  String dashVerdict(VerdictTone tone, VerdictVs? vs, int? pct) {
    final vsText = vs == null
        ? ''
        : (vs == VerdictVs.more
            ? (_en ? ' — $pct% more than yesterday' : ' — $pct% más que ayer')
            : (_en ? ' — $pct% less than yesterday' : ' — $pct% menos que ayer'));
    final head = switch (tone) {
      VerdictTone.good => _en ? 'Good day' : 'Buen día',
      VerdictTone.ok => _en ? 'Normal day' : 'Día normal',
      VerdictTone.bad => _en ? 'A day to review' : 'Día para revisar',
    };
    return '$head$vsText';
  }
  String get dashBilledToday => _en ? 'Billed today' : 'Facturaste hoy';
  String dashPaymentsCount(int n) => _en ? '$n payments' : '$n cobros';
  String get dashSpentToday => _en ? 'Spent today' : 'Gastaste hoy';
  String get dashExpensesRegistered =>
      _en ? 'Recorded expenses' : 'Egresos registrados';
  String get dashMarginToday => _en ? 'Your margin today' : 'Tu margen hoy';
  String get dashLoadExpensesForMargin => _en
      ? 'Record your expenses to know the real margin'
      : 'Cargá tus egresos para saber el margen real';
  String dashMarginExplain(int margin) => _en
      ? 'Of every \$100, \$$margin is profit'
      : 'De cada \$100, \$$margin son ganancia';
  String get dashNoSalesYet => _en ? 'No sales yet' : 'Sin ventas aún';
  String get dashChannelsTitle =>
      _en ? "Today's payments by channel" : 'Cobros de hoy por canal';
  String get dashChannelsSubtitle => _en
      ? "Gross amounts (fees not deducted yet)."
      : 'Montos brutos (aún no descontamos comisiones de Mercado Pago / tarjeta).';
  String get dashNoPaymentsToday =>
      _en ? 'No payments yet today.' : 'Todavía no hubo cobros hoy.';
  String get dashAttentionToday => _en ? 'Attention today' : 'Atención hoy';
  String get dashRevenue7dTitle =>
      _en ? 'Sales last 7 days' : 'Facturación últimos 7 días';
  String dashTotalSuffix(String amount) =>
      _en ? '$amount total' : '$amount total';
  String get dashMonthClose => _en ? 'Month close' : 'Cierre del mes';
  String get dashOnTrackToClose =>
      _en ? "At this pace, you'll close at" : 'Si seguís así, cerrás en';
  String dashDayOfMonth(int elapsed, int total) =>
      _en ? 'Day $elapsed of $total' : 'Día $elapsed de $total';
  String get dashCalculating => _en ? 'Calculating…' : 'Calculando…';
  String get dashNotEnoughData => _en
      ? 'Not enough data to project.'
      : 'Sin datos suficientes para proyectar.';
  String get dashViewFinance => _en ? 'View Finance' : 'Ver Finanzas';
  String get dashNoSales7d =>
      _en ? 'No sales in the last 7 days.' : 'Sin ventas en los últimos 7 días.';
  String get dashTomorrowTaskTitle =>
      _en ? 'Your task for tomorrow' : 'Tu tarea para mañana';
  String get dashGotIt => _en ? 'Got it' : 'Entendido';
  String get dashRegisterExpense =>
      _en ? 'Record expense' : 'Registrar egreso';
  String get homeSimpleHint => _en
      ? 'Clock in and get going. Everything you need is in the tabs below.'
      : 'Fichá tu turno y arrancá. Todo lo tuyo está en las pestañas de abajo.';

  // Aviso "comanda lista" (Fase 1)
  String readyBannerTitle(int mesa) =>
      _en ? 'Table $mesa is ready' : 'Mesa $mesa lista';
  String get readyBannerTitleNoTable =>
      _en ? 'An order is ready' : 'Una comanda está lista';
  String get readyBannerAction => _en ? 'View' : 'Ver';
  String get readyBannerDismiss => _en ? 'Dismiss' : 'Descartar';
  String readyModalTitle(int mesa) =>
      _en ? 'Table $mesa · ready' : 'Mesa $mesa · lista';
  String get readyModalTitleNoTable => _en ? 'Order ready' : 'Comanda lista';
  String get comandaEmpty => _en ? 'No items.' : 'Sin ítems.';
  String get readyModalSubtitle => _en ? 'Ready to serve' : 'Lista para servir';
  String readyModalCount(int n) => _en ? '$n items' : '$n ítems';
  String get readyNoteLabel => _en ? 'Note' : 'Nota';
  String get readyMarkServed => _en ? 'Mark served' : 'Marcar servido';
  String get readyServedDone => _en ? 'Marked as served.' : 'Marcada como servida.';
  String get readyClose => _en ? 'Close' : 'Cerrar';

  // Asignación por confirmación / bandeja QR (Fase 2)
  String pendingQrTitle(int count) =>
      _en ? 'QR to confirm ($count)' : 'QR por confirmar ($count)';
  String pendingQrItems(int count) =>
      _en ? '$count items' : '$count ítems';
  String get pendingQrConfirm => _en ? 'Confirm' : 'Confirmar';
  String get pendingQrTable => _en ? 'Table' : 'Mesa';
  String get pendingQrConfirmed =>
      _en ? 'Order confirmed — the table is yours.' : 'Comanda confirmada — la mesa es tuya.';
  String get claimTable => _en ? 'Take table' : 'Tomar mesa';
  String get claimDone => _en ? 'Table is yours now.' : 'La mesa quedó a tu nombre.';
  String get reassignWaiter => _en ? 'Change waiter' : 'Cambiar mozo';
  String get reassignDone => _en ? 'Waiter reassigned.' : 'Mozo reasignado.';

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

  // Finanzas — paridad con la pantalla del web
  String financeRange(FinanceRange r) => switch (r) {
        FinanceRange.today => _en ? 'Today' : 'Hoy',
        FinanceRange.week => _en ? 'This week' : 'Esta semana',
        FinanceRange.month => _en ? 'This month' : 'Este mes',
        FinanceRange.quarter => _en ? 'Quarter' : 'Trimestre',
      };
  String get financeLoadError =>
      _en ? "We couldn't load your finances." : 'No pudimos cargar las finanzas.';
  String get financeHeroNet =>
      _en ? 'Your net profit for the period' : 'Tu ganancia neta del período';
  String get financeVsPrevious =>
      _en ? 'vs previous period' : 'vs período anterior';
  String get financeProjectionPrefix =>
      _en ? "At this pace, you'll close at" : 'Si seguís así, cerrás en';
  String financeProjectionDays(int elapsed, int total) => '($elapsed/$total ${_en ? "days" : "días"})';
  String get financeConfigureCosts => _en
      ? 'Set your fixed costs (labor and others) in the Advisor so net margin and prime cost are exact.'
      : 'Cargá tus costos fijos (personal y otros) en el Asesor para que el margen neto y el prime cost sean exactos.';
  String get financeCommissionsLabel => _en
      ? 'Payment commissions (gateways)'
      : 'Comisiones de cobro (pasarelas)';
  String get financeNetCollected =>
      _en ? 'Net of commissions:' : 'Cobrado neto de comisiones:';
  String get financeDiagnosticsTitle =>
      _en ? 'Diagnostics' : 'Diagnósticos';
  String get financeExpenseChangesTitle => _en
      ? 'The 3 expenses that changed most'
      : 'Los 3 gastos que más cambiaron';
  String get financeExpenseDistTitle =>
      _en ? 'Expense distribution' : 'Distribución de gastos';
  String get financeExpenseEmpty => _en
      ? 'No expenses recorded in the period.'
      : 'Sin gastos registrados en el período.';
  String get financeProductMargins => _en
      ? 'Contribution margin by product'
      : 'Margen de contribución por producto';
  String get financeMovementsTitle =>
      _en ? 'Recent movements' : 'Últimos movimientos';
  String get financeUnitsMargin => _en ? 'Units · Margin' : 'Unidades · Margen';
  String get financeKpisTitle =>
      _en ? 'Sector KPIs' : 'KPIs del rubro';
  String financeHealthyRange(String low, String high) =>
      _en ? 'healthy $low–$high' : 'sano $low–$high';
  String financeHealthyMax(String high) =>
      _en ? 'healthy < $high' : 'sano < $high';
  String financeKpiLabel(String key) => switch (key) {
        'prime_cost' => 'Prime Cost',
        'food_cost' => 'Food Cost',
        'labor_cost' => _en ? 'Labor cost' : 'Costo de personal',
        'waste' => _en ? 'Waste' : 'Mermas',
        'net_margin' => _en ? 'Net margin' : 'Margen neto',
        'gross_margin' => _en ? 'Gross margin' : 'Margen bruto',
        'break_even' => _en ? 'Break-even' : 'Punto de equilibrio',
        'revpash' => 'RevPASH',
        'inventory_turnover' =>
          _en ? 'Inventory turnover' : 'Rotación de inventario',
        _ => key,
      };
  String financeStatusAction(String status) => switch (status) {
        'healthy' => _en ? 'Keep it up' : 'Mantener',
        'warn' => _en ? 'Review' : 'Revisar',
        'alert' => _en ? 'Act' : 'Actuar',
        _ => '—',
      };

  // Asesor (Fase 9) — reporte de insights + KPIs
  String get advisorTitle => _en ? 'Advisor' : 'Asesor';
  String get advisorSubtitle => _en
      ? 'Your numbers read as actions.'
      : 'Tus números leídos como acciones.';
  String get advisorLoadError =>
      _en ? "We couldn't load the report." : 'No pudimos cargar el reporte.';
  String get advisorConfigureCosts => _en
      ? 'Set your costs to unlock net margin and break-even.'
      : 'Cargá tus costos para desbloquear margen neto y punto de equilibrio.';
  String advisorBucketLabel(String bucket) => switch (bucket) {
        'pricing' => _en ? 'Pricing' : 'Precios',
        'costs' => _en ? 'Costs' : 'Costos',
        'menu' => _en ? 'Menu' : 'Carta',
        'operations' => _en ? 'Operations' : 'Operación',
        'cash' => _en ? 'Cash' : 'Caja',
        'inventory' => _en ? 'Inventory' : 'Inventario',
        _ => bucket,
      };
  String advisorKpiLabel(String key) => switch (key) {
        'sales' => _en ? 'Sales' : 'Ventas',
        'gross_margin' => _en ? 'Gross margin' : 'Margen bruto',
        'net_margin' => _en ? 'Net margin' : 'Margen neto',
        'food_cost' => 'Food Cost',
        'prime_cost' => 'Prime Cost',
        'break_even' => _en ? 'Break-even' : 'Punto de equilibrio',
        'orders' => _en ? 'Orders' : 'Órdenes',
        'avg_ticket' => _en ? 'Avg. ticket' : 'Ticket promedio',
        'no_show' => 'No-show',
        _ => key,
      };
  String get advisorConfigTitle =>
      _en ? 'Cost settings' : 'Configuración de costos';
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
  String invoiceStatusLabel(String status) => switch (status) {
        'AUTHORIZED' => _en ? 'Authorized' : 'Autorizado',
        'DRAFT' => _en ? 'Draft' : 'Borrador',
        'REJECTED' => _en ? 'Rejected' : 'Rechazado',
        _ => status,
      };
  String invoiceCaeExpiration(String date) =>
      _en ? 'CAE exp. $date' : 'Vto. CAE $date';
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
  String get repSummaryTitle => _en ? 'Summary' : 'Resumen';
  String get repSales => _en ? 'Sales' : 'Ventas';
  String get repCollectedNet => _en ? 'Net collected' : 'Cobrado neto';
  String get repExpenses => _en ? 'Expenses' : 'Gastos';
  String get repProfit => _en ? 'Profit' : 'Ganancia';
  String get repSalesByDay => _en ? 'Sales by day' : 'Ventas por día';
  String get repSalesByDayEmpty =>
      _en ? 'No sales in the period.' : 'Sin ventas en el período.';
  String get repExpensesByCategory =>
      _en ? 'Expenses by category' : 'Gastos por categoría';
  String get repExpensesEmpty => _en
      ? 'No expenses recorded in the period.'
      : 'Sin gastos registrados en el período.';
  String get repTotal => _en ? 'Total' : 'Total';
  String get repSalesCol => _en ? 'Sales' : 'Ventas';
  String get repMarginCol => _en ? 'Margin' : 'Margen';

  // Gastos
  String get gastosTitle => _en ? 'Expenses' : 'Gastos';
  String get gastosSubtitle => _en
      ? 'Record what the venue spends.'
      : 'Registrá lo que gasta el local.';
  String get gastosNew => _en ? 'New expense' : 'Nuevo gasto';
  String get gastosEmpty =>
      _en ? 'No expenses recorded yet.' : 'Sin gastos registrados todavía.';
  String get gastosAmount => _en ? 'Amount' : 'Monto';
  String get gastosCategory => _en ? 'Category' : 'Categoría';
  String get gastosCounterparty => _en ? 'Supplier / who' : 'Proveedor / a quién';
  String get gastosDescription => _en ? 'Description' : 'Descripción';
  String get gastosMethod => _en ? 'Method' : 'Medio';
  String get gastosInvalidAmount =>
      _en ? 'Enter a valid amount.' : 'Ingresá un monto válido.';
  String get gastosSaved => _en ? 'Expense recorded.' : 'Gasto registrado.';
  String get gastosError =>
      _en ? "We couldn't record the expense." : 'No pudimos registrar el gasto.';

  // Mesas QR (lado admin de la Carta QR)
  String get mesasQrTitle => _en ? 'Table QR codes' : 'QR de mesas';
  String get mesasQrSubtitle => _en
      ? 'One QR per table for the digital menu.'
      : 'Un QR por mesa para la carta digital.';
  String get mesasQrEmpty =>
      _en ? 'No active tables.' : 'No hay mesas activas.';
  String get mesasQrScanHint =>
      _en ? 'Scan to see the menu' : 'Escaneá para ver la carta';
  String mesasQrTableLabel(int n) => _en ? 'Table $n' : 'Mesa $n';
  String get mesasQrLoadError =>
      _en ? "Couldn't load the QR." : 'No pudimos cargar el QR.';
  String get settingsSaveError =>
      _en ? "We couldn't save." : 'No pudimos guardar.';
  // Autopedido
  String get selfOrderTitle => _en ? 'Self-ordering' : 'Autopedido';
  String get selfOrderSubtitle => _en
      ? 'Let diners order from their phone.'
      : 'Que el comensal pida desde el celular.';
  String get selfOrderEnable => _en ? 'Enable self-ordering' : 'Activar autopedido';
  String get selfOrderRequireConfirm =>
      _en ? "Waiter confirms the order" : 'El mozo confirma el pedido';
  String get selfOrderRequireConfirmHint => _en
      ? 'The order waits for the waiter before going to the kitchen.'
      : 'El pedido espera al mozo antes de ir a la cocina.';
  // Modo de la Carta QR (Fase 3)
  String get selfOrderModeLabel => _en ? 'QR mode' : 'Modo del QR';
  String selfOrderMode(String mode) => switch (mode) {
        'SALON' => _en ? 'Dining room' : 'Salón',
        'SELF_SERVICE' => _en ? 'Self-service' : 'Autoservicio',
        _ => _en ? 'View only' : 'Solo lectura',
      };
  String selfOrderModeHint(String mode) => switch (mode) {
        'SALON' => _en
            ? 'The diner orders; a waiter confirms it. Pay at the end.'
            : 'El comensal pide; un mozo confirma. Se paga al final.',
        'SELF_SERVICE' => _en
            ? 'The diner pays first; it auto-marches and assigns a waiter. Turns on table pay.'
            : 'El comensal paga primero; marcha sola y asigna un mozo. Prende el pago en mesa.',
        _ => _en
            ? 'The QR shows the menu only — no ordering.'
            : 'El QR solo muestra la carta — sin pedidos.',
      };
  // Pago en mesa
  String get selfPayTitle => _en ? 'Pay at the table' : 'Pago en mesa';
  String get selfPaySubtitle => _en
      ? 'Let diners pay online from their phone.'
      : 'Que el comensal pague online desde el celular.';
  String get selfPayEnable => _en ? 'Enable table payment' : 'Activar pago en mesa';
  String get selfPayEnableHint => _en
      ? 'Without this, the menu keeps "Ask for the bill".'
      : 'Sin esto, la carta mantiene "Pedir la cuenta".';
  String get selfPayOfferTip => _en ? 'Offer tip' : 'Ofrecer propina';

  // Personal (staff)
  String get staffTitle => _en ? 'Staff' : 'Personal';
  String get staffSubtitle => _en
      ? 'Hours, shifts and hourly rate.'
      : 'Horas, turnos y valor por hora.';
  String get staffReportTitle => _en ? 'Report' : 'Reporte';
  String get staffShiftsTitle => _en ? 'Shifts' : 'Turnos';
  String get staffEmployee => _en ? 'Employee' : 'Empleado';
  String get staffHours => _en ? 'Hours' : 'Horas';
  String get staffOvertime => _en ? 'Overtime' : 'Extra';
  String get staffTables => _en ? 'Tables' : 'Mesas';
  String get staffSales => _en ? 'Sales' : 'Ventas';
  String get staffHourlyRate => _en ? 'Hourly rate' : 'Valor/hora';
  String get staffNoReport =>
      _en ? 'No data in the period.' : 'Sin datos en el período.';
  String get staffNoShifts =>
      _en ? 'No shifts in the period.' : 'Sin turnos en el período.';
  String get staffInProgress => _en ? 'In progress' : 'En curso';
  String get staffClockIn => _en ? 'Clock in' : 'Entrada';
  String get staffClockOut => _en ? 'Clock out' : 'Salida';
  String get staffAdjust => _en ? 'Adjust' : 'Ajustar';
  String get staffAdjustTitle => _en ? 'Correct shift' : 'Corregir turno';
  String get staffAdjusted => _en ? 'Shift corrected.' : 'Turno corregido.';
  String get staffAdjustError =>
      _en ? "We couldn't correct the shift." : 'No pudimos corregir el turno.';
  String get staffSetRate => _en ? 'Hourly rate' : 'Valor por hora';
  String get staffRateSaved => _en ? 'Rate saved.' : 'Valor guardado.';
  String get staffRateError =>
      _en ? "We couldn't save the rate." : 'No pudimos guardar el valor.';
  String get staffInvalidRate =>
      _en ? 'Enter a valid rate.' : 'Ingresá un valor válido.';
  String get staffRateNone => _en ? 'Set rate' : 'Cargar valor';
  String formatMinutes(int m) {
    final h = m ~/ 60;
    final min = m % 60;
    if (h == 0) return '${min}m';
    if (min == 0) return '${h}h';
    return '${h}h ${min}m';
  }

  // Reservas
  String get reservasTitle => _en ? 'Reservations' : 'Reservas';
  String get reservasSubtitle => _en
      ? 'Bookings and no-shows.'
      : 'Reservas y ausencias (no-show).';
  String get reservasEmpty =>
      _en ? 'No reservations for this day.' : 'Sin reservas para este día.';
  String get reservaNew => _en ? 'New reservation' : 'Nueva reserva';
  String get reservaCustomer => _en ? 'Customer name' : 'Nombre del cliente';
  String get reservaPhone => _en ? 'Phone' : 'Teléfono';
  String get reservaGuests => _en ? 'Guests' : 'Comensales';
  String get reservaTable => _en ? 'Table' : 'Mesa';
  String get reservaNoTable => _en ? 'No table' : 'Sin mesa';
  String get reservaNote => _en ? 'Note' : 'Nota';
  String get reservaCreated => _en ? 'Reservation created.' : 'Reserva creada.';
  String get reservaError =>
      _en ? "We couldn't create the reservation." : 'No pudimos crear la reserva.';
  String get reservaCustomerRequired =>
      _en ? 'Enter the customer name.' : 'Ingresá el nombre del cliente.';
  String get reservaGuestsInvalid =>
      _en ? 'Invalid number of guests.' : 'Cantidad de comensales inválida.';
  String get reservaDay => _en ? 'Day' : 'Día';
  String get reservaShift => _en ? 'Shift' : 'Turno';
  String get reservaAll => _en ? 'All' : 'Todos';
  String get reservaDate => _en ? 'Date' : 'Fecha';
  String get reservaTime => _en ? 'Time' : 'Hora';
  String get reservaTransitionError =>
      _en ? "We couldn't update it." : 'No pudimos actualizarla.';
  String reservaTableOption(int n) => _en ? 'Table $n' : 'Mesa $n';
  String turnLabel(String turn) => switch (turn) {
        'LUNCH' => _en ? 'Lunch' : 'Almuerzo',
        'DINNER' => _en ? 'Dinner' : 'Cena',
        _ => turn,
      };
  String reservaStatusLabel(String status) => switch (status) {
        'PENDING' => _en ? 'Pending' : 'Pendiente',
        'CONFIRMED' => _en ? 'Confirmed' : 'Confirmada',
        'SEATED' => _en ? 'Seated' : 'Sentada',
        'COMPLETED' => _en ? 'Completed' : 'Completada',
        'CANCELLED' => _en ? 'Cancelled' : 'Cancelada',
        'NO_SHOW' => 'No-show',
        _ => status,
      };
  String get reservaConfirm => _en ? 'Confirm' : 'Confirmar';
  String get reservaSeat => _en ? 'Seat' : 'Sentar';
  String get reservaComplete => _en ? 'Complete' : 'Completar';
  String get reservaNoShow => _en ? 'No-show' : 'No vino';

  // Analytics
  String get analyticsTitle => _en ? 'Analytics' : 'Analítica';
  String get analyticsSubtitle => _en
      ? 'Revenue, payment mix and top products.'
      : 'Facturación, mix de pagos y top productos.';
  String get anCollected => _en ? 'Collected' : 'Cobrado';
  String get anExpenses => _en ? 'Expenses' : 'Gastos';
  String get anGrossMargin => _en ? 'Gross margin' : 'Margen bruto';
  String get anGrossMarginHint =>
      _en ? 'sales − food cost' : 'ventas − food cost';
  String get anFoodCost => 'Food Cost';
  String anOrdersCount(int n) => _en ? '$n orders' : '$n órdenes';
  String get anPaymentMixTitle => _en ? 'Payment mix' : 'Mix de pagos';
  String get anPaymentMixHint => _en
      ? 'Inflows (charges) and outflows (expenses/refunds).'
      : 'Ingresos (cobros) y egresos (gastos/reembolsos).';
  String get anInflow => _en ? 'Inflow' : 'Ingreso';
  String get anOutflow => _en ? 'Outflow' : 'Egreso';
  String get anOperations => _en ? 'Ops' : 'Ops';
  String get anTopProducts => _en ? 'Top products' : 'Top productos';
  String get anMixEmpty => _en ? 'No movements.' : 'Sin movimientos.';

  // Suscripción / plan (billing)
  String get billingTitle => _en ? 'Subscription' : 'Suscripción';
  String get billingActivePlan => _en ? 'Active plan' : 'Plan activo';
  String billingStatusLine(String value) =>
      _en ? 'Status: $value' : 'Estado: $value';
  String billingRenewsOn(String date) =>
      _en ? ' · renews on $date' : ' · renueva el $date';
  String get billingCancel =>
      _en ? 'Cancel subscription' : 'Cancelar suscripción';
  String get billingCancelConfirm => _en
      ? 'Cancel your subscription?'
      : '¿Cancelar tu suscripción?';
  String get billingCancelSuccess =>
      _en ? 'Subscription cancelled.' : 'Suscripción cancelada.';
  String get billingCancelError =>
      _en ? "We couldn't cancel." : 'No pudimos cancelar.';
  String billingChooseIntro(String gateway) => _en
      ? 'Choose a plan. Payment goes through $gateway.'
      : 'Elegí un plan. El pago se hace por $gateway.';
  String get billingNoPlans =>
      _en ? 'No plans available.' : 'No hay planes disponibles.';
  String get billingSubscribe => _en ? 'Subscribe' : 'Suscribirme';
  String get billingCheckoutError =>
      _en ? "We couldn't start checkout." : 'No pudimos iniciar el pago.';
  String get billingOpenError => _en
      ? "We couldn't open the payment page."
      : 'No pudimos abrir la página de pago.';
  String billingInterval(String interval) => switch (interval) {
        'MONTH' => _en ? 'month' : 'mes',
        'YEAR' => _en ? 'year' : 'año',
        _ => interval.toLowerCase(),
      };
  String billingStatusLabel(String status) => switch (status) {
        'ACTIVE' => _en ? 'Active' : 'Activa',
        'TRIALING' => _en ? 'Trial' : 'Prueba',
        'PAST_DUE' => _en ? 'Past due' : 'Vencida',
        'CANCELLED' || 'CANCELED' => _en ? 'Cancelled' : 'Cancelada',
        _ => status,
      };

  // Panel de Plataforma (super-admin)
  String get platformTitle => _en ? 'Platform' : 'Plataforma';
  String get platformCatalog => _en ? 'Plan catalog' : 'Catálogo de planes';
  String get platformEmpty => _en ? 'No plans yet.' : 'Sin planes todavía.';
  String get platformNewPlan => _en ? 'New plan' : 'Nuevo plan';
  String get platformEditPlan => _en ? 'Edit plan' : 'Editar plan';
  String get platformTier => _en ? 'Tier' : 'Nivel';
  String get platformRegion => _en ? 'Region' : 'Región';
  String platformPrice(String currency) =>
      _en ? 'Price ($currency)' : 'Precio ($currency)';
  String get platformIntervalLabel => _en ? 'Interval' : 'Intervalo';
  String get platformIncludes => _en ? 'Includes' : 'Incluye';
  String get platformActive => _en ? 'Active' : 'Activo';
  String get platformCreate => _en ? 'Create plan' : 'Crear plan';
  String get platformSaveChanges => _en ? 'Save changes' : 'Guardar cambios';
  String get platformInvalidPrice =>
      _en ? 'Invalid price.' : 'Precio inválido.';
  String get platformSaved => _en ? 'Plan saved.' : 'Plan guardado.';
  String get platformSaveError =>
      _en ? "We couldn't save the plan." : 'No pudimos guardar el plan.';
  String get platformDeleteConfirm =>
      _en ? 'Delete this plan?' : '¿Eliminar este plan?';
  String get platformDeleted => _en ? 'Plan deleted.' : 'Plan eliminado.';
  String get platformDeleteError =>
      _en ? "We couldn't delete it." : 'No pudimos eliminarlo.';
  String platformRegionLabel(String region) => switch (region) {
        'AR' => 'Argentina',
        'INTL' => _en ? 'International' : 'Internacional',
        _ => region,
      };

  String shiftSourceLabel(String source) => switch (source) {
        'QR' || 'qr' => 'QR',
        'MANUAL' || 'manual' => _en ? 'Manual' : 'Manual',
        'ADJUSTED' || 'adjusted' => _en ? 'Adjusted' : 'Ajustado',
        'KIOSK' || 'kiosk' => _en ? 'Kiosk' : 'Kiosco',
        _ => source,
      };

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
  String get add => _en ? 'Add' : 'Agregar';
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
