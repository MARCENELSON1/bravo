import 'package:dio/dio.dart';

import '../../api/dio_errors.dart';
import 'order_dtos.dart';

/// Órdenes (Tanda 1: crear + leer; Tanda 2 agrega la captura completa).
class OrderRepository {
  OrderRepository(this._dio);

  final Dio _dio;

  /// Crea una orden para la mesa. `id` es un UUID de cliente → replay idempotente
  /// (el backend abre la sesión de la mesa implícitamente si no existe).
  Future<String> create({required String tableId, required String id}) async {
    try {
      final res = await _dio.post<dynamic>(
        '/orders',
        data: {'table_id': tableId, 'id': id},
      );
      return (res.data as Map)['order_id'] as String;
    } catch (e) {
      throw toApiError(e);
    }
  }

  Future<Order> get(String orderId) async {
    try {
      final res = await _dio.get<dynamic>('/orders/$orderId');
      return Order.fromJson(Map<String, dynamic>.from(res.data as Map));
    } catch (e) {
      throw toApiError(e);
    }
  }
}
