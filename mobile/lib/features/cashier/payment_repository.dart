import 'package:dio/dio.dart';

import '../../api/dio_errors.dart';
import '../order/order_dtos.dart';
import 'payment_dtos.dart';

class PaymentRepository {
  PaymentRepository(this._dio);

  final Dio _dio;

  Future<List<Payment>> list(String orderId) async {
    try {
      final res = await _dio.get<dynamic>('/orders/$orderId/payments');
      return (res.data as List)
          .map((e) => Payment.fromJson(Map<String, dynamic>.from(e as Map)))
          .toList();
    } catch (e) {
      throw toApiError(e);
    }
  }

  Future<Payment> register(
    String orderId, {
    required PaymentMethod method,
    required int amount,
    int tip = 0,
  }) async {
    try {
      final res = await _dio.post<dynamic>(
        '/orders/$orderId/payments',
        data: {'method': method.api, 'amount': amount, 'tip': tip},
      );
      return Payment.fromJson(Map<String, dynamic>.from(res.data as Map));
    } catch (e) {
      throw toApiError(e);
    }
  }

  Future<void> refund(String paymentId) async {
    try {
      await _dio.post<dynamic>('/payments/$paymentId/refund');
    } catch (e) {
      throw toApiError(e);
    }
  }

  Future<Order> reopen(String orderId) async {
    try {
      final res = await _dio.post<dynamic>('/orders/$orderId/reopen');
      return Order.fromJson(Map<String, dynamic>.from(res.data as Map));
    } catch (e) {
      throw toApiError(e);
    }
  }
}
