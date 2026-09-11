import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../l10n/strings.dart';
import '../../theme/colors.dart';
import '../../util/money.dart';
import 'finance_repository.dart';
import 'finance_range.dart';

final _detailProvider = FutureProvider.autoDispose
    .family<ProductDetail, ({String productId, FinanceRange range})>(
  (ref, args) => ref
      .read(financeRepositoryProvider)
      .productDetail(args.productId, rangeWindow(args.range)),
);

/// Drill-down de un plato: en qué se fue el margen del período.
///
/// Existía en la web y no acá, y es la pregunta que sigue naturalmente a ver la
/// lista de márgenes: "este plato me deja poco… ¿por qué?". Muestra tres cosas
/// que el backend ya calcula sobre la ventana ENTERA —totales, evolución del
/// costo por día y las últimas ventas— y avisa cuando el listado viene acotado,
/// para que nadie lo lea como si fuera todo lo vendido.
class ProductDetailSheet extends ConsumerWidget {
  const ProductDetailSheet({
    super.key,
    required this.productId,
    required this.productName,
    required this.range,
  });

  final String productId;
  final String productName;
  final FinanceRange range;

  static Future<void> show(
    BuildContext context, {
    required String productId,
    required String productName,
    required FinanceRange range,
  }) =>
      showModalBottomSheet<void>(
        context: context,
        isScrollControlled: true,
        showDragHandle: true,
        builder: (_) => ProductDetailSheet(
          productId: productId,
          productName: productName,
          range: range,
        ),
      );

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = context.s;
    final theme = Theme.of(context);
    final scheme = theme.colorScheme;
    final async = ref.watch(_detailProvider((productId: productId, range: range)));

    return DraggableScrollableSheet(
      expand: false,
      initialChildSize: 0.7,
      maxChildSize: 0.92,
      builder: (context, controller) => async.when(
        loading: () => const Center(child: Padding(
          padding: EdgeInsets.all(48), child: CircularProgressIndicator())),
        error: (e, _) => Center(
          child: Padding(
            padding: const EdgeInsets.all(32),
            child: Text(s.financeProductDetailError, textAlign: TextAlign.center),
          ),
        ),
        data: (d) => ListView(
          controller: controller,
          padding: const EdgeInsets.fromLTRB(20, 0, 20, 32),
          children: [
            Semantics(
              header: true,
              child: Text(productName, style: theme.textTheme.titleLarge),
            ),
            const SizedBox(height: 16),
            _Totals(detail: d),
            if (d.costSeries.length >= 2) ...[
              const SizedBox(height: 24),
              Text(s.financeCostEvolution, style: theme.textTheme.titleSmall),
              const SizedBox(height: 8),
              _CostSparkline(points: d.costSeries, currency: d.currency),
            ],
            const SizedBox(height: 24),
            Text(s.financeRecentSales, style: theme.textTheme.titleSmall),
            const SizedBox(height: 4),
            if (d.lines.isEmpty)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 16),
                child: Text(s.financeNoSalesInPeriod,
                    style: TextStyle(color: scheme.onSurfaceVariant)),
              )
            else ...[
              for (final l in d.lines.take(30))
                Padding(
                  padding: const EdgeInsets.symmetric(vertical: 6),
                  child: Row(
                    children: [
                      Expanded(child: Text(_day(l.occurredAt))),
                      Text('${l.quantity}× ',
                          style: TextStyle(color: scheme.onSurfaceVariant)),
                      Text(formatMoney(l.marginAmount, d.currency),
                          style: const TextStyle(fontWeight: FontWeight.w600)),
                    ],
                  ),
                ),
              // El listado viene acotado por el backend; decirlo es lo que evita
              // que se lea como si fuera todo lo vendido del plato.
              if (d.linesTruncated)
                Padding(
                  padding: const EdgeInsets.only(top: 12),
                  child: Text(
                    s.financeLinesTruncated(d.lines.length),
                    style: TextStyle(
                        color: scheme.onSurfaceVariant,
                        fontStyle: FontStyle.italic,
                        fontSize: 12),
                  ),
                ),
            ],
          ],
        ),
      ),
    );
  }

  static String _day(String iso) =>
      iso.length >= 10 ? '${iso.substring(8, 10)}/${iso.substring(5, 7)}' : iso;
}

class _Totals extends StatelessWidget {
  const _Totals({required this.detail});
  final ProductDetail detail;

  @override
  Widget build(BuildContext context) {
    final s = context.s;
    final scheme = Theme.of(context).colorScheme;
    Widget cell(String label, String value, {Color? color}) => Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(label,
                  style: TextStyle(color: scheme.onSurfaceVariant, fontSize: 12)),
              const SizedBox(height: 2),
              Text(value,
                  style: TextStyle(fontWeight: FontWeight.w700, color: color)),
            ],
          ),
        );
    final negative = detail.marginAmount < 0;
    return Column(
      children: [
        Row(children: [
          cell(s.financeUnits, '${detail.unitsSold}'),
          cell(s.financeSalesLabel,
              formatMoney(detail.salesAmount, detail.currency)),
        ]),
        const SizedBox(height: 14),
        Row(children: [
          cell(s.financeFoodCost,
              formatMoney(detail.foodCostAmount, detail.currency)),
          cell(
            s.financeLeavesYou,
            formatMoney(detail.marginAmount, detail.currency),
            color: negative ? scheme.error : null,
          ),
        ]),
      ],
    );
  }
}

/// Evolución del costo unitario. Un sparkline y no una tabla: la pregunta es
/// "¿se está encareciendo?", que se contesta con la forma, no con los números.
class _CostSparkline extends StatelessWidget {
  const _CostSparkline({required this.points, required this.currency});
  final List<ProductCostPoint> points;
  final String currency;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final first = points.first.unitCost;
    final last = points.last.unitCost;
    final worse = last > first;
    return Semantics(
      label: context.s.financeCostWentFromTo(
          formatMoney(first, currency), formatMoney(last, currency)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            height: 56,
            child: CustomPaint(
              size: const Size(double.infinity, 56),
              painter: _SparkPainter(
                values: [for (final p in points) p.unitCost.toDouble()],
                color: worse
                    ? WellnodPalette.warnOn(Theme.of(context).brightness)
                    : WellnodPalette.successOn(Theme.of(context).brightness),
              ),
            ),
          ),
          const SizedBox(height: 6),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(formatMoney(first, currency),
                  style: TextStyle(color: scheme.onSurfaceVariant, fontSize: 12)),
              Text(formatMoney(last, currency),
                  style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 12)),
            ],
          ),
        ],
      ),
    );
  }
}

class _SparkPainter extends CustomPainter {
  _SparkPainter({required this.values, required this.color});
  final List<double> values;
  final Color color;

  @override
  void paint(Canvas canvas, Size size) {
    if (values.length < 2) return;
    final lo = values.reduce((a, b) => a < b ? a : b);
    final hi = values.reduce((a, b) => a > b ? a : b);
    final span = (hi - lo).abs() < 1 ? 1.0 : hi - lo;
    final path = Path();
    for (var i = 0; i < values.length; i++) {
      final x = size.width * (i / (values.length - 1));
      final y = size.height - ((values[i] - lo) / span) * size.height;
      i == 0 ? path.moveTo(x, y) : path.lineTo(x, y);
    }
    canvas.drawPath(
      path,
      Paint()
        ..color = color
        ..strokeWidth = 2
        ..style = PaintingStyle.stroke
        ..strokeCap = StrokeCap.round
        ..strokeJoin = StrokeJoin.round,
    );
  }

  @override
  bool shouldRepaint(_SparkPainter old) =>
      old.values != values || old.color != color;
}
