import 'package:dio/dio.dart';

import '../auth/token_store.dart';

typedef RefreshCallback = Future<bool> Function();

/// Interceptor de auth (espeja el single-flight 401→refresh de `http-client.ts`):
/// - Adjunta `Authorization: Bearer <access>` si hay token.
/// - Ante un `401` (que no sea del propio refresh), dispara UN refresh
///   (el single-flight vive en `AuthRepository.tryRefreshSession`) y reintenta
///   la request UNA vez con el nuevo access. Si el refresh falla, propaga el error.
///
/// `QueuedInterceptor` serializa el manejo de errores concurrentes; el reintento
/// se hace con un `Dio` limpio (sin interceptores) para no reentrar.
class AuthInterceptor extends QueuedInterceptor {
  AuthInterceptor({required this.tokenStore, required this.refresh});

  final TokenStore tokenStore;
  final RefreshCallback refresh;

  static const String _retriedFlag = '__wellnod_retried__';

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    final token = tokenStore.accessToken;
    if (token != null && options.headers['Authorization'] == null) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    handler.next(options);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) async {
    final status = err.response?.statusCode;
    final alreadyRetried = err.requestOptions.extra[_retriedFlag] == true;

    if (status == 401 && !alreadyRetried) {
      final refreshed = await refresh();
      if (refreshed) {
        final req = err.requestOptions;
        req.extra[_retriedFlag] = true;
        req.headers['Authorization'] = 'Bearer ${tokenStore.accessToken}';
        try {
          final response = await Dio().fetch<dynamic>(req);
          return handler.resolve(response);
        } on DioException catch (retryErr) {
          return handler.next(retryErr);
        }
      }
    }
    handler.next(err);
  }
}
