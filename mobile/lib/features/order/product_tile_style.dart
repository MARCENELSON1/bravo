import 'package:flutter/material.dart';

import 'capture_logic.dart';

/// Identidad visual de una tile de producto sin foto: color e ícono derivados
/// de la categoría (y la estación como fallback). Determinístico: la misma
/// categoría siempre tiene el mismo color, así el mozo la reconoce sin leer.

// Paleta de tonos (HSL hue) que separan bien entre sí sobre el fondo oscuro.
const _hues = <double>[168, 32, 340, 262, 205, 88, 14, 190, 48, 300];

/// Color de acento de la categoría (para chip, ícono y tinte).
Color categoryAccent(String? category, String station) {
  final key = normalizeText(category ?? station);
  var h = 0;
  for (final r in key.runes) {
    h = (h * 31 + r) & 0x7fffffff;
  }
  final hue = _hues[h % _hues.length];
  return HSLColor.fromAHSL(1, hue, 0.55, 0.60).toColor();
}

/// Ícono por categoría (nombre normalizado); si no matchea, por estación.
IconData categoryIcon(String? category, String station) {
  final c = normalizeText(category ?? '');
  if (c.contains('cafe')) return Icons.local_cafe_outlined;
  if (c.contains('cervez')) return Icons.sports_bar_outlined;
  if (c.contains('vino')) return Icons.wine_bar_outlined;
  if (c.contains('coctel') || c.contains('trago')) {
    return Icons.local_bar_outlined;
  }
  if (c.contains('bebida') || c.contains('gaseosa') || c.contains('agua')) {
    return Icons.local_drink_outlined;
  }
  if (c.contains('postre') || c.contains('dulce')) return Icons.cake_outlined;
  if (c.contains('entrada') || c.contains('picada')) {
    return Icons.tapas_outlined;
  }
  if (c.contains('guarnic') || c.contains('ensalada')) {
    return Icons.rice_bowl_outlined;
  }
  if (c.contains('pizza')) return Icons.local_pizza_outlined;
  if (c.contains('hamburg') || c.contains('sandwich')) {
    return Icons.lunch_dining_outlined;
  }
  return station == 'BAR'
      ? Icons.local_bar_outlined
      : Icons.restaurant_outlined;
}
