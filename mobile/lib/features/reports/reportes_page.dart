import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../l10n/strings.dart';
import '../../ui/app_background.dart';
import '../../ui/glass_panel.dart';
import '../../ui/state_views.dart';
import '../../util/money.dart';
import '../cashier/payment_dtos.dart';
import '../finance/finance_range.dart';
import '../finance/finance_repository.dart';
import 'reports_repository.dart';

/// Reportes (paridad con la pantalla del web): selector de rango + resumen del
/// período + ventas por día + gastos por categoría + top productos + mix de
/// pagos. (En AR no aparecen las tarjetas de sales tax; son US-only.)
class ReportesPage extends ConsumerStatefulWidget {
  const ReportesPage({super.key});

  @override
  ConsumerState<ReportesPage> createState() => _ReportesPageState();
}

class _ReportesPageState extends ConsumerState<ReportesPage> {
  FinanceRange _range = FinanceRange.month;

  @override
  Widget build(BuildContext context) {
    final s = context.s;
    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(
          title: Text(s.reportesTitle), backgroundColor: Colors.transparent),
      body: Stack(
        children: [
          const AppBackground(),
          SafeArea(
            child: Column(
              children: [
                _rangeBar(s),
                Expanded(
                  child: RefreshIndicator(
                    onRefresh: () async {
                      ref.invalidate(reportSummaryProvider(_range));
                      ref.invalidate(revenueDailyProvider(_range));
                      ref.invalidate(expenseBreakdownProvider(_range));
                      ref.invalidate(productPerfProvider(_range));
                      ref.invalidate(paymentMixProvider(_range));
                    },
                    child: ListView(
                      physics: const AlwaysScrollableScrollPhysics(),
                      padding: const EdgeInsets.all(16),
                      children: [
                        _summary(context, s),
                        const SizedBox(height: 16),
                        _salesByDay(context, s),
                        const SizedBox(height: 16),
                        _expensesByCategory(context, s),
                        const SizedBox(height: 16),
                        Text(s.repTopProducts,
                            style: Theme.of(context).textTheme.titleSmall),
                        const SizedBox(height: 8),
                        _topProducts(context, s),
                        const SizedBox(height: 16),
                        Text(s.repPaymentMix,
                            style: Theme.of(context).textTheme.titleSmall),
                        const SizedBox(height: 8),
                        _paymentMix(context, s),
                      ],
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

  Widget _summary(BuildContext context, Strings s) {
    final async = ref.watch(reportSummaryProvider(_range));
    return async.when(
      loading: () => const _Loading(),
      error: (e, _) => ErrorView(
          error: e, onRetry: () => ref.invalidate(reportSummaryProvider(_range))),
      data: (d) {
        Widget stat(String label, int v, {bool accent = false}) {
          final scheme = Theme.of(context).colorScheme;
          return GlassPanel(
            padding: const EdgeInsets.all(12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(label,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style:
                        TextStyle(color: scheme.onSurfaceVariant, fontSize: 12)),
                const SizedBox(height: 2),
                Align(
                  alignment: Alignment.centerLeft,
                  child: FittedBox(
                    fit: BoxFit.scaleDown,
                    child: Text(formatMoney(v, d.currency),
                        maxLines: 1,
                        style: TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.w700,
                            color: accent ? scheme.primary : scheme.onSurface)),
                  ),
                ),
              ],
            ),
          );
        }

        final scheme = Theme.of(context).colorScheme;
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(s.repSummaryTitle,
                style: Theme.of(context).textTheme.titleSmall),
            const SizedBox(height: 8),
            twoColGrid([
              stat(s.repSales, d.sales),
              stat(s.repCollectedNet, d.collectedNet),
              stat(s.repExpenses, d.expenses),
              stat(s.repProfit, d.profit, accent: true),
              stat(s.homeAvgTicket, d.avgTicket),
              GlassPanel(
                padding: const EdgeInsets.all(12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(s.repOrders,
                        style: TextStyle(
                            color: scheme.onSurfaceVariant, fontSize: 12)),
                    const SizedBox(height: 2),
                    Text('${d.paidOrders}',
                        style: const TextStyle(
                            fontSize: 18, fontWeight: FontWeight.w700)),
                  ],
                ),
              ),
            ]),
          ],
        );
      },
    );
  }

  Widget _salesByDay(BuildContext context, Strings s) {
    final scheme = Theme.of(context).colorScheme;
    final async = ref.watch(revenueDailyProvider(_range));
    return GlassPanel(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(s.repSalesByDay, style: Theme.of(context).textTheme.titleSmall),
          const SizedBox(height: 8),
          async.when(
            loading: () => const _Loading(),
            error: (e, _) => ErrorView(
                error: e,
                onRetry: () => ref.invalidate(revenueDailyProvider(_range))),
            data: (rows) {
              if (rows.isEmpty) {
                return Text(s.repSalesByDayEmpty,
                    style: TextStyle(color: scheme.onSurfaceVariant));
              }
              final max = rows.fold<int>(
                  0, (m, r) => r.salesAmount > m ? r.salesAmount : m);
              return Column(
                children: [
                  for (final r in rows)
                    Padding(
                      padding: const EdgeInsets.symmetric(vertical: 3),
                      child: Row(
                        children: [
                          SizedBox(
                            width: 74,
                            child: Text(_dayLabel(r.day),
                                style: TextStyle(
                                    color: scheme.onSurfaceVariant,
                                    fontSize: 12)),
                          ),
                          Expanded(
                            child: ClipRRect(
                              borderRadius: BorderRadius.circular(4),
                              child: LinearProgressIndicator(
                                value: max > 0 ? r.salesAmount / max : 0,
                                minHeight: 8,
                                backgroundColor: scheme.surfaceContainerHighest,
                              ),
                            ),
                          ),
                          const SizedBox(width: 8),
                          Text(formatMoney(r.salesAmount, 'ARS'),
                              style: const TextStyle(fontSize: 12)),
                        ],
                      ),
                    ),
                ],
              );
            },
          ),
        ],
      ),
    );
  }

  String _dayLabel(String iso) {
    // "2026-09-02" → "02/09"
    final parts = iso.split('-');
    if (parts.length == 3) return '${parts[2]}/${parts[1]}';
    return iso;
  }

  Widget _expensesByCategory(BuildContext context, Strings s) {
    final scheme = Theme.of(context).colorScheme;
    final async = ref.watch(expenseBreakdownProvider(_range));
    return GlassPanel(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(s.repExpensesByCategory,
              style: Theme.of(context).textTheme.titleSmall),
          const SizedBox(height: 8),
          async.when(
            loading: () => const _Loading(),
            error: (e, _) => ErrorView(
                error: e,
                onRetry: () => ref.invalidate(expenseBreakdownProvider(_range))),
            data: (b) {
              if (b.rows.isEmpty) {
                return Text(s.repExpensesEmpty,
                    style: TextStyle(color: scheme.onSurfaceVariant));
              }
              return Column(
                children: [
                  for (final r in b.rows)
                    Padding(
                      padding: const EdgeInsets.symmetric(vertical: 2),
                      child: Row(
                        children: [
                          Expanded(child: Text(r.category)),
                          if (r.delta != 0) ...[
                            Text(
                              '${r.delta > 0 ? '▲' : '▼'} ${formatMoney(r.delta.abs(), b.currency)}',
                              style: TextStyle(
                                  fontSize: 11,
                                  color: r.delta > 0
                                      ? scheme.error
                                      : scheme.primary),
                            ),
                            const SizedBox(width: 8),
                          ],
                          Text(formatMoney(r.amount, b.currency),
                              style: const TextStyle(
                                  fontWeight: FontWeight.w600)),
                        ],
                      ),
                    ),
                  const Divider(),
                  Row(
                    children: [
                      Expanded(
                          child: Text(s.repTotal,
                              style:
                                  const TextStyle(fontWeight: FontWeight.w600))),
                      Text(formatMoney(b.total, b.currency),
                          style: const TextStyle(fontWeight: FontWeight.w700)),
                    ],
                  ),
                ],
              );
            },
          ),
        ],
      ),
    );
  }

  Widget _topProducts(BuildContext context, Strings s) {
    final async = ref.watch(productPerfProvider(_range));
    return async.when(
      loading: () => const _Loading(),
      error: (e, _) => ErrorView(
          error: e, onRetry: () => ref.invalidate(productPerfProvider(_range))),
      data: (list) => list.isEmpty
          ? GlassPanel(child: Text(s.productosEmpty))
          : GlassPanel(
              padding: const EdgeInsets.symmetric(vertical: 4),
              child: Material(
                type: MaterialType.transparency,
                child: Column(
                  children: [
                    for (var i = 0; i < list.length; i++) ...[
                      if (i > 0) const Divider(height: 1),
                      ListTile(
                        title: Text(list[i].productName),
                        subtitle: Text(s.repUnits(list[i].unitsSold)),
                        trailing: Text(
                            formatMoney(list[i].marginAmount, list[i].currency)),
                      ),
                    ],
                  ],
                ),
              ),
            ),
    );
  }

  Widget _paymentMix(BuildContext context, Strings s) {
    final async = ref.watch(paymentMixProvider(_range));
    return async.when(
      loading: () => const _Loading(),
      error: (e, _) => ErrorView(
          error: e, onRetry: () => ref.invalidate(paymentMixProvider(_range))),
      data: (rows) {
        final inflow = rows.where((r) => r.direction == 'INFLOW').toList();
        if (inflow.isEmpty) {
          return GlassPanel(child: Text(s.financeExpenseEmpty));
        }
        return GlassPanel(
          child: Column(
            children: [
              for (final r in inflow)
                Padding(
                  padding: const EdgeInsets.symmetric(vertical: 2),
                  child: Row(
                    children: [
                      Text(
                          '${s.methodLabel(PaymentMethod.fromApi(r.method))} (${r.count})'),
                      const Spacer(),
                      Text(formatMoney(r.amount, 'ARS')),
                    ],
                  ),
                ),
            ],
          ),
        );
      },
    );
  }
}

class _Loading extends StatelessWidget {
  const _Loading();
  @override
  Widget build(BuildContext context) => const Padding(
        padding: EdgeInsets.all(16),
        child: Center(child: CircularProgressIndicator()),
      );
}
