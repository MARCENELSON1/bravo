import 'package:flutter/material.dart';

/// Paleta Wellnod portada 1:1 desde `frontend/src/index.css` (`:root` / `.dark`).
///
/// Los tokens del front están en **OKLCH**; acá van ya convertidos a sRGB con
/// gamut-mapping estilo CSS Color 4 (reducción de chroma hasta entrar al gamut),
/// que es como los pinta el navegador. El verde de marca es el primario.
///
/// Fuente única de verdad: `frontend/src/index.css`. Ante drift, re-portar de ahí.
class WellnodPalette {
  const WellnodPalette({
    required this.background,
    required this.foreground,
    required this.card,
    required this.cardForeground,
    required this.primary,
    required this.primaryForeground,
    required this.secondary,
    required this.secondaryForeground,
    required this.muted,
    required this.mutedForeground,
    required this.accent,
    required this.accentForeground,
    required this.destructive,
    required this.border,
    required this.input,
    required this.ring,
    required this.sidebar,
  });

  final Color background;
  final Color foreground;
  final Color card;
  final Color cardForeground;
  final Color primary;
  final Color primaryForeground;
  final Color secondary;
  final Color secondaryForeground;
  final Color muted;
  final Color mutedForeground;
  final Color accent;
  final Color accentForeground;
  final Color destructive;
  final Color border;
  final Color input;
  final Color ring;
  final Color sidebar;

  /// Ámbar de "atención/demora" (mesa o comanda que se está pasando de tiempo).
  /// Único token semántico de warning; sirve para claro y oscuro.
  static const Color warn = Color(0xFFE0A800);

  /// `:root` (index.css:54-87)
  static const WellnodPalette light = WellnodPalette(
    background: Color(0xFFFFFFFF),
    foreground: Color(0xFF090F0C),
    card: Color(0xFFFFFFFF),
    cardForeground: Color(0xFF090F0C),
    primary: Color(0xFF00A271), // verde de marca (oklch 0.63 0.14 163)
    primaryForeground: Color(0xFFFAFAFA),
    secondary: Color(0xFFECF4F0),
    secondaryForeground: Color(0xFF121815),
    muted: Color(0xFFECF4F0),
    mutedForeground: Color(0xFF596760),
    accent: Color(0xFFDDF5E9),
    accentForeground: Color(0xFF0D1914),
    destructive: Color(0xFFE40016),
    border: Color(0xFFD8E0DC),
    input: Color(0xFFD8E0DC),
    ring: Color(0xFF00A271),
    sidebar: Color(0xFFFAFAFA),
  );

  /// `.dark` (index.css:89-121). `border`/`input` son blanco con alpha.
  static const WellnodPalette dark = WellnodPalette(
    background: Color(0xFF0A0E0C),
    foreground: Color(0xFFF2F6F4),
    card: Color(0xFF131916),
    cardForeground: Color(0xFFF2F6F4),
    primary: Color(0xFF00BB83), // verde de marca (oklch 0.7 0.16 163)
    primaryForeground: Color(0xFF05100B),
    secondary: Color(0xFF202623),
    secondaryForeground: Color(0xFFF2F6F4),
    muted: Color(0xFF1B211E),
    mutedForeground: Color(0xFF94A39B),
    accent: Color(0xFF1D2A24),
    accentForeground: Color(0xFFF2F6F4),
    destructive: Color(0xFFFF6568),
    border: Color(0x14FFFFFF), // white @ 8%
    input: Color(0x1FFFFFFF), // white @ 12%
    ring: Color(0xFF00BB83),
    sidebar: Color(0xFF060807),
  );
}
