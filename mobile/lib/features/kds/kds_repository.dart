import 'package:dio/dio.dart';

import '../../api/dio_errors.dart';
import '../order/order_dtos.dart';

/// Datos del KDS (cocina). Usa el `apiDio` autenticado.
class KdsRepository {
  KdsRepository(this._dio);

  final Dio _dio;

  Future<List<Order>> orders(Station station) async {
    try {
      final res = await _dio.get<dynamic>(
        '/kds/orders',
        queryParameters: {'station': station == Station.bar ? 'BAR' : 'KITCHEN'},
      );
      return (res.data as List)
          .map((e) => Order.fromJson(Map<String, dynamic>.from(e as Map)))
          .toList();
    } catch (e) {
      throw toApiError(e);
    }
  }

  /// Avanza un ítem: action ∈ preparing | ready | served | recall.
  Future<Order> advanceItem(String orderId, String itemId, String action) async {
    try {
      final res = await _dio.post<dynamic>('/orders/$orderId/items/$itemId/$action');
      return Order.fromJson(Map<String, dynamic>.from(res.data as Map));
    } catch (e) {
      throw toApiError(e);
    }
  }

  /// Mapa id→número de mesa para etiquetar los tickets. Best-effort: si el rol
  /// KITCHEN no puede leer `/tables`, devuelve un mapa vacío.
  Future<Map<String, int>> tableNumbers() async {
    try {
      final res = await _dio.get<dynamic>('/tables');
      final map = <String, int>{};
      for (final e in res.data as List) {
        final m = Map<String, dynamic>.from(e as Map);
        map[m['id'] as String] = m['number'] as int;
      }
      return map;
    } catch (_) {
      return {};
    }
  }
}
