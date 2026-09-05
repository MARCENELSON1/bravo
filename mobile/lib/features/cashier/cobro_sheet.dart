import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/api_error.dart';
import '../../l10n/strings.dart';
import '../../ui/state_views.dart';
import '../../util/money.dart';
import '../invoices/invoice_repository.dart';
import '../floor/floor_providers.dart';
import '../order/order_dtos.dart';
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
  bool _detailOpen =
      true; // el detalle arranca visible: es lo que se lee al cobrar
  bool _closing = false;
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
    final paid = payments
        .where((p) => p.isConfirmedInflow)
        .fold(0, (a, p) => a + p.amount);
    final remaining = (total - paid).clamp(0, total);
    final isPaid = order?.status == 'PAID';
    final tips = payments
        .where((p) => p.isConfirmedInflow)
        .fold(0, (a, p) => a + p.tipAmount);

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
            // Qué se está cobrando: el mozo puede leerle la cuenta al cliente
            // sin salir del cobro (cantidades, modificadores y precio por línea).
            if (order != null) _detail(context, s, order, paid, tips),
            Row(
              children: [
                Text(
                  s.cobroRemaining,
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const Spacer(),
                Text(
                  formatMoney(remaining, currency),
                  style: Theme.of(context).textTheme.titleMedium
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
                keyboardType: const TextInputType.numberWithOptions(
                  decimal: true,
                ),
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
                keyboardType: const TextInputType.numberWithOptions(
                  decimal: true,
                ),
                decoration: InputDecoration(labelText: s.cobroTip),
              ),
              const SizedBox(height: 12),
              FilledButton.icon(
                onPressed: _register,
                icon: const Icon(Icons.payments_outlined),
                label: Text(s.cobroRegister),
              ),
            ] else if (payments.isNotEmpty) ...[
              // Saldo 0 pero la comanda no está cerrada (la reabrieron y no le
              // agregaron nada): la plata ya está, solo falta volver a cerrarla.
              // Sin esto, facturar falla con "tiene que estar pagada".
              if (!isPaid) ...[
                Text(
                  s.cobroCloseHint,
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: Theme.of(context).colorScheme.onSurfaceVariant,
                  ),
                ),
                const SizedBox(height: 8),
                FilledButton.icon(
                  onPressed: _closing ? null : _close,
                  icon: const Icon(Icons.lock_outline),
                  label: Text(s.cobroClose),
                ),
              ] else ...[
                OutlinedButton.icon(
                  onPressed: _reopen,
                  icon: const Icon(Icons.lock_open_outlined),
                  label: Text(s.cobroReopen),
                ),
                const SizedBox(height: 8),
                _invoiceSection(s),
              ],
            ],
            if (payments.isNotEmpty) ...[
              const Divider(height: 24),
              Text(
                s.cobroPayments,
                style: Theme.of(context).textTheme.titleSmall,
              ),
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

  /// Detalle de la cuenta: cada línea con cantidad, personalización y precio,
  /// más el subtotal y lo ya pagado. Colapsable para no empujar los controles
  /// de cobro cuando la comanda es larga.
  Widget _detail(
    BuildContext context,
    Strings s,
    Order order,
    int paid,
    int tips,
  ) {
    final theme = Theme.of(context);
    final muted = theme.colorScheme.onSurfaceVariant;
    final items = order.liveItems;
    if (items.isEmpty) return const SizedBox.shrink();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        InkWell(
          onTap: () => setState(() => _detailOpen = !_detailOpen),
          child: Padding(
            padding: const EdgeInsets.symmetric(vertical: 4),
            child: Row(
              children: [
                Text(s.cobroDetail, style: theme.textTheme.titleSmall),
                const SizedBox(width: 6),
                Text(
                  s.ticketItems(items.length),
                  style: theme.textTheme.labelSmall?.copyWith(color: muted),
                ),
                const Spacer(),
                Icon(
                  _detailOpen ? Icons.expand_less : Icons.expand_more,
                  color: muted,
                ),
              ],
            ),
          ),
        ),
        if (_detailOpen) ...[
          for (final it in items)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 3),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  SizedBox(
                    width: 34,
                    child: Text(
                      '${it.quantity}×',
                      style: theme.textTheme.bodyMedium?.copyWith(
                        fontWeight: FontWeight.w700,
                        fontFeatures: const [FontFeature.tabularFigures()],
                      ),
                    ),
                  ),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(it.name, style: theme.textTheme.bodyMedium),
                        if (it.selectedOptions.isNotEmpty)
                          Text(
                            it.selectedOptions.map((o) => o.name).join(' · '),
                            style: theme.textTheme.bodySmall?.copyWith(
                              color: muted,
                            ),
                          ),
                        if (it.note != null && it.note!.isNotEmpty)
                          Text(
                            '› ${it.note}',
                            style: theme.textTheme.bodySmall?.copyWith(
                              color: muted,
                            ),
                          ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 8),
                  Text(
                    formatMoney(it.lineTotal, order.currency),
                    style: theme.textTheme.bodyMedium?.copyWith(
                      fontFeatures: const [FontFeature.tabularFigures()],
                    ),
                  ),
                ],
              ),
            ),
          const Divider(height: 18),
          _totalRow(
            context,
            s.cobroSubtotal,
            order.totalAmount,
            order.currency,
            bold: true,
          ),
          if (paid > 0)
            _totalRow(context, s.cobroPaid, -paid, order.currency, muted: true),
          if (tips > 0)
            _totalRow(
              context,
              s.cobroTipsIncluded,
              tips,
              order.currency,
              muted: true,
            ),
          const SizedBox(height: 6),
        ],
        const Divider(height: 18),
      ],
    );
  }

  Widget _totalRow(
    BuildContext context,
    String label,
    int amount,
    String currency, {
    bool bold = false,
    bool muted = false,
  }) {
    final theme = Theme.of(context);
    final color = muted ? theme.colorScheme.onSurfaceVariant : null;
    final style = theme.textTheme.bodyMedium?.copyWith(
      fontWeight: bold ? FontWeight.w700 : null,
      color: color,
      fontFeatures: const [FontFeature.tabularFigures()],
    );
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Row(
        children: [
          Text(label, style: style),
          const Spacer(),
          Text(formatMoney(amount, currency), style: style),
        ],
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
      final payment = await ref
          .read(paymentRepositoryProvider)
          .register(orderId, method: _method, amount: amount, tip: tip);
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
    final s = context.s;
    final ok = await confirmDialog(
      context,
      title: s.refundConfirmTitle,
      message: s.refundConfirmBody,
      confirmLabel: s.cobroRefund,
    );
    if (!ok) return;
    try {
      await ref.read(paymentRepositoryProvider).refund(paymentId);
      ref.invalidate(orderPaymentsProvider(orderId));
      ref.invalidate(orderControllerProvider(orderId));
    } on ApiError catch (e) {
      _toast(e.message);
    }
  }

  /// Volver a cerrar una comanda reabierta cuyo saldo ya está cubierto. Usa el
  /// mismo caso de uso que "Liberar mesa": el server la cierra SOLO si los pagos
  /// confirmados alcanzan el total (si falta plata, la rechaza).
  Future<void> _close() async {
    final s = context.s;
    final messenger = ScaffoldMessenger.of(context);
    setState(() => _closing = true);
    try {
      await ref.read(orderRepositoryProvider).free(orderId);
      ref.invalidate(orderControllerProvider(orderId));
      ref.invalidate(orderPaymentsProvider(orderId));
      messenger.showSnackBar(SnackBar(content: Text(s.cobroClosed)));
    } on ApiError catch (e) {
      messenger.showSnackBar(SnackBar(content: Text(e.message)));
    } finally {
      if (mounted) setState(() => _closing = false);
    }
  }

  Future<void> _reopen() async {
    final s = context.s;
    final ok = await confirmDialog(
      context,
      title: s.reopenConfirmTitle,
      message: s.reopenConfirmBody,
      confirmLabel: s.cobroReopen,
    );
    if (!ok) return;
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
      await ref
          .read(invoiceRepositoryProvider)
          .issueForOrder(
            orderId,
            docType: docType,
            docNumber: docType == DocType.consumidorFinal
                ? null
                : numCtrl.text.trim(),
          );
      ref.invalidate(orderInvoiceProvider(orderId));
    } on ApiError catch (e) {
      _toast(e.message);
    }
  }

  void _toast(String message) {
    if (mounted) {
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text(message)));
    }
  }
}
