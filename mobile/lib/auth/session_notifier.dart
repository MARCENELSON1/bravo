import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../api/api_client.dart';
import 'auth_repository.dart';
import 'session.dart';

/// Estado de sesión (espeja booting/authenticated/anonymous de `auth-context.ts`).
sealed class SessionState {
  const SessionState();
}

class SessionBooting extends SessionState {
  const SessionBooting();
}

class SessionAuthenticated extends SessionState {
  const SessionAuthenticated(this.session);
  final Session session;
}

class SessionAnonymous extends SessionState {
  const SessionAnonymous({this.error});
  final String? error;
}

/// Maneja el ciclo de vida de la sesión. Al arrancar hace refresh silencioso +
/// `/me` (espeja `auth-provider.tsx`).
class SessionNotifier extends Notifier<SessionState> {
  @override
  SessionState build() {
    _boot();
    return const SessionBooting();
  }

  AuthRepository get _repo => ref.read(authRepositoryProvider);

  Future<void> _boot() async {
    final refreshed = await _repo.tryRefreshSession();
    if (!refreshed) {
      state = const SessionAnonymous();
      return;
    }
    try {
      final me = await _repo.me();
      state = SessionAuthenticated(Session.fromMe(me));
    } catch (_) {
      state = const SessionAnonymous();
    }
  }

  /// Login desde la pantalla. Propaga `ApiError` para mostrar el mensaje.
  Future<void> login({
    required String slug,
    required String email,
    required String password,
  }) async {
    await _repo.login(slug: slug, email: email, password: password);
    final me = await _repo.me();
    state = SessionAuthenticated(Session.fromMe(me));
  }

  Future<void> logout() async {
    await _repo.logout();
    state = const SessionAnonymous();
  }
}

final sessionProvider =
    NotifierProvider<SessionNotifier, SessionState>(SessionNotifier.new);
