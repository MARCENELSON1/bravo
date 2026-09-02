import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../auth/session_notifier.dart';
import '../../l10n/strings.dart';
import '../../theme/theme_controller.dart';
import '../../ui/glass_panel.dart';

/// Home mínimo de F0: saluda con los datos de `/me`, permite cambiar tema e
/// idioma, y cerrar sesión. Prueba de punta a punta de la fundación.
class HomePage extends ConsumerWidget {
  const HomePage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = context.s;
    final theme = Theme.of(context);
    final sessionState = ref.watch(sessionProvider);
    if (sessionState is! SessionAuthenticated) {
      return const Center(child: CircularProgressIndicator());
    }
    final session = sessionState.session;
    final mode = ref.watch(themeModeProvider);
    final locale = ref.watch(localeProvider);

    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const SizedBox(height: 8),
          GlassPanel(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  s.greeting(session.displayName),
                  style: theme.textTheme.headlineSmall
                      ?.copyWith(fontWeight: FontWeight.w700),
                ),
                const SizedBox(height: 4),
                Text(
                  '${session.tenantName} · ${s.role(session.role)}',
                  style: theme.textTheme.bodyMedium?.copyWith(
                    color: theme.colorScheme.onSurfaceVariant,
                  ),
                ),
                const SizedBox(height: 12),
                Text(s.homeSubtitle, style: theme.textTheme.bodySmall),
              ],
            ),
          ),
          const SizedBox(height: 16),
          GlassPanel(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(s.theme, style: theme.textTheme.titleSmall),
                const SizedBox(height: 8),
                SegmentedButton<ThemeMode>(
                  segments: [
                    ButtonSegment(value: ThemeMode.light, label: Text(s.themeLight)),
                    ButtonSegment(value: ThemeMode.dark, label: Text(s.themeDark)),
                    ButtonSegment(value: ThemeMode.system, label: Text(s.themeSystem)),
                  ],
                  selected: {mode},
                  onSelectionChanged: (sel) =>
                      ref.read(themeModeProvider.notifier).set(sel.first),
                ),
                const SizedBox(height: 20),
                Text(s.language, style: theme.textTheme.titleSmall),
                const SizedBox(height: 8),
                SegmentedButton<String>(
                  segments: const [
                    ButtonSegment(value: 'es', label: Text('ES')),
                    ButtonSegment(value: 'en', label: Text('EN')),
                  ],
                  selected: {locale?.languageCode ?? 'es'},
                  onSelectionChanged: (sel) => ref
                      .read(localeProvider.notifier)
                      .set(Locale(sel.first)),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          OutlinedButton.icon(
            onPressed: () => ref.read(sessionProvider.notifier).logout(),
            icon: const Icon(Icons.logout),
            label: Text(s.logout),
          ),
        ],
      ),
    );
  }
}
