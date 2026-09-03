/// Un turno fichado (backend `ShiftResponse`).
class Shift {
  const Shift({
    required this.id,
    required this.userId,
    required this.status,
    required this.clockInAt,
    this.clockOutAt,
    this.workedMinutes,
    this.note,
  });

  final String id;
  final String userId;
  final String status;
  final DateTime clockInAt;
  final DateTime? clockOutAt;
  final int? workedMinutes;
  final String? note;

  bool get isOpen => clockOutAt == null;

  factory Shift.fromJson(Map<String, dynamic> j) => Shift(
        id: j['id'] as String,
        userId: j['user_id'] as String,
        status: j['status'] as String,
        clockInAt: DateTime.parse(j['clock_in_at'] as String).toLocal(),
        clockOutAt: _date(j['clock_out_at']),
        workedMinutes: j['worked_minutes'] as int?,
        note: j['note'] as String?,
      );
}

/// Estado de fichaje del usuario (backend `MyTimeclockResponse`).
class MyTimeclock {
  const MyTimeclock({this.openShift, this.recent = const []});

  final Shift? openShift;
  final List<Shift> recent;

  bool get isClockedIn => openShift != null;

  factory MyTimeclock.fromJson(Map<String, dynamic> j) => MyTimeclock(
        openShift: j['open_shift'] == null
            ? null
            : Shift.fromJson(Map<String, dynamic>.from(j['open_shift'] as Map)),
        recent: ((j['recent'] as List?) ?? const [])
            .map((e) => Shift.fromJson(Map<String, dynamic>.from(e as Map)))
            .toList(),
      );
}

DateTime? _date(Object? v) => v is String ? DateTime.tryParse(v)?.toLocal() : null;
