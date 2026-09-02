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

FloorView floorView(FloorTable table, {DateTime? now}) {
  final current = now ?? DateTime.now();
  final session = table.session;

  if (table.isFree || session == null) {
    return const FloorView(status: FloorStatus.free, attention: false);
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
