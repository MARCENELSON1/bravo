import '../order/order_dtos.dart';

/// Un ticket del KDS = un CURSO de una comanda (todos sus platos juntos), con
/// la demora en minutos desde que se marchó. La cocina lo bumpea entero:
/// "Empezar" cuando lo pone al fuego, "Listo" cuando terminó todos los platos
/// del tiempo. Un curso en espera (HELD) se ve —para el mise en place— pero no
/// se cocina hasta que el mozo lo marche.
class KdsTicket {
  const KdsTicket({
    required this.order,
    required this.course,
    required this.items,
    this.minutes,
  });

  final Order order;
  final Course course;
  final List<OrderItem> items;
  final int? minutes;

  bool get held => items.every((i) => i.status.isHeld);

  /// Hay platos sin empezar → la acción es "Empezar" (los pasa a preparando).
  bool get canStart => items.any((i) => i.status == ItemStatus.sent);

  /// Todo preparando → la acción es "Listo" (el curso entero).
  bool get canFinish =>
      !held && items.every((i) => i.status == ItemStatus.preparing);

  bool get isLate => !held && (minutes ?? 0) >= 10;
  bool get isWarn => !held && (minutes ?? 0) >= 5;
}

/// Agrupa las órdenes en tickets por (comanda, curso) con los platos activos
/// de la estación (HELD / SENT / PREPARING). Los que están al fuego van
/// primero, más viejo primero; los en espera, al final (se ven, no apuran).
List<KdsTicket> kdsTickets(List<Order> orders, {DateTime? now}) {
  final current = now ?? DateTime.now();
  final tickets = <KdsTicket>[];
  for (final order in orders) {
    final active = order.items
        .where((i) => i.status.isHeld || i.status.isFired)
        .toList();
    for (final course in Course.values) {
      final items = active.where((i) => i.course == course).toList();
      if (items.isEmpty) continue;
      DateTime? oldest;
      for (final i in items) {
        final t = i.sentAt;
        if (t != null && (oldest == null || t.isBefore(oldest))) oldest = t;
      }
      final raw = oldest == null ? null : current.difference(oldest).inMinutes;
      tickets.add(
        KdsTicket(
          order: order,
          course: course,
          items: items,
          minutes: raw == null || raw < 0 ? null : raw,
        ),
      );
    }
  }
  tickets.sort((a, b) {
    if (a.held != b.held) return a.held ? 1 : -1; // en espera al final
    final am = a.minutes, bm = b.minutes;
    if (am == null && bm == null) return 0;
    if (am == null) return 1;
    if (bm == null) return -1;
    return bm.compareTo(am); // más viejo (más minutos) primero
  });
  return tickets;
}
