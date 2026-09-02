import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../auth/session_notifier.dart';
import '../../l10n/strings.dart';
import '../../theme/theme_controller.dart';
import '../../ui/glass_panel.dart';
import '../../util/money.dart';
import '../copilot/copilot_page.dart';
import 'home_repository.dart';

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
    final dashboard = ref.watch(dashboardProvider);

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
            child: dashboard.when(
              loading: () => const SizedBox(
                height: 44,
                child: Center(child: CircularProgressIndicator()),
              ),
              error: (e, _) => Text(s.homeSubtitle),
              data: (d) => Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Text('${s.homeNet} · ${s.homeToday}',
                          style: theme.textTheme.titleSmall),
                      const Spacer(),
                      Text(
                        formatMoney(d.net, d.currency),
                        style: theme.textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.w700,
                          color: theme.colorScheme.primary,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 10),
                  Wrap(
                    spacing: 20,
                    runSpacing: 10,
                    children: [
                      _kpi(theme, s.homeSales, formatMoney(d.sales, d.currency)),
                      _kpi(theme, s.homeCollected,
                          formatMoney(d.collectedNet, d.currency)),
                      _kpi(theme, s.homeActiveOrders, '${d.activeOrders}'),
                      _kpi(theme, s.homeAvgTicket,
                          formatMoney(d.avgTicket, d.currency)),
                    ],
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 12),
          FilledButton.icon(
            onPressed: () => Navigator.of(context).push(
              MaterialPageRoute(builder: (_) => const CopilotPage()),
            ),
            icon: const Icon(Icons.auto_awesome),
            label: Text(s.askCopilot),
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

  Widget _kpi(ThemeData theme, String label, String value) => Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(label,
              style: theme.textTheme.bodySmall
                  ?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
          Text(value,
              style: theme.textTheme.titleSmall
                  ?.copyWith(fontWeight: FontWeight.w600)),
        ],
      );
}
