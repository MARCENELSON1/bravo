import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../l10n/strings.dart';
import '../../ui/app_background.dart';
import '../../ui/glass_panel.dart';
import '../../util/money.dart';
import '../cashier/payment_dtos.dart';
import 'reports_repository.dart';

/// Reportes (Fase 6, consulta): ventas, top productos y mix de pagos.
class ReportesPage extends ConsumerWidget {
  const ReportesPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = context.s;
    final revenue = ref.watch(revenueProvider);
    final products = ref.watch(productPerfProvider);
    final mix = ref.watch(paymentMixProvider);

    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(title: Text(s.reportesTitle), backgroundColor: Colors.transparent),
      body: Stack(
        children: [
          const AppBackground(),
          SafeArea(
            child: ListView(
              padding: const EdgeInsets.all(16),
              children: [
                revenue.when(
                  loading: () => const _Loading(),
                  error: (e, _) => const SizedBox.shrink(),
                  data: (r) => GlassPanel(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        _row(s.homeSales, formatMoney(r.salesAmount, r.currency)),
                        _row(s.homeCollected,
                            formatMoney(r.collectedAmount, r.currency)),
                        _row(s.repMargin,
                            formatMoney(r.grossMarginAmount, r.currency)),
                        _row(s.repOrders, '${r.ordersCount}'),
                        _row(s.homeAvgTicket,
                            formatMoney(r.averageTicketAmount, r.currency)),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                Text(s.repTopProducts, style: Theme.of(context).textTheme.titleSmall),
                const SizedBox(height: 8),
                products.when(
                  loading: () => const _Loading(),
                  error: (e, _) => const SizedBox.shrink(),
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
                                    trailing: Text(formatMoney(
                                        list[i].marginAmount, list[i].currency)),
                                  ),
                                ],
                              ],
                            ),
                          ),
                        ),
                ),
                const SizedBox(height: 16),
                Text(s.repPaymentMix, style: Theme.of(context).textTheme.titleSmall),
                const SizedBox(height: 8),
                mix.when(
                  loading: () => const _Loading(),
                  error: (e, _) => const SizedBox.shrink(),
                  data: (rows) {
                    final inflow =
                        rows.where((r) => r.direction == 'INFLOW').toList();
                    if (inflow.isEmpty) return const SizedBox.shrink();
                    return GlassPanel(
                      child: Column(
                        children: [
                          for (final r in inflow)
                            _row(
                              '${s.methodLabel(PaymentMethod.fromApi(r.method))} (${r.count})',
                              formatMoney(r.amount, 'ARS'),
                            ),
                        ],
                      ),
                    );
                  },
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _row(String label, String value) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 2),
        child: Row(children: [Text(label), const Spacer(), Text(value)]),
      );
}

class _Loading extends StatelessWidget {
  const _Loading();
  @override
  Widget build(BuildContext context) => const Padding(
        padding: EdgeInsets.all(16),
        child: Center(child: CircularProgressIndicator()),
      );
}
