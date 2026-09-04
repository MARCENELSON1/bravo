import 'floor_dtos.dart';

/// Estado visual de una mesa en el piso (derivado, no almacenado).
enum FloorStatus { free, open, inKitchen, toServe, served, toCharge, closed }

/// Vista derivada de una mesa: alimenta color, timer y chips de forma
/// consistente. Espeja `frontend/src/lib/floor-session.ts` (`floorView`).
class FloorView {
  const FloorView({
    required this.status,
    required this.attention,
    this.minutes,
    this.pax,
    this.waiterName,
    this.totalAmount,
    this.currency,
  });

  final FloorStatus status;
  final bool attention; // TO_SERVE || TO_CHARGE
  final int? minutes; // desde state_since
  final int? pax;
  final String? waiterName;
  final int? totalAmount;
  final String? currency;
}

/// Estado de piso derivado de una orden activa SIN sesión (mesa que pidió por
/// QR y todavía no tiene mozo/sesión). Espeja `stateFromOrder` de la web.
FloorStatus _statusFromOrder(String orderStatus) {
  switch (orderStatus) {
    case 'SENT':
    case 'PREPARING':
      return FloorStatus.inKitchen;
    case 'READY':
      return FloorStatus.toServe;
    case 'SERVED':
      return FloorStatus.served;
    case 'OPEN':
    default:
      return FloorStatus.open;
  }
}

FloorView floorView(FloorTable table, {DateTime? now}) {
  final current = now ?? DateTime.now();
  final session = table.session;

  // Sin sesión: o la mesa está libre (sin orden), o pidió por QR y aún no tiene
  // mozo (orden activa sin sesión) → derivamos el estado de la orden, no la
  // damos por "libre" (paridad con la web `floorView`).
  if (session == null) {
    final order = table.activeOrder;
    if (order == null) {
      return const FloorView(status: FloorStatus.free, attention: false);
    }
    final status = _statusFromOrder(order.status);
    final since = order.createdAt;
    final minutes = since == null ? null : current.difference(since).inMinutes;
    return FloorView(
      status: status,
      attention: status == FloorStatus.toServe,
      minutes: minutes == null || minutes < 0 ? null : minutes,
      pax: table.capacity,
      totalAmount: order.totalAmount,
      currency: order.currency,
    );
  }

  final status = switch (session.state) {
    SessionState.open => FloorStatus.open,
    SessionState.inKitchen => FloorStatus.inKitchen,
    SessionState.toServe => FloorStatus.toServe,
    SessionState.served => FloorStatus.served,
    SessionState.toCharge => FloorStatus.toCharge,
    SessionState.closed => FloorStatus.closed,
  };

  final attention =
      session.state == SessionState.toServe || session.state == SessionState.toCharge;

  final since = session.stateSince ?? table.activeOrder?.createdAt;
  final minutes = since == null ? null : current.difference(since).inMinutes;

  return FloorView(
    status: status,
    attention: attention,
    minutes: minutes == null || minutes < 0 ? null : minutes,
    pax: session.pax ?? table.capacity,
    waiterName: session.waiterName,
    totalAmount: table.activeOrder?.totalAmount,
    currency: table.activeOrder?.currency,
  );
}
