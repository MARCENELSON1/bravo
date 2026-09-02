/// Error uniforme de la API. Espeja `frontend/src/api/api-error.ts`:
/// `code` es un string estable en inglés (ej. `invalid_credentials`) y
/// `message` es el texto en español (listo para mostrar) que devuelve el backend.
class ApiError implements Exception {
  const ApiError({
    required this.code,
    required this.message,
    this.status,
  });

  final String code;
  final String message;
  final int? status;

  /// Construye desde el body `{code, message}` del backend (ver `errors.py`).
  factory ApiError.fromResponse(int? status, Object? body) {
    if (body is Map) {
      final code = body['code'];
      final message = body['message'];
      return ApiError(
        code: code is String ? code : 'unknown_error',
        message: message is String ? message : 'Ocurrió un error.',
        status: status,
      );
    }
    return ApiError(
      code: 'unknown_error',
      message: 'Ocurrió un error.',
      status: status,
    );
  }

  @override
  String toString() => 'ApiError($status, $code): $message';
}
