import 'package:dio/dio.dart';

import 'api_error.dart';

/// Normaliza cualquier error de red a `ApiError` (mismo criterio que F0).
ApiError toApiError(Object e) {
  if (e is ApiError) return e;
  if (e is DioException) {
    final res = e.response;
    if (res != null) return ApiError.fromResponse(res.statusCode, res.data);
    return const ApiError(
      code: 'network_error',
      message: 'No pudimos conectar. Revisá tu conexión.',
    );
  }
  return const ApiError(code: 'unknown_error', message: 'Ocurrió un error.');
}
