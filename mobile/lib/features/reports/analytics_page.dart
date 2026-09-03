import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../l10n/strings.dart';
import '../../ui/app_background.dart';
import '../../ui/glass_panel.dart';
import '../../ui/state_views.dart';
import '../../util/money.dart';
import '../cashier/payment_dtos.dart';
import '../finance/finance_range.dart';
import 'reports_repository.dart';

/// Analítica (paridad con `/app/analytics` del web): KPIs de facturación +
/// mix de pagos (ingresos/egresos) + top productos con food cost y margen.
class AnalyticsPage extends ConsumerStatefulWidget {
  const AnalyticsPage({super.key});

  @override
  ConsumerState<AnalyticsPage> createState() => _AnalyticsPageState();
}

class _AnalyticsPageState extends ConsumerState<AnalyticsPage> {
  FinanceRange _range = FinanceRange.month;

  @override
  Widget build(BuildContext context) {
    final s = context.s;
    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(
          title: Text(s.analyticsTitle), backgroundColor: Colors.transparent),
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
                      ref.invalidate(revenueProvider(_range));
                      ref.invalidate(paymentMixProvider(_range));
                      ref.invalidate(productPerfProvider(_range));
                    },
                    child: ListView(
                      physics: const AlwaysScrollableScrollPhysics(),
                      padding: const EdgeInsets.all(16),
                      children: [
                        _kpis(context, s),
                        const SizedBox(height: 20),
                        Text(s.anPaymentMixTitle,
                            style: Theme.of(context).textTheme.titleSmall),
                        Text(s.anPaymentMixHint,
                            style: TextStyle(
                                color:
                                    Theme.of(context).colorScheme.onSurfaceVariant,
                                fontSize: 12)),
                        const SizedBox(height: 8),
                        _paymentMix(context, s),
                        const SizedBox(height: 20),
                        Text(s.anTopProducts,
                            style: Theme.of(context).textTheme.titleSmall),
                        const SizedBox(height: 8),
                        _products(context, s),
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

  Widget _kpis(BuildContext context, Strings s) {
    final async = ref.watch(revenueProvider(_range));
    return async.when(
      loading: () => const _Loading(),
      error: (e, _) => ErrorView(
          error: e, onRetry: () => ref.invalidate(revenueProvider(_range))),
      data: (r) {
        Widget k(String label, int v, {String? hint, bool negative = false}) =>
            _kpiCard(context, label, formatMoney(v, r.currency),
                hint: hint, negative: negative);
        return twoColGrid([
          k(s.repSales, r.salesAmount),
          k(s.anCollected, r.collectedAmount),
          k(s.anExpenses, r.expenseAmount),
          k(s.anGrossMargin, r.grossMarginAmount,
              hint: s.anGrossMarginHint, negative: r.grossMarginAmount < 0),
          k(s.homeAvgTicket, r.averageTicketAmount,
              hint: s.anOrdersCount(r.ordersCount)),
          k(s.anFoodCost, r.foodCostAmount),
        ]);
      },
    );
  }

  Widget _kpiCard(BuildContext context, String label, String value,
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
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(color: scheme.onSurfaceVariant, fontSize: 11)),
        ],
      ),
    );
  }

  Widget _paymentMix(BuildContext context, Strings s) {
    final scheme = Theme.of(context).colorScheme;
    final async = ref.watch(paymentMixProvider(_range));
    return async.when(
      loading: () => const _Loading(),
      error: (e, _) => ErrorView(
          error: e, onRetry: () => ref.invalidate(paymentMixProvider(_range))),
      data: (rows) {
        if (rows.isEmpty) return GlassPanel(child: Text(s.anMixEmpty));
        return GlassPanel(
          child: Column(
            children: [
              for (final r in rows)
                Padding(
                  padding: const EdgeInsets.symmetric(vertical: 3),
                  child: Row(
                    children: [
                      Expanded(
                          child: Text(
                              s.methodLabel(PaymentMethod.fromApi(r.method)))),
                      Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 8, vertical: 2),
                        decoration: BoxDecoration(
                          color: (r.direction == 'INFLOW'
                                  ? scheme.primary
                                  : scheme.onSurfaceVariant)
                              .withValues(alpha: 0.15),
                          borderRadius: BorderRadius.circular(999),
                        ),
                        child: Text(
                            r.direction == 'INFLOW' ? s.anInflow : s.anOutflow,
                            style: TextStyle(
                                fontSize: 11,
                                color: r.direction == 'INFLOW'
                                    ? scheme.primary
                                    : scheme.onSurfaceVariant)),
                      ),
                      const SizedBox(width: 8),
                      Text('${r.count}',
                          style: TextStyle(
                              color: scheme.onSurfaceVariant, fontSize: 12)),
                      const SizedBox(width: 12),
                      Text(formatMoney(r.amount, 'ARS'),
                          style: const TextStyle(fontWeight: FontWeight.w600)),
                    ],
                  ),
                ),
            ],
          ),
        );
      },
    );
  }

  Widget _products(BuildContext context, Strings s) {
    final scheme = Theme.of(context).colorScheme;
    final async = ref.watch(productPerfProvider(_range));
    return async.when(
      loading: () => const _Loading(),
      error: (e, _) => ErrorView(
          error: e, onRetry: () => ref.invalidate(productPerfProvider(_range))),
      data: (list) {
        if (list.isEmpty) return GlassPanel(child: Text(s.productosEmpty));
        return GlassPanel(
          padding: const EdgeInsets.symmetric(vertical: 4),
          child: Material(
            type: MaterialType.transparency,
            child: Column(
              children: [
                for (var i = 0; i < list.length; i++) ...[
                  if (i > 0) const Divider(height: 1),
                  ListTile(
                    title: Text(list[i].productName),
                    subtitle: Text(
                        '${s.repUnits(list[i].unitsSold)} · ${s.anFoodCost} ${formatMoney(list[i].foodCostAmount, list[i].currency)}',
                        style: TextStyle(
                            color: scheme.onSurfaceVariant, fontSize: 12)),
                    trailing: Text(
                        formatMoney(list[i].marginAmount, list[i].currency),
                        style: TextStyle(
                            fontWeight: FontWeight.w600,
                            color: list[i].marginAmount < 0
                                ? scheme.error
                                : scheme.onSurface)),
                  ),
                ],
              ],
            ),
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
