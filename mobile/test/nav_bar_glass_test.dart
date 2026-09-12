// La barra de navegación es una pastilla de vidrio: el material lo pinta el
// shell, no la barra.
//
// Es un acoplamiento que se rompe en silencio: si alguien le devuelve un fondo
// propio al `NavigationBar`, el vidrio sigue estando ahí abajo pero tapado, y
// nada falla — solo se ve una barra plana. Esto lo hace fallar.

import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:wellnod_mobile/theme/theme.dart';

/// Contraste WCAG entre dos colores opacos.
double _contrast(Color a, Color b) {
  double lum(Color c) {
    double ch(double v) => v <= 0.03928
        ? v / 12.92
        : math.pow((v + 0.055) / 1.055, 2.4).toDouble();
    return 0.2126 * ch(c.r) + 0.7152 * ch(c.g) + 0.0722 * ch(c.b);
  }

  final (hi, lo) = lum(a) > lum(b) ? (lum(a), lum(b)) : (lum(b), lum(a));
  return (hi + 0.05) / (lo + 0.05);
}

void main() {
  for (final (nombre, tema) in [
    ('claro', buildLightTheme()),
    ('oscuro', buildDarkTheme()),
  ]) {
    test('en modo $nombre la barra no trae fondo propio', () {
      expect(
        tema.navigationBarTheme.backgroundColor,
        Colors.transparent,
        reason: 'taparía el vidrio que pinta app_scaffold._GlassNavBar',
      );
      expect(tema.navigationBarTheme.elevation, 0);
    });

    test('en modo $nombre el ícono elegido se lee sobre su pastilla', () {
      // Al pintar los íconos a mano se perdió el pariente que Material elegía
      // solo. Si la paleta cambia el verde de la pastilla y nadie mira esto, la
      // pestaña donde estás parado es justo la que deja de leerse.
      final icono = tema.navigationBarTheme.iconTheme!.resolve({
        WidgetState.selected,
      })!;
      final pastilla = tema.navigationBarTheme.indicatorColor!;
      expect(
        _contrast(icono.color!, pastilla),
        greaterThanOrEqualTo(3.0),
        reason: '$nombre: ícono ${icono.color} sobre pastilla $pastilla',
      );
    });

    test('en modo $nombre se distingue la pestaña elegida de las demás', () {
      final texto = tema.navigationBarTheme.labelTextStyle!;
      final elegido = texto.resolve({WidgetState.selected})!;
      final resto = texto.resolve(<WidgetState>{})!;
      expect(elegido.color, isNot(resto.color));
      expect(elegido.fontWeight!.value, greaterThan(resto.fontWeight!.value));
      // Y el que no está elegido igual tiene que leerse. Se mide contra
      // `surface` porque es lo más parecido al velo de la pastilla que hay en
      // el tema: el velo es blanco translúcido sobre el fondo escénico, y cae
      // a pocos puntos de ahí en los dos modos.
      expect(
        _contrast(resto.color!, tema.colorScheme.surface),
        greaterThanOrEqualTo(3.0),
        reason: nombre,
      );
    });
  }
}
