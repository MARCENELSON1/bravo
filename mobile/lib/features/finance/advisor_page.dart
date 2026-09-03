import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../l10n/strings.dart';
import '../../theme/colors.dart';
import '../../ui/app_background.dart';
import '../../ui/glass_panel.dart';
import '../../ui/state_views.dart';
import '../../util/money.dart';
import 'advisor_report_repository.dart';
import 'advisor_settings_page.dart';
import 'finance_range.dart';

/// Asesor (Fase 9) — reporte de insights + KPIs del negocio, paridad con la
/// pantalla `/app/advisor` del web. La config de costos se abre desde acá.
class AdvisorPage extends ConsumerStatefulWidget {
  const AdvisorPage({super.key});

  @override
  ConsumerState<AdvisorPage> createState() => _AdvisorPageState();
}

class _AdvisorPageState extends ConsumerState<AdvisorPage> {
  FinanceRange _range = FinanceRange.month;

  static const _buckets = [
    'pricing',
    'costs',
    'menu',
    'operations',
    'cash',
    'inventory',
  ];

  String _pct(int bps) => '${(bps / 100).toStringAsFixed(1)}%';

  @override
  Widget build(BuildContext context) {
    final s = context.s;
    final async = ref.watch(advisorReportProvider(_range));
    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(
        title: Text(s.advisorTitle),
        backgroundColor: Colors.transparent,
        actions: [
          IconButton(
            icon: const Icon(Icons.tune),
            tooltip: s.advisorConfigTitle,
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
            child: Column(
              children: [
                _rangeBar(s),
                Expanded(
                  child: async.when(
                    loading: () =>
                        const Center(child: CircularProgressIndicator()),
                    error: (e, _) => ErrorView(
                      error: e,
                      onRetry: () =>
                          ref.invalidate(advisorReportProvider(_range)),
                    ),
                    data: (r) => RefreshIndicator(
                      onRefresh: () async =>
                          ref.invalidate(advisorReportProvider(_range)),
                      child: _content(context, s, r),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _rangeBar(Strings s) => Padding(
        padding: const EdgeInsets.fromLTRB(12, 8, 12, 4),
        child: SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: Row(
            children: [
              for (final r in FinanceRange.values)
                Padding(
                  padding: const EdgeInsets.only(right: 8),
                  child: ChoiceChip(
                    label: Text(s.financeRange(r)),
                    selected: _range == r,
                    onSelected: (_) => setState(() => _range = r),
                  ),
                ),
            ],
          ),
        ),
      );

  Widget _content(BuildContext context, Strings s, AdvisorReport r) {
    final scheme = Theme.of(context).colorScheme;
    final k = r.kpis;
    final locked = k.configured ? null : s.advisorConfigureCosts;
    String lock(String value) => k.configured ? value : '—';

    return ListView(
      physics: const AlwaysScrollableScrollPhysics(),
      padding: const EdgeInsets.all(16),
      children: [
        Text(s.advisorSubtitle,
            style: TextStyle(color: scheme.onSurfaceVariant)),
        const SizedBox(height: 12),
        if (r.summary != null && r.summary!.trim().isNotEmpty) ...[
          GlassPanel(
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(Icons.auto_awesome, size: 18, color: scheme.primary),
                const SizedBox(width: 8),
                Expanded(child: Text(r.summary!)),
              ],
            ),
          ),
          const SizedBox(height: 12),
        ],
        twoColGrid([
          _kpi(context, s.advisorKpiLabel('sales'),
              formatMoney(k.salesAmount, k.currency)),
          _kpi(context, s.advisorKpiLabel('gross_margin'),
              formatMoney(k.grossMarginAmount, k.currency)),
          _kpi(context, s.advisorKpiLabel('net_margin'),
              lock(formatMoney(k.netMarginAmount, k.currency)),
              hint: locked,
              negative: k.configured && k.netMarginAmount < 0),
          _kpi(context, s.advisorKpiLabel('food_cost'),
              _pct(k.foodCostRatioBps)),
          _kpi(context, s.advisorKpiLabel('prime_cost'),
              lock(_pct(k.primeCostRatioBps)),
              hint: locked),
          _kpi(context, s.advisorKpiLabel('break_even'),
              lock(formatMoney(k.breakEvenAmount, k.currency)),
              hint: locked),
          _kpi(context, s.advisorKpiLabel('orders'), '${k.ordersCount}'),
          _kpi(context, s.advisorKpiLabel('avg_ticket'),
              formatMoney(k.averageTicketAmount, k.currency)),
          _kpi(context, s.advisorKpiLabel('no_show'), _pct(k.noShowRateBps)),
        ]),
        const SizedBox(height: 16),
        for (final bucket in _buckets) ...[
          if (r.insights.any((i) => i.bucket == bucket)) ...[
            Text(s.advisorBucketLabel(bucket),
                style: Theme.of(context).textTheme.titleSmall),
            const SizedBox(height: 8),
            for (final i in r.insights.where((i) => i.bucket == bucket))
              Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: GlassPanel(
                  padding: const EdgeInsets.all(14),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Expanded(
                            child: Text(i.title,
                                style: const TextStyle(
                                    fontWeight: FontWeight.w600)),
                          ),
                          _severityBadge(context, i.severity),
                        ],
                      ),
                      const SizedBox(height: 4),
                      Text(i.body,
                          style: TextStyle(
                              color: scheme.onSurfaceVariant, fontSize: 13)),
                      if (i.action.isNotEmpty) ...[
                        const SizedBox(height: 4),
                        Text('→ ${i.action}'),
                      ],
                    ],
                  ),
                ),
              ),
            const SizedBox(height: 8),
          ],
        ],
      ],
    );
  }

  Widget _kpi(BuildContext context, String label, String value,
      {String? hint, bool negative = false}) {
    final scheme = Theme.of(context).colorScheme;
    return GlassPanel(
      padding: const EdgeInsets.all(14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(label,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: TextStyle(color: scheme.onSurfaceVariant, fontSize: 12)),
          const SizedBox(height: 2),
          Align(
            alignment: Alignment.centerLeft,
            child: FittedBox(
              fit: BoxFit.scaleDown,
              child: Text(value,
                  maxLines: 1,
                  style: TextStyle(
                      fontSize: 19,
                      fontWeight: FontWeight.w700,
                      color: negative ? scheme.error : scheme.onSurface)),
            ),
          ),
          if (hint != null)
            Text(hint,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(color: scheme.onSurfaceVariant, fontSize: 11)),
        ],
      ),
    );
  }

  Widget _severityBadge(BuildContext context, String severity) {
    final scheme = Theme.of(context).colorScheme;
    final color = switch (severity) {
      'critical' || 'alert' => scheme.error,
      'warn' || 'warning' => WellnodPalette.warn,
      _ => scheme.primary,
    };
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.15),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(severity,
          style: TextStyle(
              color: color, fontSize: 11, fontWeight: FontWeight.w600)),
    );
  }
}
