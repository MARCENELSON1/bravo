/// El backend devuelve el refresh token SOLO en la cabecera `Set-Cookie`
/// (`bravo_refresh=...`), nunca en el body — en login y en cada refresh (rotado).
/// Un cliente nativo lee la cabecera cruda y extrae el valor para guardarlo en
/// secure storage. Ver `backend/app/presentation/api/v1/auth.py:32-42`.
const String kRefreshCookieName = 'bravo_refresh';

/// Extrae el valor de `bravo_refresh` de la lista de `Set-Cookie` de la respuesta.
/// Devuelve `null` si no está presente.
String? extractRefreshCookie(List<String>? setCookies) {
  if (setCookies == null) return null;
  for (final raw in setCookies) {
    // Cada Set-Cookie: "bravo_refresh=VALUE; Path=/...; HttpOnly; ..."
    final firstPair = raw.split(';').first.trim();
    final eq = firstPair.indexOf('=');
    if (eq <= 0) continue;
    final name = firstPair.substring(0, eq).trim();
    if (name == kRefreshCookieName) {
      final value = firstPair.substring(eq + 1).trim();
      return value.isEmpty ? null : value;
    }
  }
  return null;
}
