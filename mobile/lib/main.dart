import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'data/offline/sync_service_provider.dart';
import 'router/router.dart';
import 'theme/theme.dart';
import 'theme/theme_controller.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
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
