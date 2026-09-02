import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// `SharedPreferences` se carga async en `main` y se inyecta por override.
final sharedPreferencesProvider = Provider<SharedPreferences>(
  (_) => throw UnimplementedError('override en main()'),
);

const String _themeKey = 'wellnod:theme';
const String _langKey = 'wellnod:lang'; // misma key que la web (i18n/index.ts)

/// Tema claro/oscuro/sistema, persistido. Espeja next-themes del front
/// (`defaultTheme="system"`).
class ThemeModeController extends Notifier<ThemeMode> {
  @override
  ThemeMode build() {
    final saved = ref.read(sharedPreferencesProvider).getString(_themeKey);
    return switch (saved) {
      'light' => ThemeMode.light,
      'dark' => ThemeMode.dark,
      _ => ThemeMode.system,
    };
  }

  Future<void> set(ThemeMode mode) async {
    state = mode;
    await ref.read(sharedPreferencesProvider).setString(_themeKey, mode.name);
  }
}

final themeModeProvider =
    NotifierProvider<ThemeModeController, ThemeMode>(ThemeModeController.new);

/// Idioma: `null` = sistema; si no, `es`/`en`. Fallback a español (paridad AR).
class LocaleController extends Notifier<Locale?> {
  @override
  Locale? build() {
    final saved = ref.read(sharedPreferencesProvider).getString(_langKey);
    if (saved == 'es') return const Locale('es');
    if (saved == 'en') return const Locale('en');
    return null; // sistema
  }

  Future<void> set(Locale? locale) async {
    state = locale;
    final prefs = ref.read(sharedPreferencesProvider);
    if (locale == null) {
      await prefs.remove(_langKey);
    } else {
      await prefs.setString(_langKey, locale.languageCode);
    }
  }
}

final localeProvider =
    NotifierProvider<LocaleController, Locale?>(LocaleController.new);

const String _reduceMotionKey = 'wellnod:reduce-motion'; // misma key que la web

/// Reducir movimiento (accesibilidad): desactiva las animaciones de la interfaz.
class ReduceMotionController extends Notifier<bool> {
  @override
  bool build() =>
      ref.read(sharedPreferencesProvider).getBool(_reduceMotionKey) ?? false;

  Future<void> set(bool value) async {
    state = value;
    await ref.read(sharedPreferencesProvider).setBool(_reduceMotionKey, value);
  }
}

final reduceMotionProvider =
    NotifierProvider<ReduceMotionController, bool>(ReduceMotionController.new);
