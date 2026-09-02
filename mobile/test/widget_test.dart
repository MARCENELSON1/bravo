// Test del parseo de Set-Cookie: es el detalle clave del riesgo #1 (el refresh
// token llega SOLO por `Set-Cookie: bravo_refresh=...`).
import 'package:flutter_test/flutter_test.dart';
import 'package:wellnod_mobile/auth/refresh_cookie.dart';

void main() {
  test('extrae bravo_refresh de la lista de Set-Cookie', () {
    final cookies = [
      'bravo_refresh=abc.def123; Path=/api/v1/auth; HttpOnly; Secure; SameSite=Lax',
      'other=zzz; Path=/',
    ];
    expect(extractRefreshCookie(cookies), 'abc.def123');
  });

  test('devuelve null cuando no está presente', () {
    expect(extractRefreshCookie(['other=zzz; Path=/']), isNull);
    expect(extractRefreshCookie(null), isNull);
    expect(extractRefreshCookie(const []), isNull);
  });

  test('no confunde un nombre parecido', () {
    expect(extractRefreshCookie(['not_bravo_refresh=x; Path=/']), isNull);
  });
}
