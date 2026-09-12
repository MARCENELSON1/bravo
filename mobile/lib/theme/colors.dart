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
  /// Este es el tono de RELLENO: va de fondo, con texto negro encima (9,77:1 en
  /// los dos temas). NO usarlo como color de texto sobre el fondo de la app —
  /// sobre blanco da 2,15:1 y es ilegible. Para eso está [warnOn].
  static const Color warn = Color(0xFFE0A800);

  /// Verde de "listo/servido". Mismo caso que [warn]: tono de relleno.
  static const Color success = Color(0xFF10B981);

  /// Los mismos dos como RELLENO, con su color de texto encima — el par que el
  /// web define como `--success` / `--success-foreground`. Sirven para un chip o
  /// una insignia, donde el color es el fondo. Para texto sobre el fondo de la
  /// app están [successOn] / [warnOn], que es otra cosa: confundirlos es
  /// exactamente cómo el verde de "servido" terminó en 2,54:1.
  static Color successFill(Brightness b) =>
      b == Brightness.dark ? const Color(0xFF3DCA8D) : const Color(0xFF009962);
  static Color onSuccessFill(Brightness b) =>
      b == Brightness.dark ? const Color(0xFF05100B) : const Color(0xFFFAFAFA);
  static Color warnFill(Brightness b) =>
      b == Brightness.dark ? const Color(0xFFF7B83D) : const Color(0xFFCB7F00);
  static const Color onWarnFill = Color(0xFF090F0C);

  /// Los mismos dos, en la versión que SÍ se puede usar como texto o ícono sobre
  /// el fondo de la app. El tono es el mismo; cambia la luminosidad, porque un
  /// color legible sobre negro no lo es sobre blanco y al revés. Sin esto, el
  /// verde de "servido" daba 2,54:1 en modo claro — se veía, pero no se leía.
  static Color warnOn(Brightness b) =>
      b == Brightness.dark ? warn : const Color(0xFFB45309); // 9,04 / 5,02
  static Color successOn(Brightness b) =>
      b == Brightness.dark ? success : const Color(0xFF047857); // 7,66 / 5,48

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
    destructive: Color(0xFFE7000B), // espejo de index.css
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
    destructive: Color(0xFFFF6467), // espejo de index.css
    border: Color(0x14FFFFFF), // white @ 8%
    input: Color(0x1FFFFFFF), // white @ 12%
    ring: Color(0xFF00BB83),
    sidebar: Color(0xFF060807),
  );
}
