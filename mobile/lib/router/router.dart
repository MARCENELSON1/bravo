import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../auth/session_notifier.dart';
import '../features/login/login_page.dart';
import '../features/shell/app_scaffold.dart';
import '../ui/app_background.dart';

/// Router con guards espejando `require-auth.tsx`: mientras bootea → splash;
/// anónimo → /login; autenticado → /app. `refreshListenable` re-evalúa el
/// redirect cuando cambia la sesión.
final routerProvider = Provider<GoRouter>((ref) {
  return GoRouter(
    initialLocation: '/splash',
    refreshListenable: _SessionRefresh(ref),
    redirect: (context, state) {
      final session = ref.read(sessionProvider);
      final loc = state.matchedLocation;

      if (session is SessionBooting) {
        return loc == '/splash' ? null : '/splash';
      }
      if (session is SessionAnonymous) {
        return loc == '/login' ? null : '/login';
      }
      // Autenticado: sacarlo de splash/login hacia la app.
      if (loc == '/splash' || loc == '/login') return '/app';
      return null;
    },
    routes: [
      GoRoute(path: '/splash', builder: (_, _) => const _SplashPage()),
      GoRoute(path: '/login', builder: (_, _) => const LoginPage()),
      GoRoute(path: '/app', builder: (_, _) => const AppScaffold()),
    ],
  );
});

/// Puente entre el provider de sesión y `GoRouter.refreshListenable`.
class _SessionRefresh extends ChangeNotifier {
  _SessionRefresh(Ref ref) {
    ref.listen(sessionProvider, (_, _) => notifyListeners());
  }
}

class _SplashPage extends StatelessWidget {
  const _SplashPage();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Stack(
        children: const [
          AppBackground(),
          Center(child: CircularProgressIndicator()),
        ],
      ),
    );
  }
}
