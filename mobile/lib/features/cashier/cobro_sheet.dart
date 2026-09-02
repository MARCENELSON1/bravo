import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/api_error.dart';
import '../../l10n/strings.dart';
import '../../util/money.dart';
import '../invoices/invoice_repository.dart';
import '../order/order_providers.dart';
import 'cash_providers.dart';
import 'payment_dtos.dart';

/// Cobro de una orden (Fase 3): registra pagos (efectivo/tarjeta/transferencia/QR),
/// muestra el restante y los pagos, permite reembolsar y reabrir. El pago online
/// (MercadoPago) queda para la Carta QR del comensal.
class CobroSheet extends ConsumerStatefulWidget {
  const CobroSheet({super.key, required this.orderId});

  final String orderId;

  @override
  ConsumerState<CobroSheet> createState() => _CobroSheetState();
}

class _CobroSheetState extends ConsumerState<CobroSheet> {
  static const _methods = [
    PaymentMethod.cash,
    PaymentMethod.card,
    PaymentMethod.transfer,
    PaymentMethod.qr,
  ];

  PaymentMethod _method = PaymentMethod.cash;
  final _amount = TextEditingController();
  final _tip = TextEditingController();

  String get orderId => widget.orderId;

  @override
  void dispose() {
    _amount.dispose();
    _tip.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final s = context.s;
    final order = ref.watch(orderControllerProvider(orderId)).valueOrNull;
    final payments =
        ref.watch(orderPaymentsProvider(orderId)).valueOrNull ?? const [];
    final currency = order?.currency ?? 'ARS';
    final total = order?.totalAmount ?? 0;
    final paid =
        payments.where((p) => p.isConfirmedInflow).fold(0, (a, p) => a + p.amount);
    final remaining = (total - paid).clamp(0, total);

    return Padding(
      padding: EdgeInsets.only(
        left: 16,
        right: 16,
        top: 16,
        bottom: MediaQuery.of(context).viewInsets.bottom + 16,
      ),
      child: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              children: [
                Text(s.cobroRemaining,
                    style: Theme.of(context).textTheme.titleMedium),
                const Spacer(),
                Text(
                  formatMoney(remaining, currency),
                  style: Theme.of(context)
                      .textTheme
                      .titleMedium
                      ?.copyWith(fontWeight: FontWeight.w700),
                ),
              ],
            ),
            const SizedBox(height: 12),
            if (remaining > 0) ...[
              Wrap(
                spacing: 8,
                children: [
                  for (final m in _methods)
                    ChoiceChip(
                      label: Text(s.methodLabel(m)),
                      selected: _method == m,
                      onSelected: (_) => setState(() => _method = m),
                    ),
                ],
              ),
              const SizedBox(height: 12),
              TextField(
                controller: _amount,
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                decoration: InputDecoration(labelText: s.cobroAmount),
              ),
              const SizedBox(height: 8),
              Wrap(
                spacing: 8,
                children: [
                  _preset(s.presetTotal, remaining),
                  _preset('½', remaining ~/ 2),
                  _preset('⅓', remaining ~/ 3),
                ],
              ),
              const SizedBox(height: 8),
              TextField(
                controller: _tip,
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                decoration: InputDecoration(labelText: s.cobroTip),
              ),
              const SizedBox(height: 12),
              FilledButton.icon(
                onPressed: _register,
                icon: const Icon(Icons.payments_outlined),
                label: Text(s.cobroRegister),
              ),
            ] else if (payments.isNotEmpty) ...[
              OutlinedButton.icon(
                onPressed: _reopen,
                icon: const Icon(Icons.lock_open_outlined),
                label: Text(s.cobroReopen),
              ),
              const SizedBox(height: 8),
              _invoiceSection(s),
            ],
            if (payments.isNotEmpty) ...[
              const Divider(height: 24),
              Text(s.cobroPayments, style: Theme.of(context).textTheme.titleSmall),
              for (final p in payments)
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  title: Text(s.methodLabel(p.method)),
                  subtitle: Text(p.status),
                  trailing: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(formatMoney(p.amount, p.currency)),
                      if (p.isRefundable)
                        IconButton(
                          tooltip: s.cobroRefund,
                          icon: const Icon(Icons.undo, size: 18),
                          onPressed: () => _refund(p.id),
                        ),
                    ],
                  ),
                ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _preset(String label, int minor) => ActionChip(
        label: Text(label),
        onPressed: () => _amount.text = (minor / 100).toStringAsFixed(2),
      );

  Future<void> _register() async {
    final s = context.s;
    final amount = pesosToMinor(_amount.text) ?? 0;
    if (amount <= 0) return;
    final tip = pesosToMinor(_tip.text) ?? 0;
    try {
      final payment = await ref.read(paymentRepositoryProvider).register(
            orderId,
            method: _method,
            amount: amount,
            tip: tip,
          );
      ref.invalidate(orderPaymentsProvider(orderId));
      ref.invalidate(orderControllerProvider(orderId));
      _amount.clear();
      _tip.clear();
      if (payment.checkoutUrl != null) {
        _toast('MercadoPago: cobrar online por la Carta QR');
      }
    } on ApiError catch (e) {
      if (e.code == 'no_open_cash_session') {
        _toast(s.cobroNoSession);
      } else {
        _toast(e.message);
      }
    }
  }

  Future<void> _refund(String paymentId) async {
    try {
      await ref.read(paymentRepositoryProvider).refund(paymentId);
      ref.invalidate(orderPaymentsProvider(orderId));
      ref.invalidate(orderControllerProvider(orderId));
    } on ApiError catch (e) {
      _toast(e.message);
    }
  }

  Future<void> _reopen() async {
    try {
      await ref.read(paymentRepositoryProvider).reopen(orderId);
      ref.invalidate(orderPaymentsProvider(orderId));
      ref.invalidate(orderControllerProvider(orderId));
      if (mounted) Navigator.of(context).pop();
    } on ApiError catch (e) {
      _toast(e.message);
    }
  }

  Widget _invoiceSection(Strings s) {
    final invoice = ref.watch(orderInvoiceProvider(orderId)).valueOrNull;
    if (invoice != null) {
      final num = '${invoice.pointOfSale ?? ''}-${invoice.number ?? ''}';
      final cae = invoice.cae != null ? ' · CAE ${invoice.cae}' : '';
      return Text('${s.invoiceIssued}: ${invoice.type} $num$cae');
    }
    return FilledButton.icon(
      onPressed: _factura,
      icon: const Icon(Icons.receipt_long_outlined),
      label: Text(s.facturar),
    );
  }

  Future<void> _factura() async {
    final s = context.s;
    var docType = DocType.consumidorFinal;
    final numCtrl = TextEditingController();
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setDialog) => AlertDialog(
          title: Text(s.facturar),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              DropdownButtonFormField<DocType>(
                initialValue: docType,
                decoration: InputDecoration(labelText: s.docTypeLabel),
                items: [
                  for (final t in DocType.values)
                    DropdownMenuItem(value: t, child: Text(s.docTypeName(t))),
                ],
                onChanged: (v) {
                  if (v != null) setDialog(() => docType = v);
                },
              ),
              if (docType != DocType.consumidorFinal) ...[
                const SizedBox(height: 8),
                TextField(
                  controller: numCtrl,
                  keyboardType: TextInputType.number,
                  decoration: InputDecoration(labelText: s.docNumber),
                ),
              ],
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(ctx).pop(false),
              child: Text(MaterialLocalizations.of(ctx).cancelButtonLabel),
            ),
            FilledButton(
              onPressed: () => Navigator.of(ctx).pop(true),
              child: Text(s.facturar),
            ),
          ],
        ),
      ),
    );
    if (ok != true) return;
    try {
      await ref.read(invoiceRepositoryProvider).issueForOrder(
            orderId,
            docType: docType,
            docNumber:
                docType == DocType.consumidorFinal ? null : numCtrl.text.trim(),
          );
      ref.invalidate(orderInvoiceProvider(orderId));
    } on ApiError catch (e) {
      _toast(e.message);
    }
  }

  void _toast(String message) {
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(message)));
    }
  }
}
