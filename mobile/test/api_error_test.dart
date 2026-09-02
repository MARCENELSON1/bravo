import 'package:flutter_test/flutter_test.dart';
import 'package:wellnod_mobile/api/api_error.dart';

void main() {
  test('fromResponse mapea code/message/status del backend', () {
    final e = ApiError.fromResponse(401, {
      'code': 'invalid_credentials',
      'message': 'Credenciales inválidas',
    });
    expect(e.code, 'invalid_credentials');
    expect(e.message, 'Credenciales inválidas');
    expect(e.status, 401);
  });

  test('fromResponse con body no-map cae a unknown_error', () {
    final e = ApiError.fromResponse(500, 'boom');
    expect(e.code, 'unknown_error');
    expect(e.status, 500);
  });
}
