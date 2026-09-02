import 'package:dio/dio.dart';

import '../api/api_error.dart';
import 'dtos.dart';
import 'refresh_cookie.dart';
import 'token_store.dart';

/// Cliente de auth. Espeja `frontend/src/api/auth-api.ts`.
///
/// - `login`/`tryRefreshSession`/`logout` usan `rawDio` (sin interceptor): manejan
///   los tokens explícitamente.
/// - `me` usa `apiDio` (con `AuthInterceptor`): se beneficia del refresh automático.
///
/// El backend YA acepta el refresh por body (`{"refresh_token": ...}`), así que no
/// hace falta ningún cambio de backend (probado en `test_e2e_auth.py`).
class AuthRepository {
  AuthRepository(this._rawDio, this._apiDio, this._tokenStore);

  final Dio _rawDio;
  final Dio _apiDio;
  final TokenStore _tokenStore;

  Future<bool>? _refreshing;

  /// `POST /auth/login` — form-urlencoded, el tenant slug viaja en `client_id`
  /// (OAuth2PasswordRequestForm). Guarda el access (body) y el refresh (Set-Cookie).
  Future<void> login({
    required String slug,
    required String email,
    required String password,
  }) async {
    try {
      final res = await _rawDio.post<dynamic>(
        '/auth/login',
        data: {'username': email, 'password': password, 'client_id': slug},
        options: Options(contentType: Headers.formUrlEncodedContentType),
      );
      final tokens =
          AccessTokenResponse.fromJson(Map<String, dynamic>.from(res.data as Map));
      _tokenStore.setAccessToken(tokens.accessToken);
      final refresh = extractRefreshCookie(res.headers.map['set-cookie']);
      if (refresh != null) await _tokenStore.writeRefresh(refresh);
    } on DioException catch (e) {
      throw _toApiError(e);
    }
  }

  /// `GET /me` (Bearer). Devuelve el perfil para hidratar la sesión.
  Future<MeResponse> me() async {
    try {
      final res = await _apiDio.get<dynamic>('/me');
      return MeResponse.fromJson(Map<String, dynamic>.from(res.data as Map));
    } on DioException catch (e) {
      throw _toApiError(e);
    }
  }

  /// Refresca la sesión con single-flight (una sola llamada en vuelo).
  Future<bool> tryRefreshSession() =>
      _refreshing ??= _refresh().whenComplete(() => _refreshing = null);

  Future<bool> _refresh() async {
    final stored = await _tokenStore.readRefresh();
    if (stored == null) return false;
    try {
      final res = await _rawDio.post<dynamic>(
        '/auth/refresh',
        data: {'refresh_token': stored},
      );
      final tokens =
          AccessTokenResponse.fromJson(Map<String, dynamic>.from(res.data as Map));
      _tokenStore.setAccessToken(tokens.accessToken);
      final rotated = extractRefreshCookie(res.headers.map['set-cookie']);
      if (rotated != null) await _tokenStore.writeRefresh(rotated);
      return true;
    } on DioException {
      // Refresh inválido/expirado/revocado → sesión perdida.
      await _tokenStore.clear();
      return false;
    }
  }

  /// `POST /auth/logout` (idempotente) + limpia el storage local.
  Future<void> logout() async {
    final stored = await _tokenStore.readRefresh();
    try {
      if (stored != null) {
        await _rawDio.post<dynamic>('/auth/logout', data: {'refresh_token': stored});
      }
    } on DioException {
      // best-effort; igual limpiamos local
    } finally {
      await _tokenStore.clear();
    }
  }

  ApiError _toApiError(DioException e) {
    final res = e.response;
    if (res != null) return ApiError.fromResponse(res.statusCode, res.data);
    return const ApiError(
      code: 'network_error',
      message: 'No pudimos conectar. Revisá tu conexión.',
    );
  }
}
