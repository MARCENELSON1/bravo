import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/api_client.dart';
import '../../api/dio_errors.dart';

/// Registra el push token del device en el backend (`POST /devices`, Fase 4).
class DeviceRepository {
  DeviceRepository(this._dio);
  final Dio _dio;

  Future<void> register(String token, String platform) async {
    try {
      await _dio.post<dynamic>(
        '/devices',
        data: {'token': token, 'platform': platform},
      );
    } catch (e) {
      throw toApiError(e);
    }
  }
}

final deviceRepositoryProvider = Provider<DeviceRepository>(
  (ref) => DeviceRepository(ref.read(apiDioProvider)),
);
