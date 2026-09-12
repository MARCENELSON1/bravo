import 'package:dio/dio.dart';

import '../../api/dio_errors.dart';
import 'cash_dtos.dart';

class CashRepository {
  CashRepository(this._dio);

  final Dio _dio;

  /// Sesión de caja abierta, o null si no hay ninguna.
  Future<CashSession?> current() async {
    try {
      final res = await _dio.get<dynamic>('/cashier/session/current');
      if (res.data is! Map) return null;
      return CashSession.fromJson(Map<String, dynamic>.from(res.data as Map));
    } on DioException catch (e) {
      if (e.response?.statusCode == 404) return null;
      throw toApiError(e);
    } catch (e) {
      throw toApiError(e);
    }
  }

  Future<CashSession> open(int openingFloatAmount, {String? note}) async {
    try {
      final res = await _dio.post<dynamic>(
        '/cashier/session/open',
        data: {'opening_float_amount': openingFloatAmount, 'note': ?note},
      );
      return CashSession.fromJson(Map<String, dynamic>.from(res.data as Map));
    } catch (e) {
      throw toApiError(e);
    }
  }

  /// Cierra la caja con lo contado por método (arqueo Z). `counted` = { 'CASH': 79500, ... }.
  Future<CashReport> close(
    String sessionId,
    Map<String, int> counted, {
    String? note,
  }) async {
    try {
      final res = await _dio.post<dynamic>(
        '/cashier/session/$sessionId/close',
        data: {'counted': counted, 'note': ?note},
      );
      return CashReport.fromJson(Map<String, dynamic>.from(res.data as Map));
    } catch (e) {
      throw toApiError(e);
    }
  }
}
