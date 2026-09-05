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
    List<String>? optionIds,
  }) async {
    try {
      final res = await _dio.post<dynamic>(
        '/orders/$orderId/items',
        data: {
          'product_id': productId,
          'quantity': quantity,
          'id': id,
          'note': ?note,
          // Lista (aunque vacía) = el server valida los grupos obligatorios.
          'option_ids': ?optionIds,
        },
      );
      return await _order(res, orderId);
    } catch (e) {
      throw toApiError(e);
    }
  }

  /// Nota de cocina de una línea PENDING ("cómo se quiere el plato").
  /// null / vacío la borra. Una vez marchada, el backend la congela (409).
  Future<Order> setNote(String orderId, String itemId, String? note) async {
    try {
      final res = await _dio.patch<dynamic>(
        '/orders/$orderId/items/$itemId/note',
        data: {'note': note},
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

  /// Marca la comanda como servida (READY → SERVED). Desde el modal "comanda lista".
  Future<Order> markServed(String orderId) async {
    try {
      final res = await _dio.post<dynamic>('/orders/$orderId/served');
      return await _order(res, orderId);
    } catch (e) {
      throw toApiError(e);
    }
  }

  /// Marcha a cocina (PENDING → SENT). Confirmar un pedido QR pasa por acá: el
  /// mozo que lo confirma queda dueño de la mesa (Fase 2, backend).
  Future<Order> send(String orderId) async {
    try {
      final res = await _dio.post<dynamic>('/orders/$orderId/send');
      return await _order(res, orderId);
    } catch (e) {
      throw toApiError(e);
    }
  }

  /// Bandeja "QR por confirmar": pedidos que el comensal hizo por QR y siguen
  /// OPEN (sin marchar). El mozo confirma uno con [send].
  Future<List<Order>> pendingQr() async {
    try {
      final res = await _dio.get<dynamic>('/orders/pending-qr');
      return (res.data as List)
          .map((e) => Order.fromJson(Map<String, dynamic>.from(e as Map)))
          .toList();
    } catch (e) {
      throw toApiError(e);
    }
  }

  /// Tomar una mesa huérfana: el mozo que llama queda dueño (409 si ya tiene dueño).
  Future<Order> claim(String orderId) async {
    try {
      final res = await _dio.post<dynamic>('/orders/$orderId/claim');
      return await _order(res, orderId);
    } catch (e) {
      throw toApiError(e);
    }
  }

  /// Liberar la mesa de una comanda ya paga (Autoservicio): la marca PAGADA para
  /// que se libere del plano. 409 si todavía tiene saldo (usar el cobro normal).
  Future<Order> free(String orderId) async {
    try {
      final res = await _dio.post<dynamic>('/orders/$orderId/free');
      return await _order(res, orderId);
    } catch (e) {
      throw toApiError(e);
    }
  }

  /// Reasignar el mozo dueño de la mesa (encargado): pisa el dueño actual.
  Future<Order> assignWaiter(String orderId, String waiterId) async {
    try {
      final res = await _dio.post<dynamic>(
        '/orders/$orderId/assign-waiter',
        data: {'waiter_id': waiterId},
      );
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
