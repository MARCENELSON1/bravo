import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../auth/auth_repository.dart';
import '../auth/token_store.dart';
import '../env/env.dart';
import 'auth_interceptor.dart';

/// Almacenamiento seguro (Keychain iOS / EncryptedSharedPreferences Android).
final secureStorageProvider = Provider<FlutterSecureStorage>(
  (_) => const FlutterSecureStorage(),
);

final tokenStoreProvider = Provider<TokenStore>(
  (ref) => TokenStore(ref.read(secureStorageProvider)),
);

BaseOptions _baseOptions() => BaseOptions(
      baseUrl: Env.apiBaseUrl,
      connectTimeout: const Duration(seconds: 15),
      receiveTimeout: const Duration(seconds: 20),
      responseType: ResponseType.json,
    );

/// Dio "crudo" (sin interceptor de auth): login, refresh, logout.
final rawDioProvider = Provider<Dio>((_) => Dio(_baseOptions()));

/// Dio autenticado: agrega `Bearer` y hace refresh transparente ante 401.
/// El callback de refresh lee `authRepositoryProvider` de forma perezosa para
/// evitar un ciclo de dependencias (se resuelve recién cuando ocurre un 401).
final Provider<Dio> apiDioProvider = Provider<Dio>((ref) {
  final dio = Dio(_baseOptions());
  dio.interceptors.add(
    AuthInterceptor(
      tokenStore: ref.read(tokenStoreProvider),
      refresh: () => ref.read(authRepositoryProvider).tryRefreshSession(),
    ),
  );
  return dio;
});

final Provider<AuthRepository> authRepositoryProvider = Provider<AuthRepository>(
  (ref) => AuthRepository(
    ref.read(rawDioProvider),
    ref.read(apiDioProvider),
    ref.read(tokenStoreProvider),
  ),
);
