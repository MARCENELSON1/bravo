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

  /// Agrega un ítem. `id` es un UUID de cliente → replay idempotente.
  /// Devuelve la orden autoritativa (el endpoint responde OrderResponse).
  Future<Order> addItem(
    String orderId, {
    required String id,
    required String productId,
    required int quantity,
    String? note,
  }) async {
    try {
      final res = await _dio.post<dynamic>(
        '/orders/$orderId/items',
        data: {
          'product_id': productId,
          'quantity': quantity,
          'id': id,
          'note': ?note,
        },
      );
      return await _order(res, orderId);
    } catch (e) {
      throw toApiError(e);
    }
  }

  Future<Order> setQuantity(String orderId, String itemId, int quantity) async {
    try {
      final res = await _dio.patch<dynamic>(
        '/orders/$orderId/items/$itemId',
        data: {'quantity': quantity},
      );
      return await _order(res, orderId);
    } catch (e) {
      throw toApiError(e);
    }
  }

  Future<Order> removeItem(String orderId, String itemId) async {
    try {
      final res = await _dio.delete<dynamic>('/orders/$orderId/items/$itemId');
      return await _order(res, orderId);
    } catch (e) {
      throw toApiError(e);
    }
  }

  /// Marcha a cocina (PENDING → SENT).
  Future<Order> send(String orderId) async {
    try {
      final res = await _dio.post<dynamic>('/orders/$orderId/send');
      return await _order(res, orderId);
    } catch (e) {
      throw toApiError(e);
    }
  }

  Future<Order> transfer(String orderId, String tableId) async {
    try {
      final res = await _dio.post<dynamic>(
        '/orders/$orderId/transfer',
        data: {'table_id': tableId},
      );
      return await _order(res, orderId);
    } catch (e) {
      throw toApiError(e);
    }
  }

  Future<Order> merge(String orderId, String sourceOrderId) async {
    try {
      final res = await _dio.post<dynamic>(
        '/orders/$orderId/merge',
        data: {'source_order_id': sourceOrderId},
      );
      return await _order(res, orderId);
    } catch (e) {
      throw toApiError(e);
    }
  }

  /// La mayoría de las mutaciones responden OrderResponse; si alguna respondiera
  /// vacío (204), caemos a un GET para tener la orden autoritativa.
  Future<Order> _order(Response<dynamic> res, String orderId) async {
    if (res.data is Map) {
      return Order.fromJson(Map<String, dynamic>.from(res.data as Map));
    }
    return get(orderId);
  }
}
