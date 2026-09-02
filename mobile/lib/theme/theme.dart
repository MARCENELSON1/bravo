import 'package:flutter/material.dart';

import 'colors.dart';
import 'radii.dart';

/// Construye el `ThemeData` de Wellnod a partir de la paleta portada del front.
///
/// Fuentes: por ahora usa el stack del sistema (en iOS = SF Pro, limpio). El
/// bundling de **Geist** (sans/heading) e **Inter** (display) queda como follow-up
/// chico de F0: dropear los `.ttf` variables en `assets/fonts/`, declararlos en
/// `pubspec.yaml` y setear `fontFamily` acá.
const String? _fontFamily = null; // TODO(F0): 'Geist' cuando se bundleen los .ttf

ThemeData buildLightTheme() => _build(WellnodPalette.light, Brightness.light);
ThemeData buildDarkTheme() => _build(WellnodPalette.dark, Brightness.dark);

ThemeData _build(WellnodPalette p, Brightness brightness) {
  final scheme = ColorScheme(
    brightness: brightness,
    primary: p.primary,
    onPrimary: p.primaryForeground,
    secondary: p.secondary,
    onSecondary: p.secondaryForeground,
    tertiary: p.accent,
    onTertiary: p.accentForeground,
    error: p.destructive,
    onError: brightness == Brightness.light ? Colors.white : Colors.black,
    surface: p.card,
    onSurface: p.foreground,
    surfaceContainerHighest: p.muted,
    onSurfaceVariant: p.mutedForeground,
    outline: p.border,
    outlineVariant: p.border,
  );

  return ThemeData(
    useMaterial3: true,
    brightness: brightness,
    colorScheme: scheme,
    fontFamily: _fontFamily,
    scaffoldBackgroundColor: p.background,
    cardTheme: CardThemeData(
      color: p.card,
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(WellnodRadii.panel),
        side: BorderSide(color: p.border),
      ),
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: p.card,
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(WellnodRadii.md),
        borderSide: BorderSide(color: p.input),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(WellnodRadii.md),
        borderSide: BorderSide(color: p.input),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(WellnodRadii.md),
        borderSide: BorderSide(color: p.ring, width: 1.5),
      ),
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        backgroundColor: p.primary,
        foregroundColor: p.primaryForeground,
        minimumSize: const Size.fromHeight(52),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(WellnodRadii.md),
        ),
      ),
    ),
    navigationBarTheme: NavigationBarThemeData(
      backgroundColor: p.card,
      indicatorColor: p.accent,
      elevation: 0,
    ),
  );
}
