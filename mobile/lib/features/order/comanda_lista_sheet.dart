import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/api_error.dart';
import '../../l10n/strings.dart';
import '../../ui/glass_panel.dart';
import '../../ui/state_views.dart';
import '../floor/floor_providers.dart';
import 'order_dtos.dart';
import 'order_providers.dart';

/// Modal "comanda lista" (Fase 1 + mejora Fase 4): al mozo dueño le muestra, claro,
/// qué lleva y a qué mesa cuando la cocina termina, y le deja **marcar servido** ahí
/// mismo (cierra el ciclo). Trae la comanda fresca por `orderControllerProvider`.
class ComandaListaSheet extends ConsumerStatefulWidget {
  const ComandaListaSheet({super.key, required this.orderId, this.tableNumber});

  final String orderId;
  final int? tableNumber;

  static Future<void> show(
    BuildContext context, {
    required String orderId,
    int? tableNumber,
  }) {
    return showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (_) =>
          ComandaListaSheet(orderId: orderId, tableNumber: tableNumber),
    );
  }

  @override
  ConsumerState<ComandaListaSheet> createState() => _ComandaListaSheetState();
}

class _ComandaListaSheetState extends ConsumerState<ComandaListaSheet> {
  bool _serving = false;

  Future<void> _markServed() async {
    final s = context.s;
    final messenger = ScaffoldMessenger.of(context);
    final navigator = Navigator.of(context);
    setState(() => _serving = true);
    try {
      // Servir el curso listo (no toda la orden: el principal puede estar
      // todavía en cocina).
      final order = ref
          .read(orderControllerProvider(widget.orderId))
          .valueOrNull;
      final course = order?.readyCourse;
      final repo = ref.read(orderRepositoryProvider);
      if (course != null) {
        await repo.advanceCourse(widget.orderId, course, 'served');
      } else {
        await repo.markServed(widget.orderId);
      }
      ref.read(floorProvider.notifier).refresh();
      navigator.pop();
      messenger.showSnackBar(SnackBar(content: Text(s.readyServedDone)));
    } on ApiError catch (e) {
      if (mounted) {
        setState(() => _serving = false);
        messenger.showSnackBar(SnackBar(content: Text(e.message)));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final s = context.s;
    final scheme = Theme.of(context).colorScheme;
    final async = ref.watch(orderControllerProvider(widget.orderId));
    final items = async.valueOrNull?.liveItems ?? const <OrderItem>[];
    // La comanda es en vivo: si el curso ya se sirvió (desde la comanda o el
    // plano), acá no queda nada para servir.
    final nothingReady = async.valueOrNull?.readyCourse == null;

    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(16, 4, 16, 16),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            _header(context, s, scheme, items.length),
            const SizedBox(height: 12),
            async.when(
              loading: () => const Padding(
                padding: EdgeInsets.all(24),
                child: Center(child: CircularProgressIndicator()),
              ),
              error: (e, _) => ErrorView(
                error: e,
                onRetry: () =>
                    ref.invalidate(orderControllerProvider(widget.orderId)),
              ),
              data: (order) => _items(context, s, order),
            ),
            const SizedBox(height: 14),
            FilledButton.icon(
              // Nada listo (ya lo sirvieron): el botón no aplica.
              onPressed: (_serving || items.isEmpty || nothingReady)
                  ? null
                  : _markServed,
              icon: _serving
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.check_rounded),
              label: Text(s.readyMarkServed),
              style: FilledButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 14),
              ),
            ),
            TextButton(
              onPressed: _serving ? null : () => Navigator.of(context).pop(),
              child: Text(s.readyClose),
            ),
          ],
        ),
      ),
    );
  }

  Widget _header(
    BuildContext context,
    Strings s,
    ColorScheme scheme,
    int count,
  ) {
    return Row(
      children: [
        Container(
          padding: const EdgeInsets.all(10),
          decoration: BoxDecoration(
            color: scheme.primary.withValues(alpha: 0.14),
            shape: BoxShape.circle,
          ),
          child: Icon(Icons.room_service_outlined, color: scheme.primary),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                widget.tableNumber != null
                    ? s.readyModalTitle(widget.tableNumber!)
                    : s.readyModalTitleNoTable,
                style: Theme.of(context).textTheme.titleLarge
                    ?.copyWith(fontWeight: FontWeight.w700),
              ),
              Text(
                count > 0
                    ? '${s.readyModalSubtitle} · ${s.readyModalCount(count)}'
                    : s.readyModalSubtitle,
                style: TextStyle(color: scheme.onSurfaceVariant, fontSize: 13),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _items(BuildContext context, Strings s, Order order) {
    final scheme = Theme.of(context).colorScheme;
    final items = order.liveItems;
    if (items.isEmpty) {
      return Text(
        s.comandaEmpty,
        style: TextStyle(color: scheme.onSurfaceVariant),
      );
    }
    return GlassPanel(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          for (var i = 0; i < items.length; i++) ...[
            if (i > 0) const Divider(height: 16),
            _itemRow(context, s, scheme, items[i]),
          ],
        ],
      ),
    );
  }

  Widget _itemRow(
    BuildContext context,
    Strings s,
    ColorScheme scheme,
    OrderItem it,
  ) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Badge de cantidad, bien visible.
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 4),
          decoration: BoxDecoration(
            color: scheme.primary.withValues(alpha: 0.16),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Text(
            '${it.quantity}×',
            style: TextStyle(
              color: scheme.primary,
              fontWeight: FontWeight.w700,
            ),
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                it.name,
                style: Theme.of(context).textTheme.bodyLarge
                    ?.copyWith(fontWeight: FontWeight.w600),
              ),
              if (it.selectedOptions.isNotEmpty) ...[
                const SizedBox(height: 4),
                Wrap(
                  spacing: 6,
                  runSpacing: 6,
                  children: [
                    for (final o in it.selectedOptions)
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 8,
                          vertical: 2,
                        ),
                        decoration: BoxDecoration(
                          color: scheme.surfaceContainerHighest,
                          borderRadius: BorderRadius.circular(999),
                        ),
                        child: Text(
                          o.name,
                          style: const TextStyle(fontSize: 12),
                        ),
                      ),
                  ],
                ),
              ],
              if (it.note != null && it.note!.isNotEmpty) ...[
                const SizedBox(height: 4),
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Icon(
                      Icons.sticky_note_2_outlined,
                      size: 15,
                      color: scheme.tertiary,
                    ),
                    const SizedBox(width: 4),
                    Expanded(
                      child: Text(
                        '${s.readyNoteLabel}: ${it.note}',
                        style: TextStyle(
                          color: scheme.tertiary,
                          fontSize: 13,
                          fontStyle: FontStyle.italic,
                        ),
                      ),
                    ),
                  ],
                ),
              ],
            ],
          ),
        ),
      ],
    );
  }
}
