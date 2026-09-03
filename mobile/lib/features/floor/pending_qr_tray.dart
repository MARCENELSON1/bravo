import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/api_error.dart';
import '../../l10n/strings.dart';
import '../../ui/glass_panel.dart';
import '../order/order_dtos.dart';
import 'floor_dtos.dart';
import 'floor_providers.dart';

/// Bandeja "QR por confirmar" (Fase 2): lista los pedidos que entraron por QR y
/// siguen sin marchar. Al confirmar uno, el mozo queda dueño de la mesa (el
/// backend estampa el `waiter_id`). Si no hay nada, no ocupa espacio en el Piso.
class PendingQrTray extends ConsumerWidget {
  const PendingQrTray({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = context.s;
    final orders = ref.watch(pendingQrProvider).valueOrNull ?? const <Order>[];
    if (orders.isEmpty) return const SizedBox.shrink();

    final tables = ref.watch(floorProvider).valueOrNull ?? const <FloorTable>[];
    final numbers = {for (final t in tables) t.id: t.number};

    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: GlassPanel(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(children: [
              Icon(Icons.qr_code_2,
                  size: 18, color: Theme.of(context).colorScheme.primary),
              const SizedBox(width: 8),
              Text(s.pendingQrTitle(orders.length),
                  style: Theme.of(context).textTheme.titleSmall),
            ]),
            const SizedBox(height: 8),
            for (final o in orders) _row(context, ref, s, o, numbers[o.tableId]),
          ],
        ),
      ),
    );
  }

  Widget _row(
      BuildContext context, WidgetRef ref, Strings s, Order o, int? number) {
    final label = number != null ? '${s.pendingQrTable} $number' : s.pendingQrTable;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(label,
                    style: const TextStyle(fontWeight: FontWeight.w600)),
                Text(s.pendingQrItems(o.liveItems.length),
                    style: TextStyle(
                        color: Theme.of(context).colorScheme.onSurfaceVariant,
                        fontSize: 12)),
              ],
            ),
          ),
          FilledButton(
            onPressed: () => _confirm(context, ref, s, o.id),
            child: Text(s.pendingQrConfirm),
          ),
        ],
      ),
    );
  }

  Future<void> _confirm(
      BuildContext context, WidgetRef ref, Strings s, String orderId) async {
    final messenger = ScaffoldMessenger.of(context);
    try {
      await ref.read(orderRepositoryProvider).send(orderId);
      ref.invalidate(pendingQrProvider);
      ref.read(floorProvider.notifier).refresh();
      messenger.showSnackBar(SnackBar(content: Text(s.pendingQrConfirmed)));
    } on ApiError catch (e) {
      messenger.showSnackBar(SnackBar(content: Text(e.message)));
    }
  }
}
