import 'package:intl/intl.dart';

/// Los montos vienen en unidades menores (centavos). Formatea a moneda es-AR.
String formatMoney(int amount, String currency) {
  final f = NumberFormat.currency(locale: 'es_AR', symbol: r'$ ', decimalDigits: 2);
  return f.format(amount / 100);
}
