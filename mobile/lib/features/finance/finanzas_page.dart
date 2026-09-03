import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../l10n/strings.dart';
import '../../theme/colors.dart';
import '../../ui/app_background.dart';
import '../../ui/glass_panel.dart';
import '../../ui/state_views.dart';
import '../../util/money.dart';
import 'finance_range.dart';
import 'finance_repository.dart';

/// Finanzas (paridad con la Pantalla Finanzas del web): hero ganancia neta +
/// áreas de salud + gastos que cambiaron/distribución + KPIs del rubro +
/// diagnósticos + márgenes por producto + movimientos, con selector de rango.
/// La config de costos vive en el Asesor (no acá), igual que en el web.
class FinanzasPage extends ConsumerStatefulWidget {
  const FinanzasPage({super.key});

  @override
  ConsumerState<FinanzasPage> createState() => _FinanzasPageState();
}

class _FinanzasPageState extends ConsumerState<FinanzasPage> {
  FinanceRange _range = FinanceRange.month;

  static const _health = ['net_margin', 'food_cost', 'labor_cost', 'waste'];

  Color _statusColor(String status, ColorScheme scheme) => switch (status) {
        'healthy' => scheme.primary,
        'warn' => WellnodPalette.warn,
        'alert' => scheme.error,
        _ => scheme.onSurfaceVariant,
      };

  String _kpiValue(FinanceKpi k, String currency) => switch (k.kind) {
        'ratio' => '${(k.value / 100).toStringAsFixed(1)}%',
        'turnover' => '${(k.value / 100).toStringAsFixed(1)}×',
        _ => formatMoney(k.value, currency),
      };

  String? _kpiDelta(FinanceKpi k, String currency) {
    if (k.delta == 0) return null;
    final up = k.delta > 0;
    final mag = k.kind == 'ratio'
        ? '${(k.delta.abs() / 100).toStringAsFixed(1)}pts'
        : formatMoney(k.delta.abs(), currency);
    return '${up ? '▲' : '▼'} $mag';
  }

  @override
  Widget build(BuildContext context) {
    final s = context.s;
    final async = ref.watch(financeOverviewProvider(_range));
    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(
          title: Text(s.finanzasTitle), backgroundColor: Colors.transparent),
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
                          ref.invalidate(financeOverviewProvider(_range)),
                    ),
                    data: (fin) => RefreshIndicator(
                      onRefresh: () async {
                        ref.invalidate(financeOverviewProvider(_range));
                        ref.invalidate(expenseBreakdownProvider(_range));
                        ref.invalidate(movementsProvider(_range));
                      },
                      child: _content(context, s, fin),
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

  Widget _content(BuildContext context, Strings s, FinanceOverview fin) {
    final theme = Theme.of(context);
    final scheme = theme.colorScheme;
    final net = fin.kpi('net_margin');
    final showMovements =
        _range == FinanceRange.today || _range == FinanceRange.week;

    return ListView(
      physics: const AlwaysScrollableScrollPhysics(),
      padding: const EdgeInsets.all(16),
      children: [
        // HERO — ganancia neta del período
        GlassPanel(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(s.financeHeroNet,
                  style: TextStyle(color: scheme.onSurfaceVariant)),
              const SizedBox(height: 4),
              Text(
                net != null ? formatMoney(net.value, fin.currency) : '—',
                style: theme.textTheme.headlineMedium?.copyWith(
                  fontWeight: FontWeight.w800,
                  color: (net != null && net.value < 0)
                      ? scheme.error
                      : scheme.onSurface,
                ),
              ),
              if (net != null && _kpiDelta(net, fin.currency) != null) ...[
                const SizedBox(height: 4),
                Text('${_kpiDelta(net, fin.currency)} ${s.financeVsPrevious}',
                    style: TextStyle(
                        color: net.delta > 0 ? scheme.primary : scheme.error)),
              ],
              if (fin.projection != null) ...[
                const SizedBox(height: 4),
                Text(
                  '${s.financeProjectionPrefix} ${formatMoney(fin.projection!.salesAmount, fin.currency)} ${s.financeProjectionDays(fin.projection!.elapsedDays, fin.projection!.monthDays)}',
                  style:
                      TextStyle(color: scheme.onSurfaceVariant, fontSize: 13),
                ),
              ],
            ],
          ),
        ),
        if (!fin.configured) ...[
          const SizedBox(height: 12),
          _banner(context, s.financeConfigureCosts),
        ],
        // Áreas de salud
        const SizedBox(height: 12),
        _healthGrid(context, s, fin),
        // Comisiones
        if (fin.commissionsAmount > 0) ...[
          const SizedBox(height: 12),
          GlassPanel(
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(s.financeCommissionsLabel,
                        style: TextStyle(color: scheme.onSurfaceVariant)),
                    Text('−${formatMoney(fin.commissionsAmount, fin.currency)}',
                        style: TextStyle(
                            color: scheme.error, fontWeight: FontWeight.w700)),
                  ],
                ),
                Flexible(
                  child: Text(
                    '${s.financeNetCollected} ${formatMoney(fin.collectedNetAmount, fin.currency)}',
                    textAlign: TextAlign.right,
                    style: TextStyle(color: scheme.onSurfaceVariant, fontSize: 13),
                  ),
                ),
              ],
            ),
          ),
        ],
        // Gastos que cambiaron + distribución
        const SizedBox(height: 12),
        _ExpensesSection(range: _range),
        // Resumen IA
        if (fin.summary != null && fin.summary!.trim().isNotEmpty) ...[
          const SizedBox(height: 12),
          GlassPanel(child: Text(fin.summary!)),
        ],
        // KPIs del rubro (los 7)
        if (fin.kpis.isNotEmpty) ...[
          const SizedBox(height: 12),
          Text(s.financeKpisTitle, style: theme.textTheme.titleSmall),
          const SizedBox(height: 8),
          _kpiGrid(context, s, fin),
        ],
        // Diagnósticos
        if (fin.diagnostics.isNotEmpty) ...[
          const SizedBox(height: 12),
          GlassPanel(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(s.financeDiagnosticsTitle,
                    style: theme.textTheme.titleSmall),
                const SizedBox(height: 8),
                for (final d in fin.diagnostics)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 10),
                    child: Container(
                      decoration: BoxDecoration(
                        border: Border(
                            left: BorderSide(color: scheme.primary, width: 2)),
                      ),
                      padding: const EdgeInsets.only(left: 10),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(d.title,
                              style: const TextStyle(
                                  fontWeight: FontWeight.w600)),
                          Text(d.body,
                              style: TextStyle(
                                  color: scheme.onSurfaceVariant,
                                  fontSize: 13)),
                          if (d.action != null)
                            Text('→ ${d.action}',
                                style: TextStyle(
                                    color: scheme.primary, fontSize: 13)),
                        ],
                      ),
                    ),
                  ),
              ],
            ),
          ),
        ],
        // Márgenes por producto
        if (fin.productMargins.isNotEmpty) ...[
          const SizedBox(height: 12),
          GlassPanel(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(s.financeProductMargins,
                    style: theme.textTheme.titleSmall),
                const SizedBox(height: 4),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(s.financeUnitsMargin,
                        style: TextStyle(
                            color: scheme.onSurfaceVariant, fontSize: 12)),
                  ],
                ),
                const Divider(),
                for (final p in fin.productMargins)
                  Padding(
                    padding: const EdgeInsets.symmetric(vertical: 4),
                    child: Row(
                      children: [
                        Expanded(child: Text(p.productName)),
                        Text('${p.unitsSold} · ',
                            style: TextStyle(color: scheme.onSurfaceVariant)),
                        Text(formatMoney(p.marginAmount, fin.currency),
                            style:
                                const TextStyle(fontWeight: FontWeight.w600)),
                      ],
                    ),
                  ),
              ],
            ),
          ),
        ],
        // Movimientos (Hoy/Semana)
        if (showMovements) ...[
          const SizedBox(height: 12),
          _MovementsSection(range: _range),
        ],
      ],
    );
  }

  Widget _banner(BuildContext context, String text) {
    final scheme = Theme.of(context).colorScheme;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: WellnodPalette.warn.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: WellnodPalette.warn.withValues(alpha: 0.4)),
      ),
      child: Row(
        children: [
          Icon(Icons.info_outline, size: 18, color: WellnodPalette.warn),
          const SizedBox(width: 8),
          Expanded(
              child: Text(text,
                  style: TextStyle(color: scheme.onSurface, fontSize: 13))),
        ],
      ),
    );
  }

  Widget _healthGrid(BuildContext context, Strings s, FinanceOverview fin) {
    final scheme = Theme.of(context).colorScheme;
    final cards = <Widget>[];
    for (final key in _health) {
      final k = fin.kpi(key);
      if (k == null) continue;
      cards.add(_metricCard(
        context,
        label: s.financeKpiLabel(key),
        value: _kpiValue(k, fin.currency),
        valueColor: _statusColor(k.status, scheme),
        footer: s.financeStatusAction(k.status),
        dotColor: _statusColor(k.status, scheme),
      ));
    }
    return twoColGrid(cards);
  }

  Widget _kpiGrid(BuildContext context, Strings s, FinanceOverview fin) {
    final scheme = Theme.of(context).colorScheme;
    return twoColGrid([
      for (final k in fin.kpis)
        _metricCard(
          context,
          label: s.financeKpiLabel(k.key),
          value: _kpiValue(k, fin.currency),
          valueColor: _statusColor(k.status, scheme),
          footer: _kpiDelta(k, fin.currency) ?? '—',
        ),
    ]);
  }

  Widget _metricCard(
    BuildContext context, {
    required String label,
    required String value,
    required Color valueColor,
    String? footer,
    Color? dotColor,
  }) {
    final scheme = Theme.of(context).colorScheme;
    return GlassPanel(
      padding: const EdgeInsets.all(14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Row(
            children: [
              if (dotColor != null) ...[
                Container(
                    width: 8,
                    height: 8,
                    decoration: BoxDecoration(
                        color: dotColor, shape: BoxShape.circle)),
                const SizedBox(width: 6),
              ],
              Flexible(
                child: Text(label,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(
                        color: scheme.onSurfaceVariant, fontSize: 13)),
              ),
            ],
          ),
          const SizedBox(height: 4),
          Align(
            alignment: Alignment.centerLeft,
            child: FittedBox(
              fit: BoxFit.scaleDown,
              child: Text(value,
                  maxLines: 1,
                  style: TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.w700,
                      color: valueColor)),
            ),
          ),
          if (footer != null)
            Text(footer,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(color: scheme.onSurfaceVariant, fontSize: 12)),
        ],
      ),
    );
  }
}

/// Gastos que más cambiaron + distribución por categoría (barras proporcionales).
class _ExpensesSection extends ConsumerWidget {
  const _ExpensesSection({required this.range});
  final FinanceRange range;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = context.s;
    final scheme = Theme.of(context).colorScheme;
    final async = ref.watch(expenseBreakdownProvider(range));
    return async.maybeWhen(
      data: (b) {
        if (b.rows.isEmpty) {
          return GlassPanel(
              child: Text(s.financeExpenseEmpty,
                  style: TextStyle(color: scheme.onSurfaceVariant)));
        }
        final byChange = [...b.rows]
          ..sort((a, c) => c.delta.abs().compareTo(a.delta.abs()));
        final top = byChange.take(3).toList();
        final byAmount = [...b.rows]
          ..sort((a, c) => c.amount.compareTo(a.amount));
        return Column(
          children: [
            GlassPanel(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(s.financeExpenseChangesTitle,
                      style: Theme.of(context).textTheme.titleSmall),
                  const SizedBox(height: 8),
                  for (final r in top)
                    Padding(
                      padding: const EdgeInsets.symmetric(vertical: 3),
                      child: Row(
                        children: [
                          Icon(r.delta >= 0 ? Icons.arrow_upward : Icons.arrow_downward,
                              size: 14,
                              color: r.delta >= 0
                                  ? scheme.error
                                  : scheme.primary),
                          const SizedBox(width: 6),
                          Expanded(child: Text(r.category)),
                          Text(formatMoney(r.amount, b.currency),
                              style:
                                  const TextStyle(fontWeight: FontWeight.w600)),
                        ],
                      ),
                    ),
                ],
              ),
            ),
            const SizedBox(height: 12),
            GlassPanel(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(s.financeExpenseDistTitle,
                      style: Theme.of(context).textTheme.titleSmall),
                  const SizedBox(height: 8),
                  for (final r in byAmount)
                    Padding(
                      padding: const EdgeInsets.symmetric(vertical: 4),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Expanded(child: Text(r.category)),
                              Text(formatMoney(r.amount, b.currency),
                                  style: const TextStyle(
                                      fontWeight: FontWeight.w600)),
                            ],
                          ),
                          const SizedBox(height: 4),
                          ClipRRect(
                            borderRadius: BorderRadius.circular(4),
                            child: LinearProgressIndicator(
                              value: b.total > 0 ? r.amount / b.total : 0,
                              minHeight: 6,
                              backgroundColor: scheme.surfaceContainerHighest,
                            ),
                          ),
                        ],
                      ),
                    ),
                ],
              ),
            ),
          ],
        );
      },
      orElse: () => const SizedBox.shrink(),
    );
  }
}

/// Últimos movimientos (Hoy/Semana).
class _MovementsSection extends ConsumerWidget {
  const _MovementsSection({required this.range});
  final FinanceRange range;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = context.s;
    final scheme = Theme.of(context).colorScheme;
    final async = ref.watch(movementsProvider(range));
    return async.maybeWhen(
      data: (movs) {
        if (movs.isEmpty) return const SizedBox.shrink();
        return GlassPanel(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(s.financeMovementsTitle,
                  style: Theme.of(context).textTheme.titleSmall),
              const SizedBox(height: 4),
              for (final m in movs)
                Padding(
                  padding: const EdgeInsets.symmetric(vertical: 4),
                  child: Row(
                    children: [
                      Icon(
                          m.kind == 'expense'
                              ? Icons.south_west
                              : Icons.north_east,
                          size: 14,
                          color: m.kind == 'expense'
                              ? scheme.error
                              : scheme.primary),
                      const SizedBox(width: 6),
                      Expanded(
                        child: Text(m.description ?? m.category ?? m.method),
                      ),
                      Text(
                        '${m.kind == 'expense' ? '−' : ''}${formatMoney(m.amount, m.currency)}',
                        style: const TextStyle(fontWeight: FontWeight.w600),
                      ),
                    ],
                  ),
                ),
            ],
          ),
        );
      },
      orElse: () => const SizedBox.shrink(),
    );
  }
}
