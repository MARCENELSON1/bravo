import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// Guarda los tokens de sesión. Espeja el diseño del front:
/// - **access token SOLO en memoria** (nunca en disco) — ver `token-store.ts`.
/// - **refresh token en secure storage** (Keychain iOS / EncryptedSharedPreferences
///   Android). El refresh rota en cada uso (single-use), así que siempre se persiste
///   el nuevo.
class TokenStore {
  TokenStore(this._storage);

  final FlutterSecureStorage _storage;
  static const String _refreshKey = 'wellnod_refresh';

  String? _accessToken; // memoria

  String? get accessToken => _accessToken;
  void setAccessToken(String? token) => _accessToken = token;

  Future<String?> readRefresh() => _storage.read(key: _refreshKey);
  Future<void> writeRefresh(String token) =>
      _storage.write(key: _refreshKey, value: token);

  Future<void> clear() async {
    _accessToken = null;
    await _storage.delete(key: _refreshKey);
  }
}
