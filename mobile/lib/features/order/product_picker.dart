import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../l10n/strings.dart';
import '../../ui/state_views.dart';
import '../../util/money.dart';
import 'order_providers.dart';
import 'product_dtos.dart';

/// Selector de productos (bottom sheet). Buscador + lista rankeada por uso;
/// tap = agregar 1. Queda abierto para armar la ronda (espeja `product-grid.tsx`).
class ProductPicker extends ConsumerStatefulWidget {
  const ProductPicker({super.key, required this.onAdd});

  final void Function(Product product) onAdd;

  @override
  ConsumerState<ProductPicker> createState() => _ProductPickerState();
}

class _ProductPickerState extends ConsumerState<ProductPicker> {
  final _search = TextEditingController();
  final _counts = <String, int>{};
  int _added = 0;

  void _add(Product p) {
    HapticFeedback.selectionClick();
    widget.onAdd(p);
    setState(() {
      _counts.update(p.id, (v) => v + 1, ifAbsent: () => 1);
      _added++;
    });
  }

  @override
  void dispose() {
    _search.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final s = context.s;
    final async = ref.watch(productsProvider);
    final usage = ref.read(productUsageProvider);

    return Padding(
      padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const SizedBox(height: 8),
          Center(
            child: Container(
              width: 40,
              height: 4,
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.outlineVariant,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
            child: TextField(
              controller: _search,
              onChanged: (_) => setState(() {}),
              decoration: InputDecoration(
                hintText: s.searchProduct,
                prefixIcon: const Icon(Icons.search),
              ),
            ),
          ),
          Flexible(
            child: async.when(
              loading: () => const Padding(
                padding: EdgeInsets.all(32),
                child: Center(child: CircularProgressIndicator()),
              ),
              error: (e, _) => ErrorView(
                error: e,
                onRetry: () => ref.invalidate(productsProvider),
              ),
              data: (all) {
                final q = _search.text.trim().toLowerCase();
                final orderable = all.where((p) => p.orderable).toList();
                final ranked = usage.rank(orderable);
                final list = q.isEmpty
                    ? ranked
                    : ranked
                        .where((p) => p.name.toLowerCase().contains(q))
                        .toList();
                return ListView.separated(
                  shrinkWrap: true,
                  padding: const EdgeInsets.only(bottom: 8),
                  itemCount: list.length,
                  separatorBuilder: (_, _) => const Divider(height: 1),
                  itemBuilder: (context, i) {
                    final p = list[i];
                    final count = _counts[p.id] ?? 0;
                    final scheme = Theme.of(context).colorScheme;
                    return ListTile(
                      title: Text(p.name),
                      subtitle: p.category == null ? null : Text(p.category!),
                      trailing: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Text(formatMoney(p.priceAmount, p.currency),
                              style:
                                  TextStyle(color: scheme.onSurfaceVariant)),
                          const SizedBox(width: 8),
                          if (count > 0) ...[
                            Container(
                              padding: const EdgeInsets.symmetric(
                                  horizontal: 8, vertical: 2),
                              decoration: BoxDecoration(
                                color: scheme.primary.withValues(alpha: 0.15),
                                borderRadius: BorderRadius.circular(999),
                              ),
                              child: Text('×$count',
                                  style: TextStyle(
                                      color: scheme.primary,
                                      fontWeight: FontWeight.w700)),
                            ),
                            const SizedBox(width: 4),
                          ],
                          IconButton.filledTonal(
                            visualDensity: VisualDensity.compact,
                            icon: const Icon(Icons.add),
                            tooltip: s.add,
                            onPressed: () => _add(p),
                          ),
                        ],
                      ),
                      onTap: () => _add(p),
                    );
                  },
                );
              },
            ),
          ),
          SafeArea(
            top: false,
            child: Padding(
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 12),
              child: Row(
                children: [
                  Text(
                    _added > 0 ? '+$_added' : '',
                    style: TextStyle(color: Theme.of(context).colorScheme.primary),
                  ),
                  const Spacer(),
                  FilledButton(
                    onPressed: () => Navigator.of(context).pop(),
                    child: Text(s.done),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
