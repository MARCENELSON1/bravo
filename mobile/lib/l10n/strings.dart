import 'package:flutter/widgets.dart';

import '../auth/session.dart';
import '../features/floor/floor_view.dart';
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
}

extension StringsX on BuildContext {
  Strings get s => Strings(Localizations.localeOf(this));
}
