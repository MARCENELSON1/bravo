import 'package:intl/intl.dart';

/// Los montos vienen en unidades menores (centavos). Formatea a moneda es-AR.
String formatMoney(int amount, String currency) {
  final f = NumberFormat.currency(locale: 'es_AR', symbol: r'$ ', decimalDigits: 2);
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
