import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/api_error.dart';
import '../../data/offline/sync_indicator.dart';
import '../../l10n/strings.dart';
import '../../ui/app_background.dart';
import '../../ui/glass_panel.dart';
import '../../util/money.dart';
import '../floor/floor_dtos.dart';
import '../floor/floor_providers.dart';
import 'order_dtos.dart';
import 'order_providers.dart';
import 'product_dtos.dart';
import 'product_picker.dart';

/// Comanda del mozo (Tanda 2): carrito line-based con captura optimista, marchar
/// a cocina y mover/unir mesa. Los modificadores del mozo quedan diferidos
/// (paridad con la web).
class OrderPage extends ConsumerStatefulWidget {
  const OrderPage({super.key, required this.orderId});

  final String orderId;

  @override
  ConsumerState<OrderPage> createState() => _OrderPageState();
}

class _OrderPageState extends ConsumerState<OrderPage> {
  String get orderId => widget.orderId;

  @override
  Widget build(BuildContext context) {
    final s = context.s;
    final async = ref.watch(orderControllerProvider(orderId));

    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(
        title: Text(s.orderTitle),
        backgroundColor: Colors.transparent,
        actions: const [SyncIndicator()],
      ),
      floatingActionButton: async.hasValue
          ? FloatingActionButton.extended(
              onPressed: _openPicker,
              icon: const Icon(Icons.add),
              label: Text(s.addProducts),
            )
          : null,
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
    final theme = Theme.of(context);
    final items = order.liveItems;
    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 96),
      children: [
        GlassPanel(
          padding: const EdgeInsets.symmetric(vertical: 6),
          child: items.isEmpty
              ? Padding(
                  padding: const EdgeInsets.all(16),
                  child: Text(s.orderEmpty),
                )
              : Column(
                  children: [
                    for (var i = 0; i < items.length; i++) ...[
                      if (i > 0) const Divider(height: 1),
                      _itemTile(context, s, order, items[i]),
                    ],
                  ],
                ),
        ),
        const SizedBox(height: 12),
        GlassPanel(
          child: Row(
            children: [
              Text(s.orderTotal, style: theme.textTheme.titleMedium),
              const Spacer(),
              Text(
                formatMoney(order.totalAmount, order.currency),
                style: theme.textTheme.titleMedium
                    ?.copyWith(fontWeight: FontWeight.w700),
              ),
            ],
          ),
        ),
        const SizedBox(height: 12),
        FilledButton.icon(
          onPressed: order.pendingCount == 0 ? null : _march,
          icon: const Icon(Icons.send),
          label: Text(s.marchCount(order.pendingCount)),
        ),
        const SizedBox(height: 12),
        GlassPanel(
          padding: const EdgeInsets.symmetric(vertical: 4),
          child: Material(
            type: MaterialType.transparency,
            child: Column(
              children: [
                ListTile(
                  leading: const Icon(Icons.drive_file_move_outline),
                  title: Text(s.moveTable),
                  onTap: _moveToFree,
                ),
                const Divider(height: 1),
                ListTile(
                  leading: const Icon(Icons.merge_outlined),
                  title: Text(s.mergeTable),
                  onTap: _mergeHere,
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _itemTile(BuildContext context, Strings s, Order order, OrderItem it) {
    final theme = Theme.of(context);
    final pending = it.status.isPending;
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text('${it.quantity}× ${it.name}',
                    style: theme.textTheme.bodyLarge),
              ),
              Text(formatMoney(it.lineTotal, order.currency)),
            ],
          ),
          if (_detail(it) != null)
            Padding(
              padding: const EdgeInsets.only(top: 2),
              child: Text(_detail(it)!,
                  style: theme.textTheme.bodySmall
                      ?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
            ),
          if (pending)
            Row(
              children: [
                IconButton(
                  visualDensity: VisualDensity.compact,
                  icon: const Icon(Icons.remove_circle_outline),
                  onPressed: () => _setQty(it, it.quantity - 1),
                ),
                Text('${it.quantity}'),
                IconButton(
                  visualDensity: VisualDensity.compact,
                  icon: const Icon(Icons.add_circle_outline),
                  onPressed: () => _setQty(it, it.quantity + 1),
                ),
                const Spacer(),
                IconButton(
                  visualDensity: VisualDensity.compact,
                  icon: const Icon(Icons.delete_outline),
                  onPressed: () => _remove(it),
                ),
              ],
            )
          else
            Padding(
              padding: const EdgeInsets.only(top: 4),
              child: Text(
                s.itemStatusLabel(it.status),
                style: theme.textTheme.labelSmall
                    ?.copyWith(color: theme.colorScheme.primary),
              ),
            ),
        ],
      ),
    );
  }

  String? _detail(OrderItem it) {
    if (it.selectedOptions.isNotEmpty) {
      return it.selectedOptions.map((o) => o.name).join(', ');
    }
    if (it.note != null && it.note!.isNotEmpty) return it.note;
    return null;
  }

  // --- Acciones ---

  OrderController get _ctrl =>
      ref.read(orderControllerProvider(orderId).notifier);

  Future<void> _openPicker() async {
    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      showDragHandle: false,
      builder: (_) => SizedBox(
        height: MediaQuery.of(context).size.height * 0.8,
        child: ProductPicker(onAdd: _add),
      ),
    );
  }

  Future<void> _add(Product p) async {
    try {
      await _ctrl.addProduct(p, 1);
    } on ApiError catch (e) {
      _toast(e.message);
    }
  }

  Future<void> _setQty(OrderItem it, int qty) async {
    if (qty < 1) return _remove(it);
    try {
      await _ctrl.setQty(it.id, qty);
    } on ApiError catch (e) {
      _toast(e.message);
    }
  }

  Future<void> _remove(OrderItem it) async {
    try {
      await _ctrl.removeItem(it.id);
    } on ApiError catch (e) {
      _toast(e.message);
    }
  }

  Future<void> _march() async {
    try {
      await _ctrl.send();
      if (!mounted) return;
      ref.read(floorProvider.notifier).refresh();
      Navigator.of(context).pop();
    } on ApiError catch (e) {
      _toast(e.message);
    }
  }

  Future<void> _moveToFree() async {
    final s = context.s;
    final tables = ref.read(floorProvider).valueOrNull ?? const <FloorTable>[];
    final free = tables.where((t) => t.isFree).toList();
    final picked = await _pickTable(free, s.moveTable, s.noFreeTables);
    if (picked == null) return;
    try {
      await _ctrl.transfer(picked.id);
      if (!mounted) return;
      ref.read(floorProvider.notifier).refresh();
      Navigator.of(context).pop();
    } on ApiError catch (e) {
      _toast(e.message);
    }
  }

  Future<void> _mergeHere() async {
    final s = context.s;
    final tables = ref.read(floorProvider).valueOrNull ?? const <FloorTable>[];
    final others = tables
        .where((t) => t.activeOrder != null && t.activeOrder!.id != orderId)
        .toList();
    final picked = await _pickTable(others, s.mergeTable, s.noOtherTables);
    if (picked?.activeOrder == null) return;
    try {
      await _ctrl.merge(picked!.activeOrder!.id);
      if (mounted) ref.read(floorProvider.notifier).refresh();
    } on ApiError catch (e) {
      _toast(e.message);
    }
  }

  Future<FloorTable?> _pickTable(
      List<FloorTable> tables, String title, String emptyMsg) {
    final s = context.s;
    return showModalBottomSheet<FloorTable>(
      context: context,
      builder: (_) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Padding(
              padding: const EdgeInsets.all(16),
              child: Text(title,
                  style: Theme.of(context).textTheme.titleMedium),
            ),
            if (tables.isEmpty)
              Padding(padding: const EdgeInsets.all(16), child: Text(emptyMsg))
            else
              Flexible(
                child: ListView(
                  shrinkWrap: true,
                  children: [
                    for (final t in tables)
                      ListTile(
                        title: Text(t.name ?? s.tableLabel(t.number)),
                        onTap: () => Navigator.of(context).pop(t),
                      ),
                  ],
                ),
              ),
            const SizedBox(height: 8),
          ],
        ),
      ),
    );
  }

  void _toast(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(message)));
  }
}
