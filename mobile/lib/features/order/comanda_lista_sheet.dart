import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../l10n/strings.dart';
import '../../ui/glass_panel.dart';
import '../../ui/state_views.dart';
import 'order_dtos.dart';
import 'order_providers.dart';

/// Modal "comanda lista" (Fase 1): al mozo dueño le aparece qué lleva y a qué
/// mesa cuando la cocina termina. Informativo — el marcado de "servido" se hace
/// desde el KDS/Piso. Trae la comanda fresca por `orderControllerProvider`.
class ComandaListaSheet extends ConsumerWidget {
  const ComandaListaSheet({super.key, required this.orderId, this.tableNumber});

  final String orderId;
  final int? tableNumber;

  static Future<void> show(BuildContext context,
      {required String orderId, int? tableNumber}) {
    return showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (_) =>
          ComandaListaSheet(orderId: orderId, tableNumber: tableNumber),
    );
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = context.s;
    final scheme = Theme.of(context).colorScheme;
    final async = ref.watch(orderControllerProvider(orderId));
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(16, 4, 16, 16),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              children: [
                Icon(Icons.room_service_outlined, color: scheme.primary),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    tableNumber != null
                        ? s.readyModalTitle(tableNumber!)
                        : s.readyModalTitleNoTable,
                    style: Theme.of(context)
                        .textTheme
                        .titleLarge
                        ?.copyWith(fontWeight: FontWeight.w700),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            async.when(
              loading: () => const Padding(
                padding: EdgeInsets.all(24),
                child: Center(child: CircularProgressIndicator()),
              ),
              error: (e, _) => ErrorView(
                  error: e,
                  onRetry: () =>
                      ref.invalidate(orderControllerProvider(orderId))),
              data: (order) => _items(context, s, order),
            ),
            const SizedBox(height: 12),
            FilledButton(
              onPressed: () => Navigator.of(context).pop(),
              child: Text(s.dashGotIt),
            ),
          ],
        ),
      ),
    );
  }

  Widget _items(BuildContext context, Strings s, Order order) {
    final scheme = Theme.of(context).colorScheme;
    final items = order.liveItems;
    if (items.isEmpty) {
      return Text(s.comandaEmpty,
          style: TextStyle(color: scheme.onSurfaceVariant));
    }
    return GlassPanel(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          for (final it in items)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 6),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('${it.quantity}× ${it.name}',
                      style: Theme.of(context)
                          .textTheme
                          .bodyLarge
                          ?.copyWith(fontWeight: FontWeight.w600)),
                  if (it.selectedOptions.isNotEmpty)
                    Text(it.selectedOptions.map((o) => o.name).join(', '),
                        style: TextStyle(
                            color: scheme.onSurfaceVariant, fontSize: 13)),
                  if (it.note != null && it.note!.isNotEmpty)
                    Text('› ${it.note}',
                        style: TextStyle(
                            color: scheme.onSurfaceVariant, fontSize: 13)),
                ],
              ),
            ),
        ],
      ),
    );
  }
}
