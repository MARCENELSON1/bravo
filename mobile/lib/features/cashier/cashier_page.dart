import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/api_error.dart';
import '../../l10n/strings.dart';
import '../../ui/glass_panel.dart';
import '../../util/money.dart';
import 'cash_dtos.dart';
import 'cash_providers.dart';
import 'payment_dtos.dart';

/// Pantalla de Caja (Fase 3): abrir la caja con un fondo, verla, y cerrarla con
/// el arqueo Z (contado por método). Tab body (sin Scaffold), como Piso/KDS.
class CashierPage extends ConsumerStatefulWidget {
  const CashierPage({super.key});

  @override
  ConsumerState<CashierPage> createState() => _CashierPageState();
}

class _CashierPageState extends ConsumerState<CashierPage> {
  @override
  Widget build(BuildContext context) {
    final s = context.s;
    final async = ref.watch(currentCashSessionProvider);

    return async.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (e, _) => Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Text(e is ApiError ? e.message : '$e'),
        ),
      ),
      data: (session) => session == null
          ? _openForm(s)
          : _sessionView(s, session),
    );
  }

  Widget _openForm(Strings s) {
    final controller = TextEditingController();
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        GlassPanel(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(s.cashierClosed, style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: 12),
              TextField(
                controller: controller,
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                decoration: InputDecoration(labelText: s.cashierOpeningFloat),
              ),
              const SizedBox(height: 16),
              FilledButton.icon(
                onPressed: () => _open(pesosToMinor(controller.text) ?? 0),
                icon: const Icon(Icons.lock_open),
                label: Text(s.cashierOpen),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _sessionView(Strings s, CashSession session) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        GlassPanel(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(s.cashierTitle, style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: 8),
              Row(
                children: [
                  Text(s.cashierOpeningFloat),
                  const Spacer(),
                  Text(formatMoney(session.openingFloatAmount, session.currency)),
                ],
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),
        FilledButton.icon(
          onPressed: () => _closeSheet(s, session),
          icon: const Icon(Icons.lock_outline),
          label: Text(s.cashierClose),
        ),
      ],
    );
  }

  Future<void> _open(int float) async {
    try {
      await ref.read(cashRepositoryProvider).open(float);
      ref.invalidate(currentCashSessionProvider);
    } on ApiError catch (e) {
      _toast(e.message);
    }
  }

  Future<void> _closeSheet(Strings s, CashSession session) async {
    final controllers = {
      for (final m in [
        PaymentMethod.cash,
        PaymentMethod.card,
        PaymentMethod.transfer,
        PaymentMethod.qr,
      ])
        m: TextEditingController(),
    };

    final confirmed = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      builder: (ctx) => Padding(
        padding: EdgeInsets.only(
          left: 16,
          right: 16,
          top: 16,
          bottom: MediaQuery.of(ctx).viewInsets.bottom + 16,
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(s.cashierCountPrompt, style: Theme.of(ctx).textTheme.titleMedium),
            const SizedBox(height: 12),
            for (final entry in controllers.entries) ...[
              TextField(
                controller: entry.value,
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                decoration: InputDecoration(labelText: s.methodLabel(entry.key)),
              ),
              const SizedBox(height: 8),
            ],
            const SizedBox(height: 8),
            FilledButton(
              onPressed: () => Navigator.of(ctx).pop(true),
              child: Text(s.cashierClose),
            ),
          ],
        ),
      ),
    );

    if (confirmed != true) return;

    final counted = <String, int>{};
    for (final entry in controllers.entries) {
      final minor = pesosToMinor(entry.value.text);
      if (minor != null) counted[entry.key.api] = minor;
    }

    try {
      final report = await ref.read(cashRepositoryProvider).close(session.id, counted);
      ref.invalidate(currentCashSessionProvider);
      if (mounted) _showReport(s, report);
    } on ApiError catch (e) {
      _toast(e.message);
    }
  }

  void _showReport(Strings s, CashReport report) {
    showDialog<void>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(s.cashierArqueo),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            _reportRow(s.cashierExpected,
                formatMoney(report.expectedTotal, report.currency)),
            _reportRow(
                s.cashierCounted,
                report.countedTotal == null
                    ? '—'
                    : formatMoney(report.countedTotal!, report.currency)),
            _reportRow(
                s.cashierDifference,
                report.differenceTotal == null
                    ? '—'
                    : formatMoney(report.differenceTotal!, report.currency)),
            _reportRow(s.cashierTips, formatMoney(report.tipsTotal, report.currency)),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: const Text('OK'),
          ),
        ],
      ),
    );
  }

  Widget _reportRow(String label, String value) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 2),
        child: Row(
          children: [Text(label), const Spacer(), Text(value)],
        ),
      );

  void _toast(String message) {
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(message)));
    }
  }
}
