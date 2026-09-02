import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/api_error.dart';
import '../../l10n/strings.dart';
import '../../ui/app_background.dart';
import '../../ui/glass_panel.dart';
import '../../util/money.dart';
import '../order/order_providers.dart';
import '../order/product_dtos.dart';

/// Productos (Fase 6): catálogo con precio + toggle "86" (disponible hoy).
/// La edición de costos/recetas/menu-engineering sigue en el web.
class ProductosPage extends ConsumerStatefulWidget {
  const ProductosPage({super.key});

  @override
  ConsumerState<ProductosPage> createState() => _ProductosPageState();
}

class _ProductosPageState extends ConsumerState<ProductosPage> {
  final Map<String, bool> _override = {};

  @override
  Widget build(BuildContext context) {
    final s = context.s;
    final async = ref.watch(productsProvider);
    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(
        title: Text(s.productosTitle),
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
              data: (products) => products.isEmpty
                  ? Center(child: Text(s.productosEmpty))
                  : ListView(
                      padding: const EdgeInsets.all(16),
                      children: [
                        GlassPanel(
                          padding: const EdgeInsets.symmetric(vertical: 4),
                          child: Material(
                            type: MaterialType.transparency,
                            child: Column(
                              children: [
                                for (var i = 0; i < products.length; i++) ...[
                                  if (i > 0) const Divider(height: 1),
                                  _row(s, products[i]),
                                ],
                              ],
                            ),
                          ),
                        ),
                      ],
                    ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _row(Strings s, Product p) {
    final available = _override[p.id] ?? p.availableToday;
    return ListTile(
      title: Text(p.name),
      subtitle: Text(
        [
          if (p.category != null && p.category!.isNotEmpty) p.category!,
          if (!available) s.productoUnavailable,
        ].join(' · '),
      ),
      trailing: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          TextButton(
            onPressed: () => _editPrice(s, p),
            child: Text(formatMoney(p.priceAmount, p.currency)),
          ),
          Switch(
            value: available && p.active,
            onChanged: p.active ? (v) => _toggle(p, v) : null,
          ),
        ],
      ),
    );
  }

  Future<void> _editPrice(Strings s, Product p) async {
    final ctrl =
        TextEditingController(text: (p.priceAmount / 100).toStringAsFixed(2));
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text('${s.editPrice} · ${p.name}'),
        content: TextField(
          controller: ctrl,
          autofocus: true,
          keyboardType: const TextInputType.numberWithOptions(decimal: true),
          decoration: InputDecoration(labelText: s.newPrice),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(false),
            child: Text(MaterialLocalizations.of(ctx).cancelButtonLabel),
          ),
          FilledButton(
            onPressed: () => Navigator.of(ctx).pop(true),
            child: Text(MaterialLocalizations.of(ctx).okButtonLabel),
          ),
        ],
      ),
    );
    if (ok != true) return;
    final amount = pesosToMinor(ctrl.text) ?? 0;
    if (amount <= 0) return;
    try {
      await ref.read(productRepositoryProvider).updatePrice(p.id, amount);
      ref.invalidate(productsProvider);
    } on ApiError catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(e.message)));
      }
    }
  }

  Future<void> _toggle(Product p, bool value) async {
    setState(() => _override[p.id] = value);
    try {
      await ref.read(productRepositoryProvider).setAvailability(p.id, value);
    } on ApiError catch (e) {
      setState(() => _override[p.id] = !value);
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(e.message)));
      }
    }
  }
}
