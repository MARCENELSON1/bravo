import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/api_error.dart';
import '../../l10n/strings.dart';
import '../../ui/app_background.dart';
import '../../ui/glass_panel.dart';
import '../../util/money.dart';
import 'advisor_settings_page.dart';
import 'finance_repository.dart';

/// Finanzas (Fase 6, consulta): cobrado neto, comisiones, resumen y alertas.
class FinanzasPage extends ConsumerWidget {
  const FinanzasPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = context.s;
    final async = ref.watch(financeOverviewProvider);
    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(
        title: Text(s.finanzasTitle),
        backgroundColor: Colors.transparent,
        actions: [
          IconButton(
            icon: const Icon(Icons.tune),
            tooltip: s.financeConfigOpen,
            onPressed: () => Navigator.of(context).push(
              MaterialPageRoute<void>(
                  builder: (_) => const AdvisorSettingsPage()),
            ),
          ),
        ],
      ),
      body: Stack(
        children: [
          const AppBackground(),
          SafeArea(
            child: async.when(
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (e, _) => Center(
                child: Padding(
                  padding: const EdgeInsets.all(24),
                  child: Text(e is ApiError ? e.message : '$e'),
                ),
              ),
              data: (fin) => _content(context, s, fin),
            ),
          ),
        ],
      ),
    );
  }

  Widget _content(BuildContext context, Strings s, FinanceOverview fin) {
    final theme = Theme.of(context);
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        GlassPanel(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(s.consultaOnly,
                  style: theme.textTheme.bodySmall
                      ?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
              const SizedBox(height: 10),
              _row(s.finanzasCollected,
                  formatMoney(fin.collectedNetAmount, fin.currency)),
              _row(s.finanzasCommissions,
                  formatMoney(fin.commissionsAmount, fin.currency)),
            ],
          ),
        ),
        if (!fin.configured) ...[
          const SizedBox(height: 12),
          GlassPanel(child: Text(s.finanzasNotConfigured)),
        ],
        if (fin.summary != null && fin.summary!.trim().isNotEmpty) ...[
          const SizedBox(height: 12),
          GlassPanel(child: Text(fin.summary!)),
        ],
        for (final d in fin.diagnostics) ...[
          const SizedBox(height: 12),
          GlassPanel(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Icon(_severityIcon(d.severity),
                        size: 18, color: _severityColor(context, d.severity)),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(d.title,
                          style: theme.textTheme.titleSmall
                              ?.copyWith(fontWeight: FontWeight.w600)),
                    ),
                  ],
                ),
                if (d.body.isNotEmpty) ...[
                  const SizedBox(height: 4),
                  Text(d.body, style: theme.textTheme.bodySmall),
                ],
              ],
            ),
          ),
        ],
      ],
    );
  }

  Widget _row(String label, String value) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 2),
        child: Row(children: [Text(label), const Spacer(), Text(value)]),
      );

  IconData _severityIcon(String severity) => switch (severity) {
        'critical' => Icons.error_outline,
        'warn' || 'warning' => Icons.warning_amber_outlined,
        _ => Icons.info_outline,
      };

  Color _severityColor(BuildContext context, String severity) => switch (severity) {
        'critical' => Theme.of(context).colorScheme.error,
        'warn' || 'warning' => const Color(0xFFE0A800),
        _ => Theme.of(context).colorScheme.onSurfaceVariant,
      };
}
