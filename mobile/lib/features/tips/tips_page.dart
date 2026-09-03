import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/api_error.dart';
import '../../l10n/strings.dart';
import '../../ui/app_background.dart';
import '../../ui/glass_panel.dart';
import '../../util/money.dart';
import '../cashier/payment_dtos.dart';
import 'tips_dtos.dart';
import 'tips_repository.dart';

/// Propinas (Fase 4): reporte por mozo (ganado/pagado/pendiente) + liquidación.
class TipsPage extends ConsumerStatefulWidget {
  const TipsPage({super.key});

  @override
  ConsumerState<TipsPage> createState() => _TipsPageState();
}

class _TipsPageState extends ConsumerState<TipsPage> {
  @override
  Widget build(BuildContext context) {
    final s = context.s;
    final async = ref.watch(tipsReportProvider);

    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(title: Text(s.tipsTitle), backgroundColor: Colors.transparent),
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
              data: (report) => _content(s, report),
            ),
          ),
        ],
      ),
    );
  }

  Widget _content(Strings s, TipsReport report) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        GlassPanel(
          child: Column(
            children: [
              _row(s.tipsEarned, formatMoney(report.earnedTotal, report.currency)),
              _row(s.tipsPaid, formatMoney(report.paidTotal, report.currency)),
              _row(s.tipsPending, formatMoney(report.pendingTotal, report.currency)),
            ],
          ),
        ),
        const SizedBox(height: 12),
        if (report.rows.isEmpty)
          GlassPanel(child: Text(s.tipsEmpty))
        else
          GlassPanel(
            padding: const EdgeInsets.symmetric(vertical: 4),
            child: Material(
              type: MaterialType.transparency,
              child: Column(
                children: [
                  for (final row in report.rows)
                    ListTile(
                      title: Text(row.waiterName),
                      subtitle: Text(
                          '${s.tipsPending}: ${formatMoney(row.pending, report.currency)}'),
                      trailing: row.pending > 0
                          ? TextButton(
                              onPressed: () => _payout(s, row, report.currency),
                              child: Text(s.tipsPay),
                            )
                          : null,
                    ),
                ],
              ),
            ),
          ),
      ],
    );
  }

  Widget _row(String label, String value) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 2),
        child: Row(children: [Text(label), const Spacer(), Text(value)]),
      );

  Future<void> _payout(Strings s, TipRow row, String currency) async {
    final amountCtrl =
        TextEditingController(text: (row.pending / 100).toStringAsFixed(2));
    var method = PaymentMethod.cash;

    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setDialog) => AlertDialog(
          title: Text('${s.tipsPay} · ${row.waiterName}'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: amountCtrl,
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                decoration: InputDecoration(labelText: s.cobroAmount),
              ),
              const SizedBox(height: 12),
              Wrap(
                spacing: 8,
                children: [
                  for (final m in [
                    PaymentMethod.cash,
                    PaymentMethod.transfer,
                    PaymentMethod.card,
                  ])
                    ChoiceChip(
                      label: Text(s.methodLabel(m)),
                      selected: method == m,
                      onSelected: (_) => setDialog(() => method = m),
                    ),
                ],
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(ctx).pop(false),
              child: Text(MaterialLocalizations.of(ctx).cancelButtonLabel),
            ),
            FilledButton(
              onPressed: () => Navigator.of(ctx).pop(true),
              child: Text(s.tipsPay),
            ),
          ],
        ),
      ),
    );

    if (ok != true) return;
    final amount = pesosToMinor(amountCtrl.text) ?? 0;
    if (amount <= 0) return;
    try {
      await ref
          .read(tipsRepositoryProvider)
          .payout(waiterId: row.waiterId, amount: amount, method: method);
      ref.invalidate(tipsReportProvider);
    } on ApiError catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(e.message)));
      }
    }
  }
}
