import 'package:dio/dio.dart';

import '../../api/dio_errors.dart';
import 'floor_dtos.dart';

/// Datos del piso. Usa el `apiDio` autenticado de F0.
class FloorRepository {
  FloorRepository(this._dio);

  final Dio _dio;

  Future<List<FloorTable>> floor() async {
    try {
      final res = await _dio.get<dynamic>('/floor');
      return (res.data as List)
          .map((e) => FloorTable.fromJson(Map<String, dynamic>.from(e as Map)))
          .toList();
    } catch (e) {
      throw toApiError(e);
    }
  }

  Future<List<Sector>> sectors() async {
    try {
      final res = await _dio.get<dynamic>('/sectors');
      return (res.data as List)
          .map((e) => Sector.fromJson(Map<String, dynamic>.from(e as Map)))
          .toList();
    } catch (e) {
      throw toApiError(e);
    }
  }

  /// Abrir mesa (idempotente por mesa en el backend). Devuelve el session id.
  Future<String> openSession(String tableId, {int? pax}) async {
    try {
      final res = await _dio.post<dynamic>(
        '/floor/sessions',
        data: {'table_id': tableId, 'pax': ?pax},
      );
      return (res.data as Map)['id'] as String;
    } catch (e) {
      throw toApiError(e);
    }
  }

  Future<void> requestBill(String sessionId) async {
    try {
      await _dio.post<dynamic>('/floor/sessions/$sessionId/bill');
    } catch (e) {
      throw toApiError(e);
    }
  }
}
