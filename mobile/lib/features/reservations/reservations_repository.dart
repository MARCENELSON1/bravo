import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/api_client.dart';
import '../../api/dio_errors.dart';

/// Una reserva (backend `ReservationResponse`).
class Reservation {
  const Reservation({
    required this.id,
    required this.customerName,
    required this.partySize,
    required this.reservedAt,
    required this.turn,
    required this.status,
    this.customerPhone,
    this.tableId,
    this.note,
  });
  final String id;
  final String customerName;
  final int partySize;
  final String reservedAt;
  final String turn; // LUNCH | DINNER
  final String status; // PENDING | CONFIRMED | SEATED | COMPLETED | CANCELLED | NO_SHOW
  final String? customerPhone;
  final String? tableId;
  final String? note;

  factory Reservation.fromJson(Map<String, dynamic> j) => Reservation(
        id: j['id'] as String,
        customerName: (j['customer_name'] as String?) ?? '',
        partySize: (j['party_size'] as int?) ?? 0,
        reservedAt: (j['reserved_at'] as String?) ?? '',
        turn: (j['turn'] as String?) ?? 'DINNER',
        status: (j['status'] as String?) ?? 'PENDING',
        customerPhone: j['customer_phone'] as String?,
        tableId: j['table_id'] as String?,
        note: j['note'] as String?,
      );
}

/// Clave de la query de reservas: día (yyyy-MM-dd) + turno opcional.
typedef ReservationsQuery = ({String day, String? turn});

class ReservationsRepository {
  ReservationsRepository(this._dio);
  final Dio _dio;

  Future<List<Reservation>> list(ReservationsQuery q) async {
    try {
      final from = DateTime.parse('${q.day}T00:00:00').toUtc().toIso8601String();
      final to = DateTime.parse('${q.day}T23:59:59').toUtc().toIso8601String();
      final res = await _dio.get<dynamic>('/reservations', queryParameters: {
        'from': from,
        'to': to,
        if (q.turn != null) 'turn': q.turn,
      });
      return ((res.data as List?) ?? const [])
          .map((e) => Reservation.fromJson(Map<String, dynamic>.from(e as Map)))
          .toList();
    } catch (e) {
      throw toApiError(e);
    }
  }

  Future<void> create({
    required String customerName,
    required int partySize,
    required String reservedAtIso,
    required String turn,
    String? customerPhone,
    String? tableId,
    String? note,
  }) async {
    try {
      await _dio.post<dynamic>('/reservations', data: {
        'customer_name': customerName,
        'party_size': partySize,
        'reserved_at': reservedAtIso,
        'turn': turn,
        'customer_phone': customerPhone,
        'table_id': tableId,
        'note': note,
      });
    } catch (e) {
      throw toApiError(e);
    }
  }

  /// `action`: confirm | seat | complete | cancel | no-show.
  Future<void> transition(String id, String action) async {
    try {
      await _dio.post<dynamic>('/reservations/$id/$action');
    } catch (e) {
      throw toApiError(e);
    }
  }
}

final reservationsRepositoryProvider = Provider<ReservationsRepository>(
  (ref) => ReservationsRepository(ref.read(apiDioProvider)),
);

final reservationsProvider =
    FutureProvider.autoDispose.family<List<Reservation>, ReservationsQuery>(
  (ref, q) => ref.read(reservationsRepositoryProvider).list(q),
);
