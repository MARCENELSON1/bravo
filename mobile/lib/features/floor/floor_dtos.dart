import '../order/order_dtos.dart';

// DTOs del piso contra los schemas reales (FloorTableResponse /
// FloorSessionResponse / SectorResponse de openapi.json).

/// Estado de la visita (backend `SessionStatus`).
enum SessionState {
  open,
  inKitchen,
  toServe,
  served,
  toCharge,
  closed;

  static SessionState fromApi(String v) => switch (v) {
        'OPEN' => SessionState.open,
        'IN_KITCHEN' => SessionState.inKitchen,
        'TO_SERVE' => SessionState.toServe,
        'SERVED' => SessionState.served,
        'TO_CHARGE' => SessionState.toCharge,
        'CLOSED' => SessionState.closed,
        _ => SessionState.open,
      };

  /// Clave i18n del estado (el texto se traduce; la clave es el código).
  String get apiKey => switch (this) {
        SessionState.open => 'OPEN',
        SessionState.inKitchen => 'IN_KITCHEN',
        SessionState.toServe => 'TO_SERVE',
        SessionState.served => 'SERVED',
        SessionState.toCharge => 'TO_CHARGE',
        SessionState.closed => 'CLOSED',
      };
}

class FloorSession {
  const FloorSession({
    required this.id,
    required this.state,
    this.stateSince,
    this.pax,
    this.waiterId,
    this.waiterName,
    this.sectorId,
  });

  final String id;
  final SessionState state;
  final DateTime? stateSince;
  final int? pax;
  final String? waiterId;
  final String? waiterName;
  final String? sectorId;

  factory FloorSession.fromJson(Map<String, dynamic> j) => FloorSession(
        id: j['id'] as String,
        state: SessionState.fromApi(j['state'] as String),
        stateSince: _date(j['state_since']),
        pax: j['pax'] as int?,
        waiterId: j['waiter_id'] as String?,
        waiterName: j['waiter_name'] as String?,
        sectorId: j['sector_id'] as String?,
      );
}

class FloorTable {
  const FloorTable({
    required this.id,
    required this.number,
    required this.status,
    this.name,
    this.activeOrder,
    this.session,
    this.sectorId,
    this.capacity,
  });

  final String id;
  final int number;
  final String status; // "FREE" | "OCCUPIED"
  final String? name;
  final Order? activeOrder;
  final FloorSession? session;
  final String? sectorId;
  final int? capacity;

  bool get isFree => status == 'FREE' || session == null;

  factory FloorTable.fromJson(Map<String, dynamic> j) => FloorTable(
        id: j['id'] as String,
        number: j['number'] as int,
        status: j['status'] as String,
        name: j['name'] as String?,
        activeOrder: j['active_order'] == null
            ? null
            : Order.fromJson(Map<String, dynamic>.from(j['active_order'] as Map)),
        session: j['session'] == null
            ? null
            : FloorSession.fromJson(Map<String, dynamic>.from(j['session'] as Map)),
        sectorId: j['sector_id'] as String?,
        capacity: j['capacity'] as int?,
      );
}

class Sector {
  const Sector({
    required this.id,
    required this.name,
    required this.sortOrder,
    this.color,
  });

  final String id;
  final String name;
  final int sortOrder;
  final String? color;

  factory Sector.fromJson(Map<String, dynamic> j) => Sector(
        id: j['id'] as String,
        name: j['name'] as String,
        sortOrder: (j['sort_order'] as int?) ?? 0,
        color: j['color'] as String?,
      );
}

DateTime? _date(Object? v) => v is String ? DateTime.tryParse(v)?.toLocal() : null;
