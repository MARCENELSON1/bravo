import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'data/offline/sync_service_provider.dart';
import 'router/router.dart';
import 'theme/theme.dart';
import 'theme/theme_controller.dart';

/// Handler de push en background (Fase 4): el sistema muestra la notificación solo;
/// no hay nada que hacer acá (el tap se maneja al abrir la app). Top-level + entry
/// point, requisito de firebase_messaging.
@pragma('vm:entry-point')
Future<void> _firebaseBackgroundHandler(RemoteMessage message) async {}

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  try {
    await Firebase.initializeApp();
    FirebaseMessaging.onBackgroundMessage(_firebaseBackgroundHandler);
  } catch (_) {
    // Sin config de Firebase (dev / plataforma sin push) → la app arranca igual.
  }
  final prefs = await SharedPreferences.getInstance();
  runApp(
    ProviderScope(
      overrides: [sharedPreferencesProvider.overrideWithValue(prefs)],
      child: const WellnodApp(),
    ),
  );
}

class WellnodApp extends ConsumerStatefulWidget {
  const WellnodApp({super.key});

  @override
  ConsumerState<WellnodApp> createState() => _WellnodAppState();
}

class _WellnodAppState extends ConsumerState<WellnodApp> {
  @override
  void initState() {
    super.initState();
    // Arranca el drenado de la cola de contingencia (al reconectar).
    ref.read(syncServiceProvider).start();
  }

  @override
  Widget build(BuildContext context) {
    final router = ref.watch(routerProvider);
    final mode = ref.watch(themeModeProvider);
    final locale = ref.watch(localeProvider);
    final reduceMotion = ref.watch(reduceMotionProvider);

    return MaterialApp.router(
      title: 'Wellnod',
      debugShowCheckedModeBanner: false,
      theme: buildLightTheme(),
      darkTheme: buildDarkTheme(),
      themeMode: mode,
      // `supportedLocales` con es primero → fallback a español (paridad AR).
      locale: locale,
      supportedLocales: const [Locale('es'), Locale('en')],
      localizationsDelegates: const [
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      // "Reducir movimiento": Flutter respeta `disableAnimations` en las
      // transiciones de ruta y en las animaciones implícitas.
      builder: (context, child) {
        if (!reduceMotion || child == null) return child ?? const SizedBox();
        final mq = MediaQuery.of(context);
        return MediaQuery(
          data: mq.copyWith(disableAnimations: true),
          child: child,
        );
      },
      routerConfig: router,
    );
  }
}
