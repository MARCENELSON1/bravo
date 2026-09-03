import 'package:intl/intl.dart';

/// Locale + símbolo por moneda (para respetar el agrupamiento correcto:
/// AR usa 1.234,56 y US usa 1,234.56).
const _currencyFormats = <String, ({String locale, String symbol})>{
  'ARS': (locale: 'es_AR', symbol: r'$ '),
  'USD': (locale: 'en_US', symbol: r'US$ '),
  'EUR': (locale: 'es_ES', symbol: '€ '),
  'BRL': (locale: 'pt_BR', symbol: r'R$ '),
  'CLP': (locale: 'es_CL', symbol: r'$ '),
  'MXN': (locale: 'es_MX', symbol: r'$ '),
  'UYU': (locale: 'es_UY', symbol: r'$U '),
};

/// Los montos vienen en unidades menores (centavos). Formatea según la moneda
/// del tenant (default AR). Antes ignoraba `currency` y siempre usaba es-AR.
String formatMoney(int amount, String currency) {
  final fmt = _currencyFormats[currency.toUpperCase()] ??
      (locale: 'es_AR', symbol: '${currency.toUpperCase()} ');
  final f = NumberFormat.currency(
      locale: fmt.locale, symbol: fmt.symbol, decimalDigits: 2);
  return f.format(amount / 100);
}

/// Parsea un texto en pesos (acepta coma o punto) a unidades menores (centavos).
/// Devuelve null si está vacío o no es un número.
int? pesosToMinor(String text) {
  final cleaned = text.trim().replaceAll(',', '.');
  if (cleaned.isEmpty) return null;
  final value = double.tryParse(cleaned);
  if (value == null) return null;
  return (value * 100).round();
}
