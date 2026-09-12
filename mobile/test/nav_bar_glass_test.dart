// La barra de navegación es vidrio: el material lo pinta el shell, no la barra.
//
// Es un acoplamiento que se rompe en silencio: si alguien le devuelve un fondo
// propio al `NavigationBar`, el vidrio sigue estando ahí abajo pero tapado, y
// nada falla — solo se ve una barra plana. Esto lo hace fallar.

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:wellnod_mobile/theme/theme.dart';

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

    test('en modo $nombre el tinte del vidrio sale de la superficie', () {
      // El vidrio se tiñe con `colorScheme.surface`: tiene que ser opaco, o al
      // aplicarle el 82% quedaría translúcido dos veces y se vería el fondo.
      expect(tema.colorScheme.surface.a, 1.0, reason: nombre);
    });
  }
}
