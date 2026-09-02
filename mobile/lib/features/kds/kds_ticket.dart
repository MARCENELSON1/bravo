import '../order/order_dtos.dart';

/// Un ticket del KDS = un ítem despachado en su orden, con la demora en minutos.
class KdsTicket {
  const KdsTicket({required this.order, required this.item, this.minutes});

  final Order order;
  final OrderItem item;
  final int? minutes;

  bool get isLate => (minutes ?? 0) >= 10;
  bool get isWarn => (minutes ?? 0) >= 5;
}

/// Aplana las órdenes en tickets por ítem (solo SENT/PREPARING), más viejo
/// primero (por `sent_at`). Espeja `frontend/src/lib/kds.ts` (`kdsTickets`).
List<KdsTicket> kdsTickets(List<Order> orders, {DateTime? now}) {
  final current = now ?? DateTime.now();
  final tickets = <KdsTicket>[];
  for (final order in orders) {
    for (final item in order.items) {
      if (item.status == ItemStatus.sent || item.status == ItemStatus.preparing) {
        final raw =
            item.sentAt == null ? null : current.difference(item.sentAt!).inMinutes;
        tickets.add(KdsTicket(
          order: order,
          item: item,
          minutes: raw == null || raw < 0 ? null : raw,
        ));
      }
    }
  }
  tickets.sort((a, b) {
    final at = a.item.sentAt;
    final bt = b.item.sentAt;
    if (at == null && bt == null) return 0;
    if (at == null) return 1;
    if (bt == null) return -1;
    return at.compareTo(bt); // más viejo primero
  });
  return tickets;
}
