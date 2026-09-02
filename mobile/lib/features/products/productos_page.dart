import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/api_error.dart';
import '../../l10n/strings.dart';
import '../../ui/app_background.dart';
import '../../ui/glass_panel.dart';
import '../../util/money.dart';
import '../order/order_providers.dart';
import '../order/product_dtos.dart';

/// Productos (Fase 6, consulta): catálogo con precio y disponibilidad. La
/// edición (costos, recetas, menu engineering) sigue en el web.
class ProductosPage extends ConsumerWidget {
  const ProductosPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
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
                          child: Text(s.consultaOnly,
                              style: Theme.of(context)
                                  .textTheme
                                  .bodySmall
                                  ?.copyWith(
                                      color: Theme.of(context)
                                          .colorScheme
                                          .onSurfaceVariant)),
                        ),
                        const SizedBox(height: 12),
                        GlassPanel(
                          padding: const EdgeInsets.symmetric(vertical: 4),
                          child: Material(
                            type: MaterialType.transparency,
                            child: Column(
                              children: [
                                for (var i = 0; i < products.length; i++) ...[
                                  if (i > 0) const Divider(height: 1),
                                  _tile(context, s, products[i]),
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

  Widget _tile(BuildContext context, Strings s, Product p) {
    final parts = <String>[
      if (p.category != null && p.category!.isNotEmpty) p.category!,
      if (!p.orderable) s.productoUnavailable,
    ];
    return ListTile(
      title: Text(p.name),
      subtitle: parts.isEmpty ? null : Text(parts.join(' · ')),
      trailing: Text(formatMoney(p.priceAmount, p.currency)),
    );
  }
}
