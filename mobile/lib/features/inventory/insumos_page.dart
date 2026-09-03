import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/api_error.dart';
import '../../l10n/strings.dart';
import '../../ui/app_background.dart';
import '../../ui/glass_panel.dart';
import '../../ui/state_views.dart';
import '../../util/money.dart';
import 'inventory_repository.dart';

/// Insumos (Fase 6): stock y costo, bajo-mínimo primero, con compra y merma.
class InsumosPage extends ConsumerStatefulWidget {
  const InsumosPage({super.key});

  @override
  ConsumerState<InsumosPage> createState() => _InsumosPageState();
}

class _InsumosPageState extends ConsumerState<InsumosPage> {
  @override
  Widget build(BuildContext context) {
    final s = context.s;
    final async = ref.watch(ingredientsProvider);
    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(title: Text(s.insumosTitle), backgroundColor: Colors.transparent),
      body: Stack(
        children: [
          const AppBackground(),
          SafeArea(
            child: async.when(
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (e, _) => ErrorView(
                error: e,
                onRetry: () => ref.invalidate(ingredientsProvider),
              ),
              data: (items) {
                Future<void> refresh() async =>
                    ref.invalidate(ingredientsProvider);
                if (items.isEmpty) {
                  return RefreshIndicator(
                    onRefresh: refresh,
                    child: ListView(
                      physics: const AlwaysScrollableScrollPhysics(),
                      children: [
                        SizedBox(
                            height: 280,
                            child: EmptyView(message: s.insumosEmpty)),
                      ],
                    ),
                  );
                }
                final sorted = [...items]..sort((a, b) {
                    if (a.isBelowMin == b.isBelowMin) return 0;
                    return a.isBelowMin ? -1 : 1;
                  });
                return RefreshIndicator(
                  onRefresh: refresh,
                  child: ListView(
                    physics: const AlwaysScrollableScrollPhysics(),
                    padding: const EdgeInsets.all(16),
                    children: [
                      GlassPanel(
                      padding: const EdgeInsets.symmetric(vertical: 4),
                      child: Material(
                        type: MaterialType.transparency,
                        child: Column(
                          children: [
                            for (var i = 0; i < sorted.length; i++) ...[
                              if (i > 0) const Divider(height: 1),
                              _row(s, sorted[i]),
                            ],
                          ],
                        ),
                      ),
                    ),
                  ],
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _row(Strings s, Ingredient ing) {
    final scheme = Theme.of(context).colorScheme;
    return ListTile(
      onTap: () => _actions(s, ing),
      title: Row(
        children: [
          Flexible(child: Text(ing.name)),
          if (ing.isBelowMin) ...[
            const SizedBox(width: 8),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
              decoration: BoxDecoration(
                color: scheme.error.withValues(alpha: 0.15),
                borderRadius: BorderRadius.circular(999),
              ),
              child: Text(s.insumosBelowMin,
                  style: TextStyle(color: scheme.error, fontSize: 11)),
            ),
          ],
        ],
      ),
      subtitle: Text('${s.insumosStock}: ${ing.stockQty} ${ing.unit} · mín ${ing.minQty}'),
      trailing: Text(formatMoney(ing.unitCostAmount, ing.currency)),
    );
  }

  void _actions(Strings s, Ingredient ing) {
    showModalBottomSheet<void>(
      context: context,
      builder: (ctx) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Padding(
              padding: const EdgeInsets.all(16),
              child: Text(ing.name, style: Theme.of(ctx).textTheme.titleMedium),
            ),
            ListTile(
              leading: const Icon(Icons.add_shopping_cart_outlined),
              title: Text(s.purchase),
              onTap: () {
                Navigator.of(ctx).pop();
                _purchase(s, ing);
              },
            ),
            ListTile(
              leading: const Icon(Icons.delete_sweep_outlined),
              title: Text(s.waste),
              onTap: () {
                Navigator.of(ctx).pop();
                _waste(s, ing);
              },
            ),
            const SizedBox(height: 8),
          ],
        ),
      ),
    );
  }

  Future<void> _purchase(Strings s, Ingredient ing) async {
    final qtyCtrl = TextEditingController();
    final costCtrl = TextEditingController(
        text: (ing.unitCostAmount / 100).toStringAsFixed(2));
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text('${s.purchase} · ${ing.name}'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: qtyCtrl,
              autofocus: true,
              keyboardType: TextInputType.number,
              decoration: InputDecoration(labelText: '${s.qtyLabel} (${ing.unit})'),
            ),
            const SizedBox(height: 8),
            TextField(
              controller: costCtrl,
              keyboardType: const TextInputType.numberWithOptions(decimal: true),
              decoration: InputDecoration(labelText: s.unitCostLabel),
            ),
          ],
        ),
        actions: _dialogActions(ctx),
      ),
    );
    if (ok != true) return;
    final qty = int.tryParse(qtyCtrl.text.trim()) ?? 0;
    final cost = pesosToMinor(costCtrl.text) ?? 0;
    if (qty <= 0) return;
    try {
      await ref
          .read(inventoryRepositoryProvider)
          .purchase(ing.id, qty: qty, unitCostAmount: cost);
      ref.invalidate(ingredientsProvider);
    } on ApiError catch (e) {
      _toast(e.message);
    }
  }

  Future<void> _waste(Strings s, Ingredient ing) async {
    final qtyCtrl = TextEditingController();
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text('${s.waste} · ${ing.name}'),
        content: TextField(
          controller: qtyCtrl,
          autofocus: true,
          keyboardType: TextInputType.number,
          decoration: InputDecoration(labelText: '${s.qtyLabel} (${ing.unit})'),
        ),
        actions: _dialogActions(ctx),
      ),
    );
    if (ok != true) return;
    final qty = int.tryParse(qtyCtrl.text.trim()) ?? 0;
    if (qty <= 0) return;
    try {
      await ref.read(inventoryRepositoryProvider).waste(ing.id, qty: qty);
      ref.invalidate(ingredientsProvider);
    } on ApiError catch (e) {
      _toast(e.message);
    }
  }

  List<Widget> _dialogActions(BuildContext ctx) => [
        TextButton(
          onPressed: () => Navigator.of(ctx).pop(false),
          child: Text(MaterialLocalizations.of(ctx).cancelButtonLabel),
        ),
        FilledButton(
          onPressed: () => Navigator.of(ctx).pop(true),
          child: Text(MaterialLocalizations.of(ctx).okButtonLabel),
        ),
      ];

  void _toast(String message) {
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(message)));
    }
  }
}
