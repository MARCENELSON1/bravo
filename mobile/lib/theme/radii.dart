/// Escala de radios portada de `index.css` (`--radius: 0.75rem` = 12px + multiplicadores).
class WellnodRadii {
  const WellnodRadii._();

  static const double base = 12.0; // --radius (lg)
  static const double sm = base * 0.6; // 7.2
  static const double md = base * 0.8; // 9.6
  static const double lg = base; // 12
  static const double xl = base * 1.4; // 16.8
  static const double xl2 = base * 1.8; // 21.6
  static const double xl3 = base * 2.2; // 26.4
  static const double xl4 = base * 2.6; // 31.2

  /// Los paneles glass usan el utilitario Tailwind `rounded-2xl` = 16px
  /// (distinto del token `--radius-2xl`=21.6px). Ver app-shell.tsx / glass-card.tsx.
  static const double panel = 16.0;
}
