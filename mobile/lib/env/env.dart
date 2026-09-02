/// Configuración de entorno. La base URL de la API se pasa por `--dart-define`
/// (espeja `frontend/src/lib/env.ts`, que usa `VITE_API_URL ?? "/api/v1"`).
///
/// Ejemplos:
///   iOS sim / desktop:   --dart-define=API_BASE_URL=http://localhost:8000/api/v1
///   Android emulador:    --dart-define=API_BASE_URL=http://10.0.2.2:8000/api/v1
///   prod:                --dart-define=API_BASE_URL=https://api.wellnod.com/api/v1
class Env {
  const Env._();

  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://localhost:8000/api/v1',
  );
}
