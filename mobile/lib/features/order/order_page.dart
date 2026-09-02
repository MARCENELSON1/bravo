import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/api_error.dart';
import '../../l10n/strings.dart';
import '../../ui/app_background.dart';
import '../../ui/glass_panel.dart';
import '../../util/money.dart';
import '../floor/floor_providers.dart';
import 'order_dtos.dart';

/// Tanda 1: comanda en modo lectura (ver ítems + total). La captura (grilla de
/// productos, agregar/editar/anular, marchar) llega en la Tanda 2.
final orderProvider = FutureProvider.family<Order, String>(
  (ref, id) => ref.read(orderRepositoryProvider).get(id),
);

class OrderPage extends ConsumerWidget {
  const OrderPage({super.key, required this.orderId});

  final String orderId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = context.s;
    final async = ref.watch(orderProvider(orderId));

    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(
        title: Text(s.orderTitle),
        backgroundColor: Colors.transparent,
      ),
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
              data: (order) => _content(context, s, order),
            ),
          ),
        ],
      ),
    );
  }

  Widget _content(BuildContext context, Strings s, Order order) {
    final items = order.liveItems;
    final theme = Theme.of(context);
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        GlassPanel(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                '${s.orderTotal}: ${formatMoney(order.totalAmount, order.currency)}',
                style: theme.textTheme.titleMedium
                    ?.copyWith(fontWeight: FontWeight.w700),
              ),
              const SizedBox(height: 4),
              Text(s.orderStubHint, style: theme.textTheme.bodySmall),
            ],
          ),
        ),
        const SizedBox(height: 12),
        GlassPanel(
          padding: const EdgeInsets.symmetric(vertical: 4),
          child: items.isEmpty
              ? Padding(
                  padding: const EdgeInsets.all(16),
                  child: Text(s.orderEmpty),
                )
              : Column(
                  children: [
                    for (final it in items)
                      ListTile(
                        title: Text('${it.quantity}× ${it.name}'),
                        subtitle: _subtitle(it),
                        trailing: Text(formatMoney(it.lineTotal, order.currency)),
                      ),
                  ],
                ),
        ),
      ],
    );
  }

  Widget? _subtitle(OrderItem it) {
    if (it.selectedOptions.isNotEmpty) {
      return Text(it.selectedOptions.map((o) => o.name).join(', '));
    }
    if (it.note != null && it.note!.isNotEmpty) return Text(it.note!);
    return null;
  }
}
