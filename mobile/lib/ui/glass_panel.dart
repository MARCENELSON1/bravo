import 'dart:ui';

import 'package:flutter/material.dart';

import '../theme/radii.dart';

/// Panel "glass" frosted, portado de `app-shell.tsx` / `glass-card.tsx`:
/// claro → blanco @55-60% + borde negro @10%; oscuro → blanco @4.5% + borde
/// blanco @10%; con `backdrop-blur-2xl` (~40px de CSS ≈ sigma 18 en Flutter).
class GlassPanel extends StatelessWidget {
  const GlassPanel({
    super.key,
    required this.child,
    this.padding = const EdgeInsets.all(20),
    this.radius = WellnodRadii.panel,
    this.blur = true,
  });

  final Widget child;
  final EdgeInsetsGeometry padding;
  final double radius;

  /// `false` evita el `BackdropFilter` — obligatorio cuando el panel se repite
  /// en una lista/grilla: apilar decenas de blurs mata el scroll. En ese caso
  /// se compensa con un `fill` más opaco para que igual se lea sobre el fondo.
  final bool blur;

  @override
  Widget build(BuildContext context) {
    final dark = Theme.of(context).brightness == Brightness.dark;
    final fill = dark
        ? Colors.white.withValues(alpha: blur ? 0.045 : 0.07)
        : Colors.white.withValues(alpha: blur ? 0.60 : 0.82);
    final borderColor = dark
        ? Colors.white.withValues(alpha: 0.10)
        : Colors.black.withValues(alpha: 0.10);

    final panel = Container(
      padding: padding,
      decoration: BoxDecoration(
        color: fill,
        borderRadius: BorderRadius.circular(radius),
        border: Border.all(color: borderColor),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: dark ? 0.20 : 0.05),
            blurRadius: 24,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      child: child,
    );

    if (!blur) {
      return ClipRRect(
        borderRadius: BorderRadius.circular(radius),
        child: panel,
      );
    }

    return ClipRRect(
      borderRadius: BorderRadius.circular(radius),
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 18, sigmaY: 18),
        child: panel,
      ),
    );
  }
}
