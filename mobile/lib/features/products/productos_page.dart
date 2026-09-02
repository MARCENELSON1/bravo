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
    return SwitchListTile(
      value: available && p.active,
      onChanged: p.active ? (v) => _toggle(p, v) : null,
      title: Text(p.name),
      subtitle: Text(
        [
          formatMoney(p.priceAmount, p.currency),
          if (p.category != null && p.category!.isNotEmpty) p.category!,
          if (!available) s.productoUnavailable,
        ].join(' · '),
      ),
    );
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
