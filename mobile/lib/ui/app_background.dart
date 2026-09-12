import 'package:flutter/material.dart';

/// Fondo escénico portado de `app-background.tsx` (hex EXACTOS del gradiente).
/// Gradiente radial claro/oscuro + textura PNG a 50%. La web usa
/// `radial(125% 125% at 18% 12%)` → acá `Alignment(-0.64,-0.76)` (=18%/12%) y
/// radio 1.25.
class AppBackground extends StatelessWidget {
  const AppBackground({super.key});

  @override
  Widget build(BuildContext context) {
    final dark = Theme.of(context).brightness == Brightness.dark;

    final gradient = dark
        ? const RadialGradient(
            center: Alignment(-0.64, -0.76),
            radius: 1.25,
            colors: [Color(0xFF2A4B43), Color(0xFF16241F), Color(0xFF0A120E)],
            stops: [0.0, 0.52, 1.0],
          )
        : const RadialGradient(
            center: Alignment(-0.64, -0.76),
            radius: 1.25,
            colors: [Color(0xFFD7E6DF), Color(0xFFAEC7BB), Color(0xFF85A394)],
            stops: [0.0, 0.5, 1.0],
          );

    return Positioned.fill(
      child: DecoratedBox(
        decoration: BoxDecoration(gradient: gradient),
        child: Opacity(
          opacity: 0.5,
          child: Image.asset(
            dark ? 'assets/img/app-bg-dark.png' : 'assets/img/app-bg-light.png',
            fit: BoxFit.cover,
            errorBuilder: (_, _, _) => const SizedBox.shrink(),
          ),
        ),
      ),
    );
  }
}
