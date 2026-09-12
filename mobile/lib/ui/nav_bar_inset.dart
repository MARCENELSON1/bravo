import 'dart:math' as math;

import 'package:flutter/widgets.dart';

/// Cuánto aire dejar al final de una pantalla para que su último elemento pueda
/// subir por encima de la barra de navegación.
///
/// La barra dejó de ocupar su propio pedazo de pantalla y pasó a ser una
/// pastilla que flota sobre el contenido (ver `app_scaffold._GlassNavBar`). Eso
/// es lo que hace que el vidrio se lea como vidrio —difumina la lista que le
/// pasa por debajo, no un fondo quieto— pero también significa que ya nada
/// garantiza que lo último de la lista se pueda leer: sin este espacio, el
/// último ítem queda tapado para siempre.
///
/// El número lo publica el propio `Scaffold` cuando `extendBody` está prendido:
/// es el alto de la barra. En una pantalla que se empuja encima —que no tiene
/// barra— cae al área segura del teléfono, que es justo lo que corresponde.
double navBarInset(BuildContext context) =>
    MediaQuery.paddingOf(context).bottom;

/// Cuánto subir un botón flotante para que la barra no se le siente encima.
///
/// No sirve [navBarInset] acá: una pantalla con `Scaffold` propio ya ubica su
/// botón por encima del área segura del teléfono, así que sumarle el alto de la
/// barra entera lo dejaría flotando de más. Lo que falta es solo la diferencia
/// —lo que la barra ocupa por arriba de esa área segura—, y en una pantalla que
/// se empuja encima, donde no hay barra, esa diferencia es cero y nada se mueve.
double navBarOverlap(BuildContext context) {
  final mq = MediaQuery.of(context);
  return math.max(mq.padding.bottom - mq.viewPadding.bottom, 0);
}
