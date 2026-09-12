import 'package:flutter/material.dart';

/// Fondo escénico de la app, en dos escenas — espejo de
/// `frontend/src/components/shell/app-background.tsx`.
///
/// El gradiente de base es el mismo en las dos. Lo que las separa es el cierre:
///
///  * **consola** — lleva la textura del mockup del hero de la landing (los
///    mismos valores, para que lo que se promete en la web sea lo que se ve al
///    entrar) y va SIN viñeta: la viñeta oscurece justo los bordes, que es donde
///    se apoyan los paneles de vidrio.
///  * **identidad** — el login y sus hermanas. Sin textura y CON viñeta: ahí el
///    fondo se ve directo, sin paneles que lo filtren, así que el mismo
///    tratamiento pesaría mucho más.
///
/// La textura va desaturada y en modo `softLight`: la foto es verde, y a color
/// le devolvería a la base el tinte que justamente no tiene que tener.
///
/// **Por qué es neutro y no verde.** El fondo anterior era un gradiente verde con
/// una textura fotográfica de 2,4 MB. Cuando el fondo también es verde, el verde
/// de marca deja de destacarse contra él: el acento se pierde en su propio tono.
/// El web hizo este cambio el 5 de septiembre; el móvil se había quedado atrás.
///
/// Cinco capas, en este orden exacto:
///
///  1. gradiente neutro por tema
///  2. grano fino — va DEBAJO de las manchas; encima obligaría a recomponer la
///     mezcla en cada cuadro de la animación
///  3. tres manchas de luz que derivan solas, muy lento
///  4. viñeta, que cierra los bordes
///
/// Es un `Positioned.fill`: va dentro de un `Stack`. Lo pinta el `builder` de
/// `MaterialApp` una sola vez para toda la app.
enum BackgroundScene { console, identity }

class AppBackground extends StatefulWidget {
  const AppBackground({super.key, this.scene = BackgroundScene.console});

  final BackgroundScene scene;

  @override
  State<AppBackground> createState() => _AppBackgroundState();
}

class _AppBackgroundState extends State<AppBackground>
    with SingleTickerProviderStateMixin {
  /// Un solo controlador para las tres manchas. El web les da 90, 115 y 140
  /// segundos; acá un ciclo largo con tres desfasajes da la misma sensación de
  /// que nunca se repiten, con un timer en vez de tres.
  late final AnimationController _drift = AnimationController(
    vsync: this,
    duration: const Duration(seconds: 120),
  )..repeat(reverse: true);

  @override
  void dispose() {
    _drift.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final dark = Theme.of(context).brightness == Brightness.dark;
    final identity = widget.scene == BackgroundScene.identity;
    // "Reducir movimiento" (Ajustes) y el ajuste del sistema: las manchas quedan
    // quietas. El fondo sigue estando; lo que se apaga es la deriva.
    final still = MediaQuery.of(context).disableAnimations;
    if (still && _drift.isAnimating) _drift.stop();
    if (!still && !_drift.isAnimating) _drift.repeat(reverse: true);

    final base = dark
        ? const [Color(0xFF1D1D1D), Color(0xFF131313), Color(0xFF0A0A0A)]
        : const [Color(0xFFF6F6F6), Color(0xFFE9E9E9), Color(0xFFD7D7D7)];
    final stops = dark ? const [0.0, 0.52, 1.0] : const [0.0, 0.5, 1.0];

    // Manchas: color y opacidad de `--aurora-a/b/c`.
    final blobs = dark
        ? const [
            (Color(0xFFC4C4C4), 0.15),
            (Color(0xFFB1B1B1), 0.11),
            (Color(0xFFD7D7D7), 0.08),
          ]
        : const [
            (Color(0xFF424242), 0.16),
            (Color(0xFF333333), 0.12),
            (Color(0xFF555555), 0.09),
          ];
    final vignette = dark
        ? const Color(0xFF000000).withValues(alpha: 0.40)
        : const Color(0xFF161616).withValues(alpha: 0.10);

    return Positioned.fill(
      child: RepaintBoundary(
        child: LayoutBuilder(
          builder: (context, c) {
            final w = c.maxWidth, h = c.maxHeight;
            return Stack(
              children: [
                // 1 · Base. `at 18% 12%` → Alignment(-0.64, -0.76); radio 1.25.
                DecoratedBox(
                  decoration: BoxDecoration(
                    gradient: RadialGradient(
                      center: const Alignment(-0.64, -0.76),
                      radius: 1.25,
                      colors: base,
                      stops: stops,
                    ),
                  ),
                  child: const SizedBox.expand(),
                ),
                // 2 · Grano. Teselado, debajo de las manchas. Más marcado en la
                // consola, donde los paneles de vidrio lo suavizan.
                // Va como `DecorationImage` y no como `Image`: dentro de un Stack
                // una Image toma su tamaño intrínseco (220×220) y el teselado se
                // queda en ese cuadrado, con un borde duro arriba a la izquierda.
                Opacity(
                  opacity: identity ? 0.12 : 0.18,
                  child: DecoratedBox(
                    decoration: const BoxDecoration(
                      image: DecorationImage(
                        image: AssetImage('assets/img/grain.png'),
                        repeat: ImageRepeat.repeat,
                        filterQuality: FilterQuality.none,
                      ),
                    ),
                    child: const SizedBox.expand(),
                  ),
                ),
                // 3 · Textura, solo en la consola. Desaturada y en `softLight`:
                // modula el valor en vez de taparlo, y no le devuelve el verde.
                if (!identity)
                  Opacity(
                    opacity: 0.5,
                    child: ColorFiltered(
                      colorFilter: const ColorFilter.matrix(_grayscale),
                      child: DecoratedBox(
                        decoration: const BoxDecoration(
                          image: DecorationImage(
                            image: AssetImage('assets/img/app-bg-texture.webp'),
                            fit: BoxFit.cover,
                          ),
                        ),
                        child: const SizedBox.expand(),
                      ),
                    ),
                  ),
                // 3 · Las tres manchas.
                AnimatedBuilder(
                  animation: _drift,
                  builder: (context, _) {
                    final t = Curves.easeInOut.transform(_drift.value);
                    return Stack(
                      children: [
                        // a: arriba a la izquierda, la más grande.
                        _Blob(
                          left: -0.05 * w,
                          top: -0.10 * h,
                          size: 0.55 * w,
                          color: blobs[0].$1,
                          opacity: blobs[0].$2,
                          dx: 0.06 * w * t,
                          dy: 0.04 * h * t,
                        ),
                        // b: a la derecha, medio alto, deriva al contrario.
                        _Blob(
                          left: w - 0.30 * w,
                          top: 0.25 * h,
                          size: 0.45 * w,
                          color: blobs[1].$1,
                          opacity: blobs[1].$2,
                          dx: -0.07 * w * t,
                          dy: -0.05 * h * t,
                        ),
                        // c: abajo, la más ancha y la más tenue.
                        _Blob(
                          left: 0.20 * w,
                          top: h - 0.30 * h,
                          size: 0.60 * w,
                          color: blobs[2].$1,
                          opacity: blobs[2].$2,
                          dx: 0.05 * w * t,
                          dy: -0.03 * h * t,
                        ),
                      ],
                    );
                  },
                ),
                // 5 · Viñeta: solo en identidad, donde no hay panel que ocupe
                // todo. En la consola oscurecería los bordes, que es donde se
                // apoyan los paneles.
                if (identity)
                  DecoratedBox(
                    decoration: BoxDecoration(
                      gradient: RadialGradient(
                        center: const Alignment(0, -0.24), // at 50% 38%
                        radius: 0.95,
                        colors: [Colors.transparent, vignette],
                        stops: const [0.0, 1.0],
                      ),
                    ),
                    child: const SizedBox.expand(),
                  ),
              ],
            );
          },
        ),
      ),
    );
  }
}

/// Desaturación total (luma Rec. 709) — el equivalente de `grayscale` en CSS.
const _grayscale = <double>[
  0.2126,
  0.7152,
  0.0722,
  0,
  0,
  0.2126,
  0.7152,
  0.0722,
  0,
  0,
  0.2126,
  0.7152,
  0.0722,
  0,
  0,
  0,
  0,
  0,
  1,
  0,
];

/// Una mancha de luz: círculo con degradado radial que se desvanece al 72%,
/// igual que `.aurora-*` en el web.
class _Blob extends StatelessWidget {
  const _Blob({
    required this.left,
    required this.top,
    required this.size,
    required this.color,
    required this.opacity,
    required this.dx,
    required this.dy,
  });

  final double left, top, size, opacity, dx, dy;
  final Color color;

  @override
  Widget build(BuildContext context) {
    final c = color.withValues(alpha: opacity);
    return Positioned(
      left: left + dx,
      top: top + dy,
      width: size,
      height: size,
      child: DecoratedBox(
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          gradient: RadialGradient(
            colors: [c, c, Colors.transparent],
            stops: const [0.0, 0.14, 0.72],
          ),
        ),
      ),
    );
  }
}
