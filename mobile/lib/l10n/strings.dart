import 'package:flutter/widgets.dart';

import '../auth/session.dart';

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
}

extension StringsX on BuildContext {
  Strings get s => Strings(Localizations.localeOf(this));
}
